"""
Volume indicators calculator.
Computes Volume Weighted Average Price (VWAP) and On Balance Volume (OBV).
"""

from typing import List, Union


class VolumeCalculator:
    """
    Calculator class handling volume metrics like VWAP and OBV.
    """
    @staticmethod
    def calculate_vwap(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float]
    ) -> Union[float, None]:
        """
        Calculates Volume Weighted Average Price (VWAP).
        """
        if not closes:
            return None

        total_pv = 0.0
        total_v = 0.0
        
        for h, l, c, v in zip(highs, lows, closes, volumes):
            typical_price = (h + l + c) / 3.0
            total_pv += typical_price * v
            total_v += v

        if total_v == 0.0:
            return closes[-1]  # Fallback to last close if no volume
            
        return total_pv / total_v

    @staticmethod
    def calculate_obv(closes: List[float], volumes: List[float]) -> Union[float, None]:
        """
        Calculates On Balance Volume (OBV).
        """
        if not closes:
            return None

        obv = 0.0
        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                obv += volumes[i]
            elif closes[i] < closes[i - 1]:
                obv -= volumes[i]
                
        return obv
