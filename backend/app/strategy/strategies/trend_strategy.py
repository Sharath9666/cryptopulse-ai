"""
Trend strategy.
Evaluates trend conditions using EMAs, MACD, and RSI.
"""

from app.features.models.feature_vector import FeatureVector


class TrendStrategy:
    """
    Evaluates Trend indicators (EMAs, MACD, RSI) on the FeatureVector.
    """
    def __init__(self) -> None:
        self.strategy_type = "trend"

    def execute(self, features: FeatureVector) -> dict:
        """
        Executes Trend-following logic.
        """
        # 1. EMA Crossovers
        ema9 = features.ema_9
        ema20 = features.ema_20
        ema50 = features.ema_50
        ema200 = features.ema_200
        
        # Check alignment: Bullish if ema_9 > ema_20 > ema_50
        bullish_ema = ema9 > ema20 > ema50 if (ema9 and ema20 and ema50) else False
        bearish_ema = ema9 < ema20 < ema50 if (ema9 and ema20 and ema50) else False

        # 2. MACD confirmations
        macd_hist = features.macd_hist
        bullish_macd = macd_hist > 0.0 if macd_hist is not None else False
        bearish_macd = macd_hist < 0.0 if macd_hist is not None else False

        # 3. RSI bounds
        rsi = features.rsi_14
        bullish_rsi = 50.0 < rsi < 70.0 if rsi is not None else False
        bearish_rsi = 30.0 < rsi < 50.0 if rsi is not None else False

        # Compute Direction & Confidence
        direction = "NEUTRAL"
        confidence = 0.50
        reasons = []

        if bullish_ema and bullish_macd:
            direction = "BULLISH"
            confidence = 0.75
            reasons.append("Bullish EMA crossover confirmed by MACD histogram")
            if bullish_rsi:
                confidence = 0.85
                reasons.append("RSI is accelerating upward within positive boundaries")
        elif bearish_ema and bearish_macd:
            direction = "BEARISH"
            confidence = 0.75
            reasons.append("Bearish EMA crossover confirmed by MACD histogram")
            if bearish_rsi:
                confidence = 0.85
                reasons.append("RSI is descending within negative boundaries")
        else:
            reasons.append("No clear EMA/MACD alignment detected")

        return {
            "symbol": features.symbol,
            "direction": direction,
            "confidence": confidence,
            "reasoning": "; ".join(reasons)
        }
