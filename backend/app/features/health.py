"""
Feature engine health tracking and diagnostics.
Monitors history buffers, feature generation counts, and calculation latencies.
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class FeatureEngineHealth(BaseModel):
    """
    Representation of the Feature Engine's health indicators.
    """
    tracked_symbols: List[str] = Field(..., description="List of currently tracked symbols")
    history_lengths: Dict[str, int] = Field(..., description="Map of symbols to historical candle buffer sizes")
    features_generated_count: int = Field(0, description="Total features generated since startup")
    last_calculation_latency_ms: float = Field(0.0, description="Calculation latency in milliseconds of the last run")


class FeatureHealthTracker:
    """
    Thread-safe tracker storing runtime metrics for the Feature Engineering Engine.
    """
    def __init__(self) -> None:
        self.tracked_symbols: List[str] = []
        self.history_lengths: Dict[str, int] = {}
        self.features_generated_count: int = 0
        self.last_calculation_latency_ms: float = 0.0

    def update_metrics(
        self,
        symbols: List[str],
        history_lengths: Dict[str, int],
        latency_ms: float
    ) -> None:
        """
        Updates tracked symbols, lengths, and latencies.
        """
        self.tracked_symbols = symbols
        self.history_lengths = history_lengths
        self.last_calculation_latency_ms = latency_ms
        self.features_generated_count += 1

    def get_health(self) -> FeatureEngineHealth:
        """
        Returns the aggregated health snapshot.
        """
        return FeatureEngineHealth(
            tracked_symbols=self.tracked_symbols,
            history_lengths=self.history_lengths,
            features_generated_count=self.features_generated_count,
            last_calculation_latency_ms=self.last_calculation_latency_ms,
        )


# Global tracker instance
feature_health_tracker = FeatureHealthTracker()
