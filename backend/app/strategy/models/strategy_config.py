"""
Strategy config Pydantic model definitions.
"""

from pydantic import BaseModel, Field


class StrategyConfig(BaseModel):
    """
    Model representing symbol-specific strategy parameters.
    """
    symbol: str = Field(..., description="Target pair symbol (e.g. BTCUSDT)")
    strategy_type: str = Field(..., description="Strategy type (e.g. 'trend', 'momentum', 'volatility')")
    confidence_threshold: float = Field(0.70, description="Minimum strategy confidence threshold")
    risk_level: str = Field("medium", description="Risk level profile: high, medium, low")
    take_profit_percentage: float = Field(3.0, description="Take profit target ratio percentage")
    stop_loss_percentage: float = Field(2.0, description="Stop loss threshold ratio percentage")
