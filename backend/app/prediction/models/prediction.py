"""
Prediction schema definitions.
Represents a directional movement prediction with confidence scoring and reasoning.
"""

from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class Prediction(BaseModel):
    """
    Standard model representing quantitative direction and confidence results.
    """
    symbol: str = Field(..., description="Trading pair symbol (e.g. BTCUSDT)")
    timeframe: str = Field(..., description="Candle interval timeframe (e.g. '1m')")
    timestamp: datetime = Field(..., description="Time of prediction generation")
    direction: str = Field(..., description="Directional prediction: 'BULLISH', 'BEARISH', or 'NEUTRAL'")
    probability: float = Field(..., description="Calculated probability value (0.0 to 1.0) of the direction")
    confidence: str = Field(..., description="Prediction confidence grade: 'HIGH', 'MEDIUM', or 'LOW'")
    expected_move_percent: float = Field(..., description="Estimated expected movement percent")
    features_used: List[str] = Field(..., description="List of technical indicator feature names utilized")
    reasoning: str = Field(..., description="Text summary outlining indicators reasoning")
    # Auditability fields — populated by the prediction engine orchestrator
    source: str = Field("rules", description="Prediction source: 'ml' (XGBoost) or 'rules' (rule engine)")
    model_version: Optional[str] = Field(None, description="ML model version used (e.g. 'v1'), None for rule-based predictions")

