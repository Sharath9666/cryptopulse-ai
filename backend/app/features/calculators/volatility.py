"""
Volatility indicators calculator.
Computes Average True Range (ATR) and Bollinger Bands.
"""

from typing import List, Tuple, Union


class VolatilityCalculator:
    """
    Calculator class handling volatility metrics like ATR and Bollinger Bands.
    """
    @staticmethod
    def calculate_atr(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14
    ) -> Union[float, None]:
        """
        Calculates Average True Range (ATR).
        """
        if len(closes) < period + 1:
            return None

        tr_values = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            tr_values.append(tr)

        # Average True Range over period (Wilder's or simple SMA, using SMA for simplicity)
        return sum(tr_values[-period:]) / period

    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float],
        period: int = 20,
        num_std: float = 2.0
    ) -> Tuple[Union[float, None], Union[float, None], Union[Union[float, None], None], Union[float, None]]:
        """
        Calculates Bollinger Bands (Upper, Middle, Lower, Width).
        """
        if len(prices) < period:
            return None, None, None, None

        window = prices[-period:]
        sma = sum(window) / period
        
        # Calculate standard deviation
        variance = sum((p - sma) ** 2 for p in window) / period
        std_dev = variance ** 0.5
        
        upper = sma + num_std * std_dev
        lower = sma - num_std * std_dev
        width = (upper - lower) / sma if sma != 0 else 0.0

        return upper, sma, lower, width
