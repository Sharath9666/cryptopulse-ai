"""
Strategy execution engine.
Routes incoming feature vectors to matched strategy instances and fires signal events.
"""

from loguru import logger

from app.features.models.feature_vector import FeatureVector
from app.strategy.strategies.trend_strategy import TrendStrategy
from app.strategy.strategies.momentum_strategy import MomentumStrategy
from app.strategy.strategies.volatility_strategy import VolatilityStrategy
from app.strategy.publisher import StrategySignalPublisher


class StrategyEngine:
    """
    Core engine managing configurations and executions of trading strategies.
    """
    def __init__(self, publisher: StrategySignalPublisher = None) -> None:
        self.publisher = publisher or StrategySignalPublisher()
        
        # Strategy instances mapping
        self.trend_strat = TrendStrategy()
        self.momentum_strat = MomentumStrategy()
        self.volatility_strat = VolatilityStrategy()

    async def process_features(self, features: FeatureVector) -> None:
        """
        Receives FeatureVector, matches symbol to strategy, executes calculations, and publishes signal.
        """
        symbol = features.symbol.upper()
        logger.info(f"Strategy Engine processing features for {symbol}")

        # Routing rules:
        # - BTCUSDT, ETHUSDT -> Trend strategy
        # - DOGEUSDT, SOLUSDT -> Momentum strategy
        # - Others -> Volatility strategy
        if symbol in ["BTCUSDT", "ETHUSDT"]:
            strategy = self.trend_strat
        elif symbol in ["DOGEUSDT", "SOLUSDT"]:
            strategy = self.momentum_strat
        else:
            strategy = self.volatility_strat

        try:
            result = strategy.execute(features)
            
            # Publish output signal
            await self.publisher.publish_signal(
                symbol=symbol,
                direction=result["direction"],
                confidence=result["confidence"],
                reasoning=result["reasoning"]
            )
        except Exception as e:
            logger.error(f"Failed to execute strategy for {symbol}: {e}")


# Global StrategyEngine instance
strategy_engine = StrategyEngine()
