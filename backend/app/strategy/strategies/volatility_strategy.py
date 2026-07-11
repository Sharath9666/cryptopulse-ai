"""
Volatility strategy.
Evaluates volatility conditions using Bollinger Bands breakout and ATR.
"""

from app.features.models.feature_vector import FeatureVector


class VolatilityStrategy:
    """
    Evaluates volatility bands (Bollinger Bands, ATR) on the FeatureVector.
    """
    def __init__(self) -> None:
        self.strategy_type = "volatility"

    def execute(self, features: FeatureVector) -> dict:
        """
        Executes Bollinger Bands breakout and ATR volatility checks.
        """
        # Bollinger Bands
        upper_bb = features.bb_upper
        lower_bb = features.bb_lower
        close_price = features.ema_9  # Use ema_9 as price proxy since close is not in FeatureVector
        bb_width = features.bb_width
        
        # Breakout signals
        bullish_break = close_price > upper_bb if (close_price and upper_bb) else False
        bearish_break = close_price < lower_bb if (close_price and lower_bb) else False

        # ATR checks
        atr = features.atr_14

        # Compute Direction & Confidence
        direction = "NEUTRAL"
        confidence = 0.50
        reasons = []

        if bullish_break:
            direction = "BULLISH"
            confidence = 0.75
            reasons.append(f"Price broke above Bollinger Upper Band ({upper_bb:.2f})")
            if atr > 0.0:
                reasons.append(f"Volatility confirmed by ATR of {atr:.4f}")
        elif bearish_break:
            direction = "BEARISH"
            confidence = 0.75
            reasons.append(f"Price broke below Bollinger Lower Band ({lower_bb:.2f})")
            if atr > 0.0:
                reasons.append(f"Volatility confirmed by ATR of {atr:.4f}")
        else:
            reasons.append("Price remains inside Bollinger Bands boundaries")

        return {
            "symbol": features.symbol,
            "direction": direction,
            "confidence": confidence,
            "reasoning": "; ".join(reasons)
        }
