"""
Backtest runner service.
Coordinates downloading historical data, executing replay streams, and computing metrics.
"""

import asyncio
from datetime import datetime
from loguru import logger
import uuid

from app.paper_trading.services.portfolio_manager import portfolio_manager
from app.backtesting.models.backtest_result import BacktestResult
from app.backtesting.services.historical_data_service import HistoricalDataService
from app.backtesting.services.market_replay_engine import MarketReplayEngine
from app.backtesting.publisher import BacktestPublisher
from app.backtesting.health import backtest_health_tracker


class BacktestRunner:
    """
    Runner class executing the backtest pipeline end-to-end.
    """
    def __init__(
        self,
        data_service: HistoricalDataService = None,
        replay_engine: MarketReplayEngine = None,
        publisher: BacktestPublisher = None
    ) -> None:
        self.data_service = data_service or HistoricalDataService()
        self.replay_engine = replay_engine or MarketReplayEngine()
        self.publisher = publisher or BacktestPublisher()

    async def run(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        starting_balance: float = 100000.0,
        backtest_id: str = None
    ) -> BacktestResult:
        """
        Coordinates historical data download, feeds the stream, and yields performance statistics.
        """
        symbol_upper = symbol.upper()
        if not backtest_id:
            backtest_id = str(uuid.uuid4())
        
        # 1. Update health status
        backtest_health_tracker.start_backtest()
        logger.info(f"Starting Backtest session {backtest_id} for {symbol_upper} ({timeframe})")

        # 2. Reset paper portfolio virtual state for this simulation run
        portfolio = await portfolio_manager.get_portfolio()
        portfolio.starting_balance = starting_balance
        portfolio.available_balance = starting_balance
        portfolio.total_profit = 0.0
        portfolio.total_loss = 0.0
        portfolio.open_positions = []
        portfolio.closed_trades = []
        await portfolio_manager.save_portfolio(portfolio)
        logger.info(f"Reset virtual paper portfolio balance to {starting_balance:.2f} USDT")

        try:
            # 3. Download historical candles
            candles = await self.data_service.fetch_candles(
                symbol=symbol_upper,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )

            if not candles:
                logger.error("No historical candles fetched. Aborting backtest.")
                result = self._empty_result(backtest_id, symbol_upper, timeframe)
                backtest_health_tracker.complete_backtest(result)
                return result

            # 4. Stream candles via MarketReplayEngine
            await self.replay_engine.replay(candles)

            # 5. Let the queue settle to ensure all events are dispatched
            from app.events import event_bus
            await event_bus._queue.join()

            # 6. Close any remaining open positions at the last candle price
            final_portfolio = await portfolio_manager.get_portfolio()
            if candles and final_portfolio.open_positions:
                last_price = candles[-1].close
                open_trades = list(final_portfolio.open_positions)
                for trade in open_trades:
                    await portfolio_manager.close_position(
                        trade_id=trade.trade_id,
                        exit_price=last_price,
                        reason="Forced backtest end closure"
                    )
                # Reload portfolio state after closing positions
                final_portfolio = await portfolio_manager.get_portfolio()
            result = self._calculate_metrics(
                backtest_id=backtest_id,
                symbol=symbol_upper,
                timeframe=timeframe,
                starting_balance=starting_balance,
                closed_trades=final_portfolio.closed_trades,
                total_profit=final_portfolio.total_profit,
                total_loss=final_portfolio.total_loss
            )

            # 7. Persist result in Redis and update health metrics
            await self.publisher.save_result(result)
            backtest_health_tracker.complete_backtest(result)
            
            logger.info(
                f"Backtest {backtest_id} complete. Trades: {result.total_trades} | "
                f"Net Profit: {result.total_profit:.2f} USDT ({result.profit_percentage:.2f}%)"
            )
            return result

        except Exception as e:
            logger.error(f"Error running backtest {backtest_id}: {e}")
            result = self._empty_result(backtest_id, symbol_upper, timeframe)
            backtest_health_tracker.complete_backtest(result)
            return result

    def _calculate_metrics(
        self,
        backtest_id: str,
        symbol: str,
        timeframe: str,
        starting_balance: float,
        closed_trades: list,
        total_profit: float,
        total_loss: float
    ) -> BacktestResult:
        """
        Computes win rates, maximum drawdown, and return averages.
        """
        total_trades = len(closed_trades)
        winning_trades = sum(1 for t in closed_trades if t.profit_loss > 0.0)
        losing_trades = sum(1 for t in closed_trades if t.profit_loss < 0.0)
        
        win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0
        net_profit = total_profit - total_loss
        profit_pct = (net_profit / starting_balance) * 100.0

        # Calculate Average Trade Return percent
        trade_returns = []
        for t in closed_trades:
            cost = t.entry_price * t.quantity
            if cost > 0:
                trade_returns.append((t.profit_loss / cost) * 100.0)
        avg_trade_return = (sum(trade_returns) / len(trade_returns)) if trade_returns else 0.0

        # Calculate Maximum Drawdown using equity curve step analysis
        current_equity = starting_balance
        equity_curve = [starting_balance]
        for t in closed_trades:
            current_equity += t.profit_loss
            equity_curve.append(current_equity)

        peak = starting_balance
        max_dd = 0.0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
        
        max_drawdown_pct = max_dd * 100.0

        return BacktestResult(
            backtest_id=backtest_id,
            symbol=symbol,
            timeframe=timeframe,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit=net_profit,
            profit_percentage=profit_pct,
            maximum_drawdown=max_drawdown_pct,
            average_trade_return=avg_trade_return
        )

    def _empty_result(self, backtest_id: str, symbol: str, timeframe: str) -> BacktestResult:
        return BacktestResult(
            backtest_id=backtest_id,
            symbol=symbol,
            timeframe=timeframe,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_profit=0.0,
            profit_percentage=0.0,
            maximum_drawdown=0.0,
            average_trade_return=0.0
        )


# Global runner instance
backtest_runner = BacktestRunner()
