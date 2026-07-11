"""
Prediction scoring engine.
Computes bullish and bearish signals from a FeatureVector using quantitative rules.
"""

from typing import Dict, List, Tuple
from app.features.models.feature_vector import FeatureVector


class ScoringEngine:
    """
    Evaluates FeatureVectors to yield probability, direction, and move estimations.
    """
    @staticmethod
    def score_features(fv: FeatureVector) -> Tuple[str, float, str, float, List[str], str]:
        """
        Processes FeatureVector metrics to return:
        (direction, probability, confidence, expected_move_percent, features_used, reasoning)
        """
        bullish_score = 0.0
        bearish_score = 0.0
        reasons = []
        features_used = []

        # 1. Trend Analysis
        if fv.ema_20 is not None and fv.ema_50 is not None:
            features_used.append("ema_20")
            features_used.append("ema_50")
            if fv.ema_20 > fv.ema_50:
                bullish_score += 2.0
                reasons.append("EMA20 > EMA50 (Bullish trend alignment)")
            else:
                bearish_score += 2.0
                reasons.append("EMA20 < EMA50 (Bearish trend alignment)")

        if fv.ema_50 is not None and fv.ema_200 is not None:
            features_used.append("ema_50")
            features_used.append("ema_200")
            if fv.ema_50 > fv.ema_200:
                bullish_score += 3.0
                reasons.append("EMA50 > EMA200 (Long-term Golden Cross)")
            else:
                bearish_score += 3.0
                reasons.append("EMA50 < EMA200 (Long-term Death Cross)")

        # 2. Momentum Analysis
        if fv.rsi_14 is not None:
            features_used.append("rsi_14")
            if fv.rsi_14 < 30.0:
                bullish_score += 2.0
                reasons.append(f"RSI oversold ({fv.rsi_14:.1f})")
            elif fv.rsi_14 > 70.0:
                bearish_score += 2.0
                reasons.append(f"RSI overbought ({fv.rsi_14:.1f})")
            elif fv.rsi_14 > 50.0:
                bullish_score += 1.0
                reasons.append(f"RSI in positive momentum ({fv.rsi_14:.1f})")
            else:
                bearish_score += 1.0
                reasons.append(f"RSI in negative momentum ({fv.rsi_14:.1f})")

        if fv.macd is not None and fv.macd_signal is not None:
            features_used.append("macd")
            features_used.append("macd_signal")
            if fv.macd > fv.macd_signal:
                bullish_score += 2.0
                reasons.append("MACD > Signal Line (Bullish crossover)")
            else:
                bearish_score += 2.0
                reasons.append("MACD < Signal Line (Bearish crossover)")

        # 3. Volume Analysis (Comparing proxy EMA9 to VWAP)
        if fv.ema_9 is not None and fv.vwap is not None:
            features_used.append("ema_9")
            features_used.append("vwap")
            if fv.ema_9 > fv.vwap:
                bullish_score += 1.5
                reasons.append("Price proxy (EMA9) > VWAP (Above average volume-weighted cost)")
            else:
                bearish_score += 1.5
                reasons.append("Price proxy (EMA9) < VWAP (Below average volume-weighted cost)")

        # 4. Volatility Scaling (ATR for expected movement)
        expected_move = 0.5  # default baseline
        if fv.atr_14 is not None and fv.ema_9 is not None:
            features_used.append("atr_14")
            # Calculate ATR percentage of price proxy
            expected_move = (fv.atr_14 / fv.ema_9) * 100.0

        # Calculate final direction & probability
        total_score = bullish_score + bearish_score
        if total_score == 0:
            direction = "NEUTRAL"
            probability = 0.5
            confidence = "LOW"
            reasoning = "Insufficient indicator signals to make prediction."
        else:
            bullish_pct = bullish_score / total_score
            if abs(bullish_pct - 0.5) < 0.1:
                direction = "NEUTRAL"
                probability = 0.5
                confidence = "LOW"
                reasoning = "Indecisive trend. Bullish and bearish indicators are balanced."
            elif bullish_pct > 0.5:
                direction = "BULLISH"
                probability = bullish_pct
                confidence = "HIGH" if probability > 0.7 else "MEDIUM"
                reasoning = f"Bullish indicators prevail: {', '.join(reasons)}"
            else:
                direction = "BEARISH"
                probability = 1.0 - bullish_pct
                confidence = "HIGH" if probability > 0.7 else "MEDIUM"
                reasoning = f"Bearish indicators prevail: {', '.join(reasons)}"

        return direction, probability, confidence, expected_move, list(set(features_used)), reasoning
