"""
Prediction Engine health tracking and diagnostics.
Monitors execution rates, tracked symbols, processing latencies, and ML model status.
"""

from datetime import datetime
from typing import Dict, List, Union
from pydantic import BaseModel, Field


class PredictionEngineHealth(BaseModel):
    """
    Representation of the Prediction Engine's health indicators.
    """
    predictions_generated: int = Field(0, description="Total predictions generated since startup")
    tracked_symbols: List[str] = Field(..., description="List of symbols for which predictions have been made")
    average_prediction_latency_ms: float = Field(0.0, description="Rolling average prediction latency in milliseconds")
    last_prediction_time: Union[datetime, None] = Field(None, description="Timestamp of last prediction")
    ml_predictions: int = Field(0, description="Predictions produced by the XGBoost model")
    rule_predictions: int = Field(0, description="Predictions produced by the rule engine")
    ml_models_loaded: List[str] = Field(default_factory=list, description="Symbols with active XGBoost models in memory")


class PredictionHealthTracker:
    """
    Thread-safe tracker storing runtime metrics for the Prediction Engine.
    """

    def __init__(self) -> None:
        self.predictions_generated: int = 0
        self.tracked_symbols: List[str] = []
        self.total_latency_ms: float = 0.0
        self.last_prediction_time: Union[datetime, None] = None
        self.ml_predictions: int = 0
        self.rule_predictions: int = 0

    def update_metrics(self, symbol: str, latency_ms: float, source: str = "rules") -> None:
        """
        Updates tracked counters, averages, and timestamps.

        Args:
            symbol: Trading pair symbol.
            latency_ms: Time taken for this prediction in milliseconds.
            source: "ml" for XGBoost predictions, "rules" for rule-engine predictions.
        """
        symbol_upper = symbol.upper()
        if symbol_upper not in self.tracked_symbols:
            self.tracked_symbols.append(symbol_upper)

        self.predictions_generated += 1
        self.total_latency_ms += latency_ms
        self.last_prediction_time = datetime.now()

        src_prefix = source.split("/")[0]  # strip version suffix like "ml/v1"
        if src_prefix == "ml":
            self.ml_predictions += 1
        else:
            self.rule_predictions += 1

    def get_health(self) -> PredictionEngineHealth:
        """
        Returns the aggregated health snapshot.
        """
        avg_latency = 0.0
        if self.predictions_generated > 0:
            avg_latency = self.total_latency_ms / self.predictions_generated

        # Query loaded ML models from global predictor (avoids circular import)
        ml_loaded: List[str] = []
        try:
            from app.ml.predictor import ml_predictor
            ml_loaded = ml_predictor.loaded_symbols()
        except Exception:
            pass

        return PredictionEngineHealth(
            predictions_generated=self.predictions_generated,
            tracked_symbols=self.tracked_symbols,
            average_prediction_latency_ms=avg_latency,
            last_prediction_time=self.last_prediction_time,
            ml_predictions=self.ml_predictions,
            rule_predictions=self.rule_predictions,
            ml_models_loaded=ml_loaded,
        )


# Global tracker instance
prediction_health_tracker = PredictionHealthTracker()
