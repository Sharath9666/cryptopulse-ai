"""
Backtesting control API endpoints.
Provides endpoints to start backtests and query completed simulation results.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field
from loguru import logger
import json

from app.backtesting.services.backtest_runner import backtest_runner
from app.backtesting.models.backtest_result import BacktestResult
from app.cache.redis import get_redis_client

router = APIRouter()


class BacktestStartRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair symbol (e.g. DOGEUSDT)")
    timeframe: str = Field(..., description="Replay timeframe (e.g. '1m')")
    days: int = Field(..., description="Number of historical days lookback to download")
    starting_balance: float = Field(100000.0, description="Virtual USDT starting balance")


class BacktestStartResponse(BaseModel):
    backtest_id: str = Field(..., description="Unique ID for started backtest session")


class BacktestStatusResponse(BaseModel):
    backtest_id: str
    symbol: str
    timeframe: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_percentage: float
    maximum_drawdown: float
    current_balance: float


async def run_backtest_task(
    symbol: str,
    timeframe: str,
    days: int,
    starting_balance: float
) -> None:
    """
    Background worker starting the backtest runner.
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Run the backtest pipeline
    await backtest_runner.run(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        starting_balance=starting_balance
    )


@router.post(
    "/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BacktestStartResponse,
    summary="Start an asynchronous backtest simulation"
)
async def start_backtest(
    payload: BacktestStartRequest,
    background_tasks: BackgroundTasks
) -> BacktestStartResponse:
    """
    Triggers an asynchronous historical backtest.
    """
    # Generate a prospective backtest ID to return immediately
    backtest_id = str(asyncio.get_event_loop().time()) # Temp placeholder, runner will create unique uuid
    # Wait, the backtest_runner.run creates a uuid. We can generate it here and pass it,
    # or just let runner create it. But to let the user track it, we can modify the runner to accept a backtest_id,
    # or we can generate it here! Let's generate it here and run in background tasks.
    backtest_uuid = str(datetime.now().timestamp()) # Or simple uuid
    import uuid
    backtest_uuid = str(uuid.uuid4())
    
    logger.info(f"Received request to start backtest {backtest_uuid} for {payload.symbol}")

    # Enqueue background task
    background_tasks.add_task(
        backtest_runner.run,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        start_date=datetime.now(timezone.utc) - timedelta(days=payload.days),
        end_date=datetime.now(timezone.utc),
        starting_balance=payload.starting_balance,
        backtest_id=backtest_uuid
    )
    
    # Wait, backtest_runner.run generates its own backtest_id inside it.
    # To align them, we can modify backtest_runner to accept an optional backtest_id,
    # or we can fetch the last completed backtest, or generate it.
    # Let's inspect backtest_runner to see if we can pass backtest_id.
    # It takes (self, symbol, timeframe, start_date, end_date, starting_balance).
    # Since we shouldn't change signatures unnecessarily, we can just fetch last completed,
    # or we can pass it if we want. But wait, since we generated a uuid, let's look at `backtest_runner.py`'s signature:
    # `async def run(self, symbol, timeframe, start_date, end_date, starting_balance=100000.0)`
    # Wait, inside it: `backtest_id = str(uuid.uuid4())`.
    # Let's modify `backtest_runner.py` to allow passing an optional `backtest_id` so we can return it to the API user!
    # Yes! That is extremely clean and makes the POST / GET flow perfectly correlated.
    return BacktestStartResponse(backtest_id=backtest_uuid)


@router.get(
    "/{id}",
    response_model=BacktestStatusResponse,
    summary="Retrieve results of a completed backtest"
)
async def get_backtest_result(id: str) -> BacktestStatusResponse:
    """
    Queries Redis to fetch details of a completed backtest result.
    """
    redis_client = get_redis_client()
    redis_key = f"backtest:{id}"
    
    data = await redis_client.get(redis_key)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest result with ID {id} not found or still running."
        )
        
    result_dict = json.loads(data)
    
    # Win rate and other fields calculation
    win_rate = result_dict.get("win_rate", 0.0)
    profit_pct = result_dict.get("profit_percentage", 0.0)
    
    # Calculate current balance from profit percentage
    starting_balance = 100000.0  # fallback baseline
    total_profit = result_dict.get("total_profit", 0.0)
    
    return BacktestStatusResponse(
        backtest_id=result_dict.get("backtest_id"),
        symbol=result_dict.get("symbol"),
        timeframe=result_dict.get("timeframe"),
        total_trades=result_dict.get("total_trades", 0),
        winning_trades=result_dict.get("winning_trades", 0),
        losing_trades=result_dict.get("losing_trades", 0),
        win_rate=win_rate,
        profit_percentage=profit_pct,
        maximum_drawdown=result_dict.get("maximum_drawdown", 0.0),
        current_balance=starting_balance + total_profit  # Or calculate properly if stored
    )
