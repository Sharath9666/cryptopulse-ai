"""
Momentum strategy.
Evaluates momentum conditions using RSI momentum, Volume multiples, and price indicators.
"""

from app.features.models.feature_vector import FeatureVector


class MomentumStrategy:
    """
    Evaluates momentum indicators (Stochastic RSI, RSI, Volume spikes) on the FeatureVector.
    """
    def __init__(self) -> None:
        self.strategy_type = "momentum"

    def execute(self, features: FeatureVector) -> dict:
        """
        Executes Momentum logic.
        """
        # 1. Stochastic RSI / RSI
        stoch_rsi = features.stoch_rsi
        rsi = features.rsi_14
        
        # Bullish momentum if RSI crosses above 50 and Stochastic RSI is high
        bullish_mom = (rsi > 50.0 and stoch_rsi > 0.70) if (rsi is not None and stoch_rsi is not None) else False
        bearish_mom = (rsi < 50.0 and stoch_rsi < 0.30) if (rsi is not None and stoch_rsi is not None) else False

        # 2. Volume checks
        vwap = features.vwap
        close_price = features.ema_9  # Use ema_9 as price proxy since close is not in FeatureVector
        
        bullish_vol = close_price > vwap if (close_price and vwap) else False
        bearish_vol = close_price < vwap if (close_price and vwap) else False

        # Compute Direction & Confidence
        direction = "NEUTRAL"
        confidence = 0.50
        reasons = []

        if bullish_mom:
            direction = "BULLISH"
            confidence = 0.70
            reasons.append("Bullish momentum detected in RSI and Stochastic RSI")
            if bullish_vol:
                confidence = 0.80
                reasons.append("Close price exceeds VWAP indicating strong volume backup")
        elif bearish_mom:
            direction = "BEARISH"
            confidence = 0.70
            reasons.append("Bearish momentum detected in RSI and Stochastic RSI")
            if bearish_vol:
                confidence = 0.80
                reasons.append("Close price below VWAP indicating volume sells pressure")
        else:
            reasons.append("RSI and Stochastic RSI indicators are in neutral bounds")

        return {
            "symbol": features.symbol,
            "direction": direction,
            "confidence": confidence,
            "reasoning": "; ".join(reasons)
        }
