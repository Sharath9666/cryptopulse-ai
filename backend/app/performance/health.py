"""
Performance Engine health diagnostics.
Aggregates accuracy stats, prediction rates, and tracking symbols dynamically.
"""

from typing import List
from pydantic import BaseModel, Field


class PerformanceEngineHealth(BaseModel):
    """
    Representation of the Performance Engine's health indicators.
    """
    predictions_received: int = Field(0, description="Total prediction events received")
    predictions_evaluated: int = Field(0, description="Total evaluated prediction events")
    accuracy_percentage: float = Field(0.0, description="Evaluated predictions accuracy percentage (0.0 to 100.0)")
    avg_confidence: float = Field(0.0, description="Average confidence rating score (1.0=LOW, 2.0=MEDIUM, 3.0=HIGH)")
    symbols_tracked: List[str] = Field(default_factory=list, description="Symbols evaluated since start")


class PerformanceHealthTracker:
    """
    Stateful metric tracker compiling accuracy and confidence metrics dynamically.
    """
    def __init__(self) -> None:
        self.predictions_received: int = 0
        self.predictions_evaluated: int = 0
        self.correct_evaluations: int = 0
        
        self.confidence_sum: float = 0.0
        self._tracked_symbols: List[str] = []

    def receive_prediction(self, symbol: str, confidence: str) -> None:
        """
        Registers a new prediction event, updating counters and symbols lists.
        """
        self.predictions_received += 1
        symbol_upper = symbol.upper()
        if symbol_upper not in self._tracked_symbols:
            self._tracked_symbols.append(symbol_upper)
            
        # Map confidence
        conf_map = {"HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}
        self.confidence_sum += conf_map.get(confidence.upper(), 1.0)

    def register_evaluation(self, correct: bool) -> None:
        """
        Accumulates evaluation outcomes.
        """
        self.predictions_evaluated += 1
        if correct:
            self.correct_evaluations += 1

    def get_health(self) -> PerformanceEngineHealth:
        """
        Returns compiled health snapshot.
        """
        accuracy = 0.0
        if self.predictions_evaluated > 0:
            accuracy = (self.correct_evaluations / self.predictions_evaluated) * 100.0
            
        avg_conf = 0.0
        if self.predictions_received > 0:
            avg_conf = self.confidence_sum / self.predictions_received
            
        return PerformanceEngineHealth(
            predictions_received=self.predictions_received,
            predictions_evaluated=self.predictions_evaluated,
            accuracy_percentage=accuracy,
            avg_confidence=avg_conf,
            symbols_tracked=self._tracked_symbols,
        )


# Global tracker instance
performance_health_tracker = PerformanceHealthTracker()
