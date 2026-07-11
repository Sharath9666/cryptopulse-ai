"""
Trend indicators calculator.
Provides methods to compute Exponential Moving Averages (EMA).
"""

from typing import List, Union


class TrendCalculator:
    """
    Calculator class handling trend metrics like EMAs.
    """
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> Union[float, None]:
        """
        Calculates Exponential Moving Average for a given period.
        """
        if len(prices) < period:
            return None

        # Start with simple moving average (SMA) for initial value
        sma = sum(prices[:period]) / period
        ema = sma
        
        # Calculate multiplier
        multiplier = 2.0 / (period + 1.0)
        
        # Apply EMA formula to remaining prices
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
            
        return ema
