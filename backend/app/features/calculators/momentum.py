"""
Momentum indicators calculator.
Computes Relative Strength Index (RSI), MACD components, and Stochastic RSI.
"""

from typing import List, Tuple, Union
from app.features.calculators.trend import TrendCalculator


class MomentumCalculator:
    """
    Calculator class handling momentum metrics like RSI, MACD, and Stochastic RSI.
    """
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Union[float, None]:
        """
        Calculates Wilder's Relative Strength Index (RSI).
        """
        if len(prices) < period + 1:
            return None

        # Calculate difference change list
        changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        
        gains = [c if c > 0 else 0.0 for c in changes]
        losses = [-c if c < 0 else 0.0 for c in changes]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Wilder's smoothing logic
        for i in range(period, len(changes)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def calculate_macd(prices: List[float]) -> Tuple[Union[float, None], Union[float, None], Union[float, None]]:
        """
        Calculates MACD, MACD Signal Line (9 EMA of MACD), and MACD Histogram.
        Requires at least 35 periods to calculate signal line correctly.
        """
        if len(prices) < 26:
            return None, None, None

        # Build list of MACD values
        macd_values = []
        for i in range(26, len(prices) + 1):
            sub_prices = prices[:i]
            ema_12 = TrendCalculator.calculate_ema(sub_prices, 12)
            ema_26 = TrendCalculator.calculate_ema(sub_prices, 26)
            if ema_12 is not None and ema_26 is not None:
                macd_values.append(ema_12 - ema_26)

        if not macd_values:
            return None, None, None

        macd_line = macd_values[-1]
        
        # Compute Signal line (9-period EMA of MACD line)
        if len(macd_values) < 9:
            return macd_line, None, None

        signal_line = TrendCalculator.calculate_ema(macd_values, 9)
        if signal_line is None:
            return macd_line, None, None

        hist = macd_line - signal_line
        return macd_line, signal_line, hist

    @staticmethod
    def calculate_stoch_rsi(prices: List[float], period: int = 14) -> Union[float, None]:
        """
        Calculates Stochastic RSI.
        Requires at least 29 periods to calculate 14 RSI values.
        """
        # Calculate RSI values over the lookback window
        rsi_values = []
        # We need a window of 'period' RSI values
        for i in range(len(prices) - period, len(prices) + 1):
            if i >= period + 1:
                sub_prices = prices[:i]
                rsi = MomentumCalculator.calculate_rsi(sub_prices, period)
                if rsi is not None:
                    rsi_values.append(rsi)

        if len(rsi_values) < period:
            return None

        current_rsi = rsi_values[-1]
        min_rsi = min(rsi_values)
        max_rsi = max(rsi_values)

        denom = max_rsi - min_rsi
        if denom == 0.0:
            return 1.0  # Fallback to avoid division by zero
            
        return (current_rsi - min_rsi) / denom
