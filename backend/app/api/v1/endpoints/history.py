"""
History endpoints for Candles, Predictions, and Trades.
Provides production-grade paginated query endpoints over SQLAlchemy PostgreSQL data.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependencies import get_db
from app.database.models import MarketCandle, PredictionRecord, TradeRecord
from app.api.v1.schemas.records import MarketCandleSchema, PredictionRecordSchema, TradeRecordSchema
from app.api.v1.schemas.common import PaginatedResponse, APIErrorResponse

router = APIRouter()


@router.get(
    "/candles",
    response_model=PaginatedResponse[MarketCandleSchema],
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": APIErrorResponse}},
    summary="Query historical market candles",
    description="Retrieve paginated historical OHLCV market candles from database persistence."
)
async def get_candles_history(
    symbol: Optional[str] = Query(None, description="Filter by trading pair symbol (e.g. BTCUSDT)"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe (e.g. '1m', '1h')"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[MarketCandleSchema]:
    # Query building
    stmt = select(MarketCandle)
    count_stmt = select(func.count(MarketCandle.id))

    if symbol:
        stmt = stmt.where(MarketCandle.symbol == symbol.upper())
        count_stmt = count_stmt.where(MarketCandle.symbol == symbol.upper())
    if timeframe:
        stmt = stmt.where(MarketCandle.timeframe == timeframe)
        count_stmt = count_stmt.where(MarketCandle.timeframe == timeframe)

    # Count total
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Paginate and order by start_time descending (newest first)
    stmt = stmt.order_by(MarketCandle.start_time.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=[MarketCandleSchema.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get(
    "/predictions",
    response_model=PaginatedResponse[PredictionRecordSchema],
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": APIErrorResponse}},
    summary="Query historical ML & rule-based predictions",
    description="Retrieve paginated historical prediction records with evaluation outcomes from database persistence."
)
async def get_predictions_history(
    symbol: Optional[str] = Query(None, description="Filter by trading pair symbol (e.g. BTCUSDT)"),
    correct: Optional[bool] = Query(None, description="Filter by prediction correctness status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[PredictionRecordSchema]:
    stmt = select(PredictionRecord)
    count_stmt = select(func.count(PredictionRecord.id))

    if symbol:
        stmt = stmt.where(PredictionRecord.symbol == symbol.upper())
        count_stmt = count_stmt.where(PredictionRecord.symbol == symbol.upper())
    if correct is not None:
        stmt = stmt.where(PredictionRecord.correct == correct)
        count_stmt = count_stmt.where(PredictionRecord.correct == correct)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = stmt.order_by(PredictionRecord.prediction_time.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=[PredictionRecordSchema.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get(
    "/trades",
    response_model=PaginatedResponse[TradeRecordSchema],
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": APIErrorResponse}},
    summary="Query historical paper trading positions",
    description="Retrieve paginated simulated trades and positions history from database persistence."
)
async def get_trades_history(
    symbol: Optional[str] = Query(None, description="Filter by trading pair symbol (e.g. BTCUSDT)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (OPEN or CLOSED)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[TradeRecordSchema]:
    stmt = select(TradeRecord)
    count_stmt = select(func.count(TradeRecord.id))

    if symbol:
        stmt = stmt.where(TradeRecord.symbol == symbol.upper())
        count_stmt = count_stmt.where(TradeRecord.symbol == symbol.upper())
    if status_filter:
        stmt = stmt.where(TradeRecord.status == status_filter.upper())
        count_stmt = count_stmt.where(TradeRecord.status == status_filter.upper())

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = stmt.order_by(TradeRecord.opened_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    pages = (total + size - 1) // size
    return PaginatedResponse(
        items=[TradeRecordSchema.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
        pages=pages
    )
