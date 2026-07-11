from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import MarketCandle


class CandleRepository:
    """
    Repository handling database operations for MarketCandle.
    """
    @staticmethod
    async def save_batch(session: AsyncSession, candles: List[MarketCandle]) -> None:
        """
        Saves a batch of market candles to the database.
        """
        session.add_all(candles)
        await session.flush()

    @staticmethod
    async def get_candles(
        session: AsyncSession,
        symbol: str,
        timeframe: str,
        limit: int = 300
    ) -> List[MarketCandle]:
        """
        Retrieves the latest candles for a given symbol and timeframe, ordered chronologically.
        """
        stmt = (
            select(MarketCandle)
            .where(MarketCandle.symbol == symbol.upper())
            .where(MarketCandle.timeframe == timeframe)
            .order_by(MarketCandle.start_time.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        # Reverse to get chronological order (oldest to newest)
        return list(reversed(result.scalars().all()))
