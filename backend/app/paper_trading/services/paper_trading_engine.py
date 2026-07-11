"""
Paper trading engine service.
Coordinates incoming predictions to enter positions, and evaluates ticks against TP/SL targets.
"""

import json
from loguru import logger

from app.prediction.models.prediction import Prediction
from app.market.schemas.market_tick import MarketTick
from app.paper_trading.services.portfolio_manager import portfolio_manager
from app.paper_trading.publisher import PaperTradingPublisher
from app.paper_trading.health import paper_trading_health_tracker


class PaperTradingEngineService:
    """
    Simulates paper trading execution, checking targets against ticks and managing executions.
    """
    def __init__(self, publisher: PaperTradingPublisher = None) -> None:
        self.publisher = publisher or PaperTradingPublisher()

    async def handle_prediction(self, prediction: Prediction) -> None:
        """
        Receives predictions and triggers simulated entry if probabilities hit thresholds.
        """
        # Criteria: BULLISH prediction and probability >= 0.70
        if prediction.direction.upper() != "BULLISH" or prediction.probability < 0.70:
            return

        symbol = prediction.symbol.upper()
        logger.info(f"Signal received: {symbol} probability {prediction.probability:.2f} (>= 0.70). Evaluated for trade entry.")

        from app.config.settings import settings
        entry_price = None

        try:
            if settings.BACKTEST_SPEED_MODE:
                from app.features.services.feature_engine import feature_engine
                candles = feature_engine.history.get(symbol, [])
                if candles:
                    entry_price = candles[-1].close
                else:
                    entry_price = 1.0  # Fallback
            else:
                # Query entry price from the latest market tick stored in Redis
                redis_client = portfolio_manager.redis
                market_key = f"market:{symbol}"
                raw_tick = await redis_client.get(market_key)
                
                if not raw_tick:
                    logger.error(f"Cannot find latest price tick for {symbol} in Redis. Skipping entry.")
                    return

                tick_dict = json.loads(raw_tick)
                entry_price = float(tick_dict["price"])

            # Call portfolio manager to allocate and open the simulated trade
            trade = await portfolio_manager.open_position(symbol, entry_price)
            if trade:
                # Cache the opened trade to Redis
                await self.publisher.cache_open_trade(trade)
                # Update health tracker
                paper_trading_health_tracker.track_symbols(symbol)
                
        except Exception as e:
            logger.error(f"Error executing paper trade entry for {prediction.symbol}: {e}")

    async def handle_tick(self, tick: MarketTick) -> None:
        """
        Monitors open positions against current market price updates, checking TP/SL targets.
        """
        symbol = tick.symbol.upper()
        portfolio = await portfolio_manager.get_portfolio()
        
        # Identify open trades for this symbol
        open_trades = [t for t in portfolio.open_positions if t.symbol == symbol]
        if not open_trades:
            return

        price = tick.price
        for trade in open_trades:
            entry = trade.entry_price
            tp_target = entry * 1.03
            sl_target = entry * 0.98

            # Check Take Profit target (+3%)
            if price >= tp_target:
                closed_trade = await portfolio_manager.close_position(
                    trade_id=trade.trade_id,
                    exit_price=price,
                    reason=f"Take Profit (+3.0%) hit at {price:.4f}"
                )
                if closed_trade:
                    await self.publisher.publish_trade_close(closed_trade)

            # Check Stop Loss target (-2%)
            elif price <= sl_target:
                closed_trade = await portfolio_manager.close_position(
                    trade_id=trade.trade_id,
                    exit_price=price,
                    reason=f"Stop Loss (-2.0%) hit at {price:.4f}"
                )
                if closed_trade:
                    await self.publisher.publish_trade_close(closed_trade)


# Global service instance
paper_trading_engine = PaperTradingEngineService()
