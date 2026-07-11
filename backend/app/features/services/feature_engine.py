"""
Feature engine service.
Stores historical candle buffers, executes technical indicator calculators,
and generates structured FeatureVectors.
"""

from datetime import datetime, timezone
import time
from typing import Dict, List, Union
from loguru import logger

from app.candles.models.candle import Candle
from app.features.models.feature_vector import FeatureVector
from app.features.publisher import FeaturePublisher
from app.features.health import feature_health_tracker

# Import calculators
from app.features.calculators.trend import TrendCalculator
from app.features.calculators.momentum import MomentumCalculator
from app.features.calculators.volatility import VolatilityCalculator
from app.features.calculators.volume import VolumeCalculator


class FeatureEngineService:
    """
    Stateful service processing completed candles, managing history buffers,
    and delegating computations to indicator calculators.
    """
    def __init__(self, publisher: FeaturePublisher = None) -> None:
        self.publisher = publisher or FeaturePublisher()
        # Historical buffer per symbol: Dict[symbol, List[Candle]]
        self.history: Dict[str, List[Candle]] = {}
        self.max_history: int = 300  # Maintain enough window history for EMA200

    async def process_candle(self, candle: Candle) -> None:
        """
        Appends a completed candle to history buffer and triggers feature engineering.
        """
        symbol = candle.symbol.upper()
        if symbol not in self.history:
            self.history[symbol] = []
            
        self.history[symbol].append(candle)
        
        # Enforce history limit constraints
        if len(self.history[symbol]) > self.max_history:
            self.history[symbol].pop(0)

        logger.info(
            f"Appended completed candle for {symbol} ({candle.timeframe}). "
            f"Current history length: {len(self.history[symbol])}"
        )
        
        # Calculate features and track execution latency
        start_time = time.perf_counter()
        try:
            feature_vector = self._calculate_features(symbol, candle.timeframe)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            if feature_vector:
                # Cache and publish feature vector
                await self.publisher.publish(feature_vector)
                
                # Update health analytics
                history_lengths = {sym: len(candles) for sym, candles in self.history.items()}
                feature_health_tracker.update_metrics(
                    symbols=list(self.history.keys()),
                    history_lengths=history_lengths,
                    latency_ms=latency_ms,
                )
                logger.info(
                    f"Generated FeatureVector for {symbol} ({candle.timeframe}) "
                    f"in {latency_ms:.2f}ms"
                )
        except Exception as e:
            logger.error(f"Error executing indicator calculations for {symbol}: {e}")

    def _calculate_features(self, symbol: str, timeframe: str) -> Union[FeatureVector, None]:
        """
        Performs calculations across trend, momentum, volatility, and volume indicators.
        """
        candles = self.history.get(symbol, [])
        if not candles:
            return None

        # Extract close, high, low, volume arrays for calculation
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        volumes = [c.volume for c in candles]

        # 1. Trend calculations
        ema_9 = TrendCalculator.calculate_ema(closes, 9)
        ema_20 = TrendCalculator.calculate_ema(closes, 20)
        ema_50 = TrendCalculator.calculate_ema(closes, 50)
        ema_200 = TrendCalculator.calculate_ema(closes, 200)

        # 2. Momentum calculations
        rsi_14 = MomentumCalculator.calculate_rsi(closes, 14)
        macd, macd_signal, macd_hist = MomentumCalculator.calculate_macd(closes)
        stoch_rsi = MomentumCalculator.calculate_stoch_rsi(closes, 14)

        # 3. Volatility calculations
        atr_14 = VolatilityCalculator.calculate_atr(highs, lows, closes, 14)
        bb_upper, bb_middle, bb_lower, bb_width = VolatilityCalculator.calculate_bollinger_bands(closes, 20, 2.0)

        # 4. Volume calculations
        vwap = VolumeCalculator.calculate_vwap(highs, lows, closes, volumes)
        obv = VolumeCalculator.calculate_obv(closes, volumes)

        # Build feature vector
        return FeatureVector(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now(timezone.utc),
            ema_9=ema_9,
            ema_20=ema_20,
            ema_50=ema_50,
            ema_200=ema_200,
            rsi_14=rsi_14,
            macd=macd,
            macd_signal=macd_signal,
            macd_hist=macd_hist,
            stoch_rsi=stoch_rsi,
            atr_14=atr_14,
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower,
            bb_width=bb_width,
            vwap=vwap,
            obv=obv,
        )


# Global service instance
feature_engine = FeatureEngineService()
