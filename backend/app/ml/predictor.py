"""
MLPredictor — per-symbol XGBoost inference service.

Responsibilities:
  - Load the latest trained model for a symbol via ModelRegistry
  - Convert FeatureVector → numpy array via FeatureExtractor
  - Run XGBoost inference and return a structured PredictionResult
  - Expose is_ready(symbol) for health checks
  - Thread-safe model reload via asyncio.Lock

Fallback contract:
  The predictor signals when ML is unavailable (no model, exception, low
  confidence) by returning source="rules" in the PredictionResult.
  The PredictionEngineService orchestrates the actual fallback call to
  ScoringEngine.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
from loguru import logger

from app.features.models.feature_vector import FeatureVector
from app.ml.config import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    LABEL_TO_DIRECTION,
    ML_ENABLED,
    ML_MIN_CONFIDENCE,
)
from app.ml.features import FeatureExtractor
from app.ml.model import ModelRegistry, ModelMetadata, model_registry


@dataclass
class PredictionResult:
    """
    Structured output from the ML prediction layer.
    Compatible with the existing Prediction Pydantic model fields.
    """
    direction: str           # "BULLISH" | "BEARISH" | "NEUTRAL"
    probability: float       # Max class probability (0-1)
    confidence: str          # "HIGH" | "MEDIUM" | "LOW"
    expected_return: float   # ATR-scaled expected move %
    model_version: str       # Registry version that produced this result
    source: str              # "ml" or "rules"
    class_probabilities: dict[str, float] = field(default_factory=dict)
    features_used: list[str] = field(default_factory=list)


def _probability_to_confidence(probability: float) -> str:
    """Map a raw probability to HIGH / MEDIUM / LOW confidence grade."""
    if probability >= CONFIDENCE_HIGH:
        return "HIGH"
    if probability >= CONFIDENCE_MEDIUM:
        return "MEDIUM"
    return "LOW"


def _compute_expected_return(fv: FeatureVector, direction: str) -> float:
    """
    Estimate expected return % from ATR, scaled by direction.
    Falls back to 0.5% when ATR is unavailable.
    """
    if fv.atr_14 is not None and fv.ema_9 is not None and fv.ema_9 > 0:
        atr_pct = (fv.atr_14 / fv.ema_9) * 100.0
    else:
        atr_pct = 0.5

    if direction == "BULLISH":
        return round(atr_pct, 4)
    elif direction == "BEARISH":
        return round(-atr_pct, 4)
    return 0.0


class MLPredictor:
    """
    Per-symbol XGBoost inference engine.

    Models are loaded lazily on first predict() call and cached in memory.
    Use reload(symbol) to force a hot-reload (e.g. after retraining).
    """

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        self._registry = registry or model_registry
        # symbol → (pipeline, ModelMetadata)
        self._models: dict[str, tuple[Any, ModelMetadata]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_lock(self, symbol: str) -> asyncio.Lock:
        if symbol not in self._locks:
            self._locks[symbol] = asyncio.Lock()
        return self._locks[symbol]

    def _load_model(self, symbol: str) -> bool:
        """Attempt to load (or reload) the model for a symbol. Returns True on success."""
        try:
            pipeline, meta = self._registry.load(symbol)
            self._models[symbol] = (pipeline, meta)
            logger.info(
                f"MLPredictor: loaded model for {symbol} "
                f"| version={meta.version} | accuracy={meta.accuracy:.4f}"
            )
            return True
        except FileNotFoundError:
            logger.debug(f"MLPredictor: no trained model for {symbol}")
            return False
        except Exception as e:
            logger.error(f"MLPredictor: failed to load model for {symbol}: {e}")
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_ready(self, symbol: str) -> bool:
        """Return True if a model is loaded in memory for the symbol."""
        return symbol.upper() in self._models

    def loaded_symbols(self) -> list[str]:
        """Return the list of symbols with models currently loaded in memory."""
        return list(self._models.keys())

    async def ensure_loaded(self, symbol: str) -> bool:
        """
        Load model for symbol if not already in memory.
        Thread-safe via per-symbol asyncio.Lock.
        """
        sym = symbol.upper()
        if sym in self._models:
            return True
        async with self._get_lock(sym):
            # Re-check inside lock
            if sym in self._models:
                return True
            return self._load_model(sym)

    async def reload(self, symbol: str) -> bool:
        """
        Force-reload the model for a symbol (e.g. after retraining).
        """
        sym = symbol.upper()
        async with self._get_lock(sym):
            if sym in self._models:
                del self._models[sym]
            return self._load_model(sym)

    async def predict(self, fv: FeatureVector) -> Optional[PredictionResult]:
        """
        Run XGBoost inference on a FeatureVector.

        Returns:
            PredictionResult with source="ml" if successful.
            None if ML is disabled, no model exists, or inference fails.
            The caller (PredictionEngineService) should fall back to rules on None.
        """
        if not ML_ENABLED:
            return None

        sym = fv.symbol.upper()

        # Ensure model is loaded
        loaded = await self.ensure_loaded(sym)
        if not loaded:
            return None

        pipeline, meta = self._models[sym]

        try:
            # Extract features
            X = FeatureExtractor.to_2d_array(fv)

            # Inference
            class_probs: np.ndarray = pipeline.predict_proba(X)[0]
            predicted_label: int = int(np.argmax(class_probs))
            max_prob: float = float(class_probs[predicted_label])
            direction = LABEL_TO_DIRECTION[predicted_label]

            # Low-confidence guard — signal caller to use rule fallback
            if max_prob < ML_MIN_CONFIDENCE:
                logger.debug(
                    f"MLPredictor: low confidence for {sym} "
                    f"({max_prob:.3f} < {ML_MIN_CONFIDENCE}). Deferring to rules."
                )
                return None

            confidence = _probability_to_confidence(max_prob)
            expected_return = _compute_expected_return(fv, direction)

            # Build per-class probability dict
            class_prob_dict = {
                LABEL_TO_DIRECTION[i]: float(p)
                for i, p in enumerate(class_probs)
            }

            result = PredictionResult(
                direction=direction,
                probability=round(max_prob, 6),
                confidence=confidence,
                expected_return=expected_return,
                model_version=meta.version,
                source="ml",
                class_probabilities=class_prob_dict,
                features_used=meta.feature_columns,
            )

            logger.debug(
                f"MLPredictor [{sym}]: {direction} | "
                f"prob={max_prob:.4f} | conf={confidence} | v={meta.version}"
            )
            return result

        except Exception as e:
            logger.error(f"MLPredictor: inference error for {sym}: {e}")
            return None

    def preload_all(self) -> list[str]:
        """
        Synchronously preload models for all symbols that have a trained version.
        Called at application startup.

        Returns:
            List of successfully loaded symbol names.
        """
        available = self._registry.available_symbols()
        loaded: list[str] = []
        for sym in available:
            if self._load_model(sym):
                loaded.append(sym)
        if loaded:
            logger.info(f"MLPredictor: preloaded models for {loaded}")
        else:
            logger.info("MLPredictor: no trained models found — will use rule engine.")
        return loaded


# Global predictor instance
ml_predictor = MLPredictor()
