"""
Paper trading portfolio manager.
Handles loading, updating, and saving the portfolio state in Redis.
"""

from datetime import datetime, timezone
import json
from loguru import logger
from redis.asyncio import Redis

from app.cache.redis import get_redis_client
from app.paper_trading.models.portfolio import Portfolio
from app.paper_trading.models.trade import Trade


class PortfolioManager:
    """
    Manages state mutations of the virtual paper trading portfolio stored in Redis.
    """
    def __init__(self, redis_client: Redis = None) -> None:
        self._redis_client = redis_client
        self._portfolio_key = "paper_portfolio"
        self._local_fallback: Portfolio = None

    @property
    def redis(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    async def get_portfolio(self) -> Portfolio:
        """
        Retrieves the virtual portfolio state from Redis or initializes a default one.
        """
        from app.config.settings import settings
        if settings.BACKTEST_SPEED_MODE:
            if self._local_fallback is None:
                self._local_fallback = Portfolio()
            return self._local_fallback

        try:
            data = await self.redis.get(self._portfolio_key)
            if data:
                portfolio = Portfolio.model_validate_json(data)
                self._local_fallback = portfolio
                return portfolio
        except Exception as e:
            logger.error(f"Error loading paper portfolio from Redis: {e}")
            
        if self._local_fallback is not None:
            return self._local_fallback

        # Fallback/Initialization default portfolio
        portfolio = Portfolio()
        self._local_fallback = portfolio
        await self.save_portfolio(portfolio)
        return portfolio

    async def save_portfolio(self, portfolio: Portfolio) -> bool:
        """
        Saves the current portfolio state in Redis.
        """
        self._local_fallback = portfolio
        from app.config.settings import settings
        if settings.BACKTEST_SPEED_MODE:
            return True

        try:
            await self.redis.set(
                name=self._portfolio_key,
                value=portfolio.model_dump_json(),
            )
            return True
        except Exception as e:
            logger.error(f"Error saving paper portfolio to Redis: {e}")
            return False

    async def open_position(self, symbol: str, entry_price: float) -> Union[Trade, None]:
        """
        Checks buying power, allocates 10% of available balance, and creates an open trade.
        """
        portfolio = await self.get_portfolio()
        
        # Avoid opening multiple concurrent positions for the same symbol to prevent over-allocation
        for pos in portfolio.open_positions:
            if pos.symbol == symbol:
                logger.debug(f"Position already open for {symbol}. Skipping double entry.")
                return None

        # Position allocation USDT size: 10% of available balance
        allocation_value = portfolio.available_balance * 0.10
        if allocation_value < 10.0:  # Minimum trade threshold limit
            logger.warning(
                f"Insufficient balance to open position for {symbol}. "
                f"Available: {portfolio.available_balance:.2f} USDT"
            )
            return None

        # Calculate quantity and update balances
        quantity = allocation_value / entry_price
        portfolio.available_balance -= allocation_value
        
        # Create trade object
        trade = Trade(
            symbol=symbol,
            direction="LONG",
            entry_price=entry_price,
            quantity=quantity,
            status="OPEN",
            opened_at=datetime.now(timezone.utc),
        )
        
        portfolio.open_positions.append(trade)
        await self.save_portfolio(portfolio)
        
        # Persist trade record to PostgreSQL
        try:
            from app.database.session import async_session_factory
            from app.database.models import TradeRecord
            from app.database.repositories.trade_repository import TradeRepository
            
            db_trade = TradeRecord(
                trade_id=trade.trade_id,
                symbol=trade.symbol,
                direction=trade.direction,
                entry_price=trade.entry_price,
                quantity=trade.quantity,
                profit_loss=trade.profit_loss,
                status=trade.status,
                opened_at=trade.opened_at
            )
            async with async_session_factory() as session:
                async with session.begin():
                    await TradeRepository.save(session, db_trade)
            logger.info(f"Persisted TradeRecord {trade.trade_id} to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to persist TradeRecord {trade.trade_id} to PostgreSQL: {e}")

        # Save portfolio snapshot to PostgreSQL
        await self.save_portfolio_snapshot(portfolio)

        logger.info(
            f"Opened LONG position for {symbol} | Entry Price: {entry_price:.4f} | "
            f"Qty: {quantity:.6f} | Allocated: {allocation_value:.2f} USDT"
        )
        return trade

    async def close_position(self, trade_id: str, exit_price: float, reason: str) -> Union[Trade, None]:
        """
        Closes an open trade position, calculates profits/losses, and restores buying power.
        """
        portfolio = await self.get_portfolio()
        target_trade = None
        
        # Locate the open trade
        for trade in portfolio.open_positions:
            if trade.trade_id == trade_id:
                target_trade = trade
                break
                
        if not target_trade:
            logger.error(f"Failed to find active open trade {trade_id} to close.")
            return None

        # Calculate trade statistics
        portfolio.open_positions.remove(target_trade)
        
        target_trade.exit_price = exit_price
        target_trade.status = "CLOSED"
        target_trade.closed_at = datetime.now(timezone.utc)
        
        principal_allocated = target_trade.entry_price * target_trade.quantity
        realized_value = exit_price * target_trade.quantity
        pnl = realized_value - principal_allocated
        
        target_trade.profit_loss = pnl
        
        # Return principal + PnL back to available balance
        portfolio.available_balance += realized_value
        
        if pnl >= 0:
            portfolio.total_profit += pnl
        else:
            portfolio.total_loss += abs(pnl)
            
        portfolio.closed_trades.append(target_trade)
        await self.save_portfolio(portfolio)
        
        # Update trade record in PostgreSQL
        try:
            from app.database.session import async_session_factory
            from app.database.repositories.trade_repository import TradeRepository
            
            async with async_session_factory() as session:
                async with session.begin():
                    db_trade = await TradeRepository.get_by_trade_id(session, trade_id)
                    if db_trade:
                        db_trade.exit_price = target_trade.exit_price
                        db_trade.profit_loss = target_trade.profit_loss
                        db_trade.status = target_trade.status
                        db_trade.closed_at = target_trade.closed_at
                        logger.info(f"Updated TradeRecord {trade_id} to CLOSED in PostgreSQL.")
                    else:
                        logger.error(f"TradeRecord {trade_id} not found in PostgreSQL to close.")
        except Exception as e:
            logger.error(f"Failed to update TradeRecord {trade_id} in PostgreSQL: {e}")

        # Save portfolio snapshot to PostgreSQL
        await self.save_portfolio_snapshot(portfolio)

        logger.info(
            f"Closed position for {target_trade.symbol} | Entry: {target_trade.entry_price:.4f} | "
            f"Exit: {exit_price:.4f} | PnL: {pnl:.2f} USDT ({reason})"
        )
        return target_trade

    async def save_portfolio_snapshot(self, portfolio: Portfolio) -> None:
        """
        Saves a snapshot of the virtual portfolio to PostgreSQL.
        """
        try:
            from app.database.session import async_session_factory
            from app.database.models import PortfolioSnapshot
            
            snapshot = PortfolioSnapshot(
                timestamp=datetime.now(timezone.utc),
                starting_balance=portfolio.starting_balance,
                available_balance=portfolio.available_balance,
                total_profit=portfolio.total_profit,
                total_loss=portfolio.total_loss,
                open_positions_count=len(portfolio.open_positions),
                closed_trades_count=len(portfolio.closed_trades)
            )
            async with async_session_factory() as session:
                async with session.begin():
                    session.add(snapshot)
            logger.info("Persisted PortfolioSnapshot to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to persist PortfolioSnapshot to PostgreSQL: {e}")


# Global manager instance
portfolio_manager = PortfolioManager()
