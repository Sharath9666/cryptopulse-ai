from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import PredictionRecord


class PredictionRepository:
    """
    Repository handling database operations for PredictionRecord.
    """
    @staticmethod
    async def save(session: AsyncSession, record: PredictionRecord) -> PredictionRecord:
        """
        Saves a prediction record to the database.
        """
        session.add(record)
        await session.flush()
        return record

    @staticmethod
    async def get_by_prediction_id(session: AsyncSession, prediction_id: str) -> Optional[PredictionRecord]:
        """
        Retrieves a prediction record by its unique prediction_id.
        """
        stmt = select(PredictionRecord).where(PredictionRecord.prediction_id == prediction_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
