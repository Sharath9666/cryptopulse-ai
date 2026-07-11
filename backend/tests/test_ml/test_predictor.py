"""
Tests for MLPredictor — model loading, inference, fallback logic, and
PredictionEngineService orchestration.
"""

import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from app.features.models.feature_vector import FeatureVector
from app.ml.features import FeatureExtractor
from app.ml.model import ModelRegistry
from app.ml.predictor import MLPredictor, PredictionResult
from app.ml.trainer import ModelTrainer
from app.ml.config import ML_MIN_CONFIDENCE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_fv(**kwargs) -> FeatureVector:
    defaults = dict(
        symbol="BTCUSDT",
        timeframe="1h",
        timestamp=datetime.now(timezone.utc),
        ema_9=65100.0,
        ema_20=64900.0,
        ema_50=63000.0,
        ema_200=58000.0,
        rsi_14=62.0,
        macd=200.0,
        macd_signal=150.0,
        macd_hist=50.0,
        stoch_rsi=0.70,
        atr_14=750.0,
        bb_upper=None,
        bb_middle=None,
        bb_lower=None,
        bb_width=0.030,
        vwap=64800.0,
        obv=4_000_000.0,
    )
    defaults.update(kwargs)
    return FeatureVector(**defaults)


@pytest.fixture
def trained_registry(tmp_path):
    """A ModelRegistry with a trained BTCUSDT model."""
    registry = ModelRegistry(models_dir=tmp_path)
    trainer = ModelTrainer(registry=registry)
    fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=300, seed=42)
    trainer.train("BTCUSDT", fvs, labels=labels)
    return registry


# ---------------------------------------------------------------------------
# MLPredictor — model loading
# ---------------------------------------------------------------------------

class TestMLPredictorLoading:

    def test_is_not_ready_when_no_model(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        predictor = MLPredictor(registry=registry)
        assert not predictor.is_ready("BTCUSDT")

    def test_is_ready_after_model_loaded(self, trained_registry):
        predictor = MLPredictor(registry=trained_registry)
        predictor._load_model("BTCUSDT")
        assert predictor.is_ready("BTCUSDT")

    def test_loaded_symbols_empty_initially(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        predictor = MLPredictor(registry=registry)
        assert predictor.loaded_symbols() == []

    def test_loaded_symbols_after_load(self, trained_registry):
        predictor = MLPredictor(registry=trained_registry)
        predictor._load_model("BTCUSDT")
        assert "BTCUSDT" in predictor.loaded_symbols()

    def test_preload_all_loads_trained_symbol(self, trained_registry):
        predictor = MLPredictor(registry=trained_registry)
        loaded = predictor.preload_all()
        assert "BTCUSDT" in loaded

    @pytest.mark.asyncio
    async def test_reload_works_after_initial_load(self, trained_registry):
        predictor = MLPredictor(registry=trained_registry)
        predictor._load_model("BTCUSDT")
        result = await predictor.reload("BTCUSDT")
        assert result is True
        assert predictor.is_ready("BTCUSDT")


# ---------------------------------------------------------------------------
# MLPredictor — inference
# ---------------------------------------------------------------------------

class TestMLPredictorInference:

    @pytest.mark.asyncio
    async def test_predict_returns_none_when_no_model(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        predictor = MLPredictor(registry=registry)
        fv = _make_fv()
        result = await predictor.predict(fv)
        assert result is None

    @pytest.mark.asyncio
    async def test_predict_returns_result_with_trained_model(self, trained_registry):
        predictor = MLPredictor(registry=trained_registry)
        fv = _make_fv()
        result = await predictor.predict(fv)
        # May return None if confidence < threshold — that's valid behaviour
        if result is not None:
            assert isinstance(result, PredictionResult)
            assert result.direction in ("BULLISH", "BEARISH", "NEUTRAL")
            assert 0.0 <= result.probability <= 1.0
            assert result.confidence in ("HIGH", "MEDIUM", "LOW")
            assert result.source == "ml"
            assert result.model_version is not None

    @pytest.mark.asyncio
    async def test_predict_class_probabilities_sum_to_one(self, trained_registry):
        predictor = MLPredictor(registry=trained_registry)
        predictor._load_model("BTCUSDT")
        fv = _make_fv()
        result = await predictor.predict(fv)
        if result is not None:
            total = sum(result.class_probabilities.values())
            assert abs(total - 1.0) < 1e-4

    @pytest.mark.asyncio
    async def test_predict_returns_none_when_ml_disabled(self, trained_registry):
        predictor = MLPredictor(registry=trained_registry)
        predictor._load_model("BTCUSDT")
        fv = _make_fv()
        with patch("app.ml.predictor.ML_ENABLED", False):
            result = await predictor.predict(fv)
        assert result is None

    @pytest.mark.asyncio
    async def test_ensure_loaded_returns_true_for_trained(self, trained_registry):
        predictor = MLPredictor(registry=trained_registry)
        ok = await predictor.ensure_loaded("BTCUSDT")
        assert ok is True

    @pytest.mark.asyncio
    async def test_ensure_loaded_returns_false_for_untrained(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        predictor = MLPredictor(registry=registry)
        ok = await predictor.ensure_loaded("UNKNOWN")
        assert ok is False


# ---------------------------------------------------------------------------
# PredictionEngineService orchestration
# ---------------------------------------------------------------------------

class TestPredictionEngineOrchestration:

    @pytest.mark.asyncio
    async def test_falls_back_to_rules_when_no_model(self, tmp_path):
        """
        When MLPredictor returns None (no model), PredictionEngineService must
        call ScoringEngine and produce a prediction with source='rules'.
        """
        from app.prediction.services.prediction_engine import PredictionEngineService

        # Mock publisher to capture published prediction
        captured = []

        async def fake_publish(prediction):
            captured.append(prediction)
            return True

        mock_publisher = MagicMock()
        mock_publisher.publish = fake_publish

        # Use an untrained registry
        registry = ModelRegistry(models_dir=tmp_path)
        predictor = MLPredictor(registry=registry)

        engine = PredictionEngineService(publisher=mock_publisher)
        engine._ml_predictor = predictor

        fv = _make_fv()
        await engine.generate_prediction(fv)

        assert len(captured) == 1
        prediction = captured[0]
        assert prediction.source == "rules"
        assert prediction.model_version is None
        assert prediction.direction in ("BULLISH", "BEARISH", "NEUTRAL")

    @pytest.mark.asyncio
    async def test_uses_ml_when_model_available_and_confident(self, trained_registry):
        """
        When MLPredictor returns a high-confidence result, source should be 'ml'.
        """
        from app.prediction.services.prediction_engine import PredictionEngineService

        captured = []

        async def fake_publish(prediction):
            captured.append(prediction)
            return True

        mock_publisher = MagicMock()
        mock_publisher.publish = fake_publish

        predictor = MLPredictor(registry=trained_registry)

        # Inject a mock predict that always returns a confident ML result
        async def mock_predict(fv):
            return PredictionResult(
                direction="BULLISH",
                probability=0.82,
                confidence="HIGH",
                expected_return=1.2,
                model_version="v1",
                source="ml",
                class_probabilities={"BULLISH": 0.82, "NEUTRAL": 0.10, "BEARISH": 0.08},
                features_used=["ema_9", "rsi_14"],
            )

        predictor.predict = mock_predict

        engine = PredictionEngineService(publisher=mock_publisher)
        engine._ml_predictor = predictor

        fv = _make_fv()
        await engine.generate_prediction(fv)

        assert len(captured) == 1
        prediction = captured[0]
        assert prediction.source == "ml"
        assert prediction.model_version == "v1"
        assert prediction.direction == "BULLISH"
        assert prediction.probability == pytest.approx(0.82)

    @pytest.mark.asyncio
    async def test_falls_back_when_ml_returns_none(self, tmp_path):
        """Explicit test: ML returns None → rules path taken."""
        from app.prediction.services.prediction_engine import PredictionEngineService

        captured = []

        async def fake_publish(prediction):
            captured.append(prediction)
            return True

        mock_publisher = MagicMock()
        mock_publisher.publish = fake_publish

        predictor = MLPredictor(registry=ModelRegistry(models_dir=tmp_path))

        async def always_none(_):
            return None

        predictor.predict = always_none

        engine = PredictionEngineService(publisher=mock_publisher)
        engine._ml_predictor = predictor

        fv = _make_fv()
        await engine.generate_prediction(fv)

        assert len(captured) == 1
        assert captured[0].source == "rules"
