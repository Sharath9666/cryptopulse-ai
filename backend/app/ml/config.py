"""
ML module configuration.
Controls model directory, confidence thresholds, and feature flags.
"""

import os
from pathlib import Path

# Root directory of the ml module
ML_MODULE_DIR = Path(__file__).parent

# Where trained models are persisted
ML_MODELS_DIR = Path(os.getenv("ML_MODELS_DIR", str(ML_MODULE_DIR / "saved_models")))

# Minimum ML probability before falling back to rule engine
ML_MIN_CONFIDENCE = float(os.getenv("ML_MIN_CONFIDENCE", "0.55"))

# Feature flag: when False, always use rule engine
ML_ENABLED = os.getenv("ML_ENABLED", "true").lower() == "true"

# XGBoost hyperparameters
XGBOOST_PARAMS: dict = {
    "n_estimators": 200,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "eval_metric": "mlogloss",
    "random_state": 42,
    "n_jobs": -1,
}

# Canonical label mapping
LABEL_TO_DIRECTION: dict[int, str] = {0: "BEARISH", 1: "NEUTRAL", 2: "BULLISH"}
DIRECTION_TO_LABEL: dict[str, int] = {"BEARISH": 0, "NEUTRAL": 1, "BULLISH": 2}

# Confidence thresholds
CONFIDENCE_HIGH = 0.75
CONFIDENCE_MEDIUM = 0.60

# Canonical feature columns — order MUST NOT change between train and predict
FEATURE_COLUMNS: list[str] = [
    "ema_9",
    "ema_20",
    "ema_50",
    "ema_200",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
    "stoch_rsi",
    "atr_14",
    "bb_width",
    "vwap",
    "obv",
]
