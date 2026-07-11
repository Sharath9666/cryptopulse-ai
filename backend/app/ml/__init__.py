"""
app/ml package.

Exposes the core ML components for external use:
  - MLPredictor: per-symbol XGBoost inference
  - ModelTrainer: training pipeline
  - ModelRegistry: versioned model storage
  - FeatureExtractor: FeatureVector → numpy array
  - ml_predictor: global singleton predictor
  - model_registry: global singleton registry
"""

from app.ml.predictor import MLPredictor, PredictionResult, ml_predictor
from app.ml.trainer import ModelTrainer, TrainingResult
from app.ml.model import ModelRegistry, ModelMetadata, model_registry
from app.ml.features import FeatureExtractor

__all__ = [
    "MLPredictor",
    "PredictionResult",
    "ml_predictor",
    "ModelTrainer",
    "TrainingResult",
    "ModelRegistry",
    "ModelMetadata",
    "model_registry",
    "FeatureExtractor",
]
