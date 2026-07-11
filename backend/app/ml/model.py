"""
Model Registry — versioned save/load for trained XGBoost pipelines.

Directory layout:
    saved_models/
        {SYMBOL}/
            registry.json          ← version manifest
            v1/
                model.pkl          ← joblib-serialised sklearn Pipeline
                metadata.json      ← training metadata
            v2/
                ...

Versioning uses monotonically incrementing integers (v1, v2, …).
The registry.json tracks which version is "latest" so rollback is trivial.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import joblib
from loguru import logger

from app.ml.config import ML_MODELS_DIR


class ModelMetadata:
    """Lightweight struct for model training metadata."""

    def __init__(
        self,
        symbol: str,
        version: str,
        trained_at: str,
        n_samples: int,
        accuracy: float,
        feature_columns: list[str],
        xgboost_params: dict[str, Any],
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        self.symbol = symbol
        self.version = version
        self.trained_at = trained_at
        self.n_samples = n_samples
        self.accuracy = accuracy
        self.feature_columns = feature_columns
        self.xgboost_params = xgboost_params
        self.extra = extra or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "version": self.version,
            "trained_at": self.trained_at,
            "n_samples": self.n_samples,
            "accuracy": self.accuracy,
            "feature_columns": self.feature_columns,
            "xgboost_params": self.xgboost_params,
            **self.extra,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ModelMetadata":
        return cls(
            symbol=d["symbol"],
            version=d["version"],
            trained_at=d["trained_at"],
            n_samples=d["n_samples"],
            accuracy=d["accuracy"],
            feature_columns=d["feature_columns"],
            xgboost_params=d.get("xgboost_params", {}),
        )


class ModelRegistry:
    """
    Manages versioned XGBoost model storage and retrieval.

    Usage:
        # Save a new model version
        registry = ModelRegistry()
        meta = registry.save(symbol="BTCUSDT", pipeline=pipeline, metadata={...})

        # Load the latest model
        pipeline, meta = registry.load("BTCUSDT")

        # Load a specific version
        pipeline, meta = registry.load("BTCUSDT", version="v2")
    """

    def __init__(self, models_dir: Optional[Path] = None) -> None:
        self._root = Path(models_dir or ML_MODELS_DIR)
        self._root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _symbol_dir(self, symbol: str) -> Path:
        d = self._root / symbol.upper()
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _registry_path(self, symbol: str) -> Path:
        return self._symbol_dir(symbol) / "registry.json"

    def _read_registry(self, symbol: str) -> dict[str, Any]:
        path = self._registry_path(symbol)
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return {"latest": None, "versions": []}

    def _write_registry(self, symbol: str, data: dict[str, Any]) -> None:
        path = self._registry_path(symbol)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _next_version(self, symbol: str) -> str:
        reg = self._read_registry(symbol)
        existing = reg.get("versions", [])
        return f"v{len(existing) + 1}"

    def _version_dir(self, symbol: str, version: str) -> Path:
        d = self._symbol_dir(symbol) / version
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(
        self,
        symbol: str,
        pipeline: Any,
        n_samples: int,
        accuracy: float,
        feature_columns: list[str],
        xgboost_params: dict[str, Any],
        extra: Optional[dict[str, Any]] = None,
    ) -> ModelMetadata:
        """
        Serialise a trained sklearn Pipeline and write model + metadata to disk.

        Args:
            symbol: Trading pair (e.g. "BTCUSDT").
            pipeline: Trained sklearn Pipeline containing scaler + XGBClassifier.
            n_samples: Number of training samples.
            accuracy: Held-out test accuracy (0-1).
            feature_columns: Ordered list of feature names used during training.
            xgboost_params: Hyperparameters dict for auditability.
            extra: Any additional key-value pairs to store in metadata.

        Returns:
            ModelMetadata instance describing the saved version.
        """
        version = self._next_version(symbol)
        vdir = self._version_dir(symbol, version)

        # Serialise pipeline
        model_path = vdir / "model.pkl"
        joblib.dump(pipeline, model_path, compress=3)

        # Write metadata
        trained_at = datetime.now(timezone.utc).isoformat()
        meta = ModelMetadata(
            symbol=symbol,
            version=version,
            trained_at=trained_at,
            n_samples=n_samples,
            accuracy=accuracy,
            feature_columns=feature_columns,
            xgboost_params=xgboost_params,
            extra=extra or {},
        )
        meta_path = vdir / "metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta.to_dict(), f, indent=2)

        # Update registry
        reg = self._read_registry(symbol)
        reg["latest"] = version
        reg["versions"].append(
            {"version": version, "trained_at": trained_at, "accuracy": accuracy}
        )
        self._write_registry(symbol, reg)

        logger.info(
            f"ModelRegistry: saved {symbol} {version} "
            f"| samples={n_samples} | accuracy={accuracy:.4f} | path={vdir}"
        )
        return meta

    def load(
        self, symbol: str, version: Optional[str] = None
    ) -> tuple[Any, ModelMetadata]:
        """
        Load a trained pipeline from disk.

        Args:
            symbol: Trading pair (e.g. "BTCUSDT").
            version: Specific version string (e.g. "v2"). Defaults to latest.

        Returns:
            (pipeline, ModelMetadata)

        Raises:
            FileNotFoundError: if no model exists for the symbol/version.
        """
        reg = self._read_registry(symbol)
        target_version = version or reg.get("latest")

        if not target_version:
            raise FileNotFoundError(
                f"No model found for symbol '{symbol}'. "
                "Train a model first with ModelTrainer."
            )

        vdir = self._symbol_dir(symbol) / target_version
        model_path = vdir / "model.pkl"
        meta_path = vdir / "metadata.json"

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file missing for {symbol} {target_version}: {model_path}"
            )

        pipeline = joblib.load(model_path)

        meta_dict: dict[str, Any] = {}
        if meta_path.exists():
            with open(meta_path) as f:
                meta_dict = json.load(f)
        meta = ModelMetadata.from_dict(meta_dict) if meta_dict else ModelMetadata(
            symbol=symbol,
            version=target_version,
            trained_at="unknown",
            n_samples=0,
            accuracy=0.0,
            feature_columns=[],
            xgboost_params={},
        )

        logger.info(f"ModelRegistry: loaded {symbol} {target_version} from {vdir}")
        return pipeline, meta

    def list_versions(self, symbol: str) -> list[dict[str, Any]]:
        """Return all version entries for a symbol from the registry."""
        return self._read_registry(symbol).get("versions", [])

    def latest_version(self, symbol: str) -> Optional[str]:
        """Return the latest version string for a symbol, or None if not trained."""
        return self._read_registry(symbol).get("latest")

    def has_model(self, symbol: str) -> bool:
        """Return True if at least one model version exists for the symbol."""
        return self.latest_version(symbol) is not None

    def available_symbols(self) -> list[str]:
        """Return all symbols that have at least one saved model."""
        if not self._root.exists():
            return []
        return [
            d.name
            for d in self._root.iterdir()
            if d.is_dir() and (d / "registry.json").exists()
            and self._read_registry(d.name).get("latest") is not None
        ]


# Global registry instance
model_registry = ModelRegistry()
