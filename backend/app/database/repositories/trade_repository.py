from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import TradeRecord


class TradeRepository:
    """
    Repository handling database operations for TradeRecord.
    """
    @staticmethod
    async def save(session: AsyncSession, record: TradeRecord) -> TradeRecord:
        """
        Saves a trade record to the database.
        """
        session.add(record)
        await session.flush()
        return record

    @staticmethod
    async def get_by_trade_id(session: AsyncSession, trade_id: str) -> Optional[TradeRecord]:
        """
        Retrieves a trade record by its unique trade_id.
        """
        stmt = select(TradeRecord).where(TradeRecord.trade_id == trade_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_open_trades(session: AsyncSession, symbol: Optional[str] = None) -> List[TradeRecord]:
        """
        Retrieves all active open trades, optionally filtered by symbol.
        """
        stmt = select(TradeRecord).where(TradeRecord.status == "OPEN")
        if symbol:
            stmt = stmt.where(TradeRecord.symbol == symbol.upper())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_trades(session: AsyncSession) -> List[TradeRecord]:
        """
        Retrieves all trades.
        """
        stmt = select(TradeRecord).order_by(TradeRecord.opened_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
