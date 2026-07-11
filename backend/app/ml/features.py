"""
Feature extraction layer for the ML prediction engine.

Converts a FeatureVector Pydantic model into a fixed-length numpy array
suitable for XGBoost inference. The canonical column order is defined in
config.FEATURE_COLUMNS and must never change between training and prediction.
"""

from __future__ import annotations

import numpy as np
from typing import Optional

from app.features.models.feature_vector import FeatureVector
from app.ml.config import FEATURE_COLUMNS


# Per-feature fallback values used when a FeatureVector field is None.
# These represent neutral / market-average states that introduce minimal bias.
_FEATURE_DEFAULTS: dict[str, float] = {
    "ema_9":        0.0,
    "ema_20":       0.0,
    "ema_50":       0.0,
    "ema_200":      0.0,
    "rsi_14":       50.0,   # neutral RSI
    "macd":         0.0,
    "macd_signal":  0.0,
    "macd_hist":    0.0,
    "stoch_rsi":    0.5,    # neutral stochastic
    "atr_14":       0.0,
    "bb_width":     0.0,
    "vwap":         0.0,
    "obv":          0.0,
}


class FeatureExtractor:
    """
    Transforms a FeatureVector into a numpy array for XGBoost inference.

    The column order matches config.FEATURE_COLUMNS exactly.
    None values are replaced with domain-appropriate defaults so the
    model always receives a fully populated vector.
    """

    # Number of features — must equal len(FEATURE_COLUMNS)
    N_FEATURES: int = len(FEATURE_COLUMNS)

    @staticmethod
    def to_array(fv: FeatureVector) -> np.ndarray:
        """
        Convert a FeatureVector to a 1-D numpy array of shape (N_FEATURES,).

        Args:
            fv: FeatureVector Pydantic model from the feature engine.

        Returns:
            np.ndarray of dtype float64 with shape (N_FEATURES,).
        """
        values: list[float] = []
        for col in FEATURE_COLUMNS:
            raw = getattr(fv, col, None)
            if raw is None or (isinstance(raw, float) and np.isnan(raw)):
                values.append(_FEATURE_DEFAULTS.get(col, 0.0))
            else:
                values.append(float(raw))
        return np.array(values, dtype=np.float64)

    @staticmethod
    def to_2d_array(fv: FeatureVector) -> np.ndarray:
        """
        Convert a FeatureVector to a 2-D numpy array of shape (1, N_FEATURES).
        Required by scikit-learn / XGBoost single-sample prediction interface.
        """
        return FeatureExtractor.to_array(fv).reshape(1, -1)

    @staticmethod
    def batch_to_array(feature_vectors: list[FeatureVector]) -> np.ndarray:
        """
        Convert a list of FeatureVectors into a 2-D numpy array
        of shape (n_samples, N_FEATURES).

        Args:
            feature_vectors: List of FeatureVector objects.

        Returns:
            np.ndarray of shape (n_samples, N_FEATURES).
        """
        if not feature_vectors:
            return np.empty((0, FeatureExtractor.N_FEATURES), dtype=np.float64)
        rows = [FeatureExtractor.to_array(fv) for fv in feature_vectors]
        return np.vstack(rows)

    @staticmethod
    def feature_names() -> list[str]:
        """Returns the canonical ordered list of feature column names."""
        return list(FEATURE_COLUMNS)

    @staticmethod
    def validate(fv: FeatureVector) -> tuple[bool, list[str]]:
        """
        Validate a FeatureVector — identify which features are None/NaN.

        Returns:
            (is_complete, missing_fields) where is_complete is True
            only if no features are missing.
        """
        missing: list[str] = []
        for col in FEATURE_COLUMNS:
            val = getattr(fv, col, None)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                missing.append(col)
        return len(missing) == 0, missing
