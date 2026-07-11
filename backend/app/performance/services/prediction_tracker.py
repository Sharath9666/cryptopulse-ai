"""
Prediction Performance Tracker Service.
Listens for new predictions, stores snapshots, and schedules future evaluations.
"""

import asyncio
from datetime import datetime, timezone
import json
from loguru import logger
from redis.asyncio import Redis

from app.cache.redis import get_redis_client
from app.config.settings import settings
from app.prediction.models.prediction import Prediction
from app.performance.models.prediction_record import PredictionRecord
from app.performance.services.accuracy_engine import accuracy_engine
from app.performance.health import performance_health_tracker


class PredictionTracker:
    """
    Subscribes to PredictionCreatedEvent to track and schedule accuracy reviews.
    """
    def __init__(self, redis_client: Redis = None) -> None:
        self._redis_client = redis_client
        self._local_records = {}

    @property
    def redis(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    async def track_prediction(self, prediction: Prediction) -> None:
        """
        Extracts entry price, persists a prediction snapshot in Redis,
        and schedules an evaluation task to run after the configured delay.
        """
        symbol = prediction.symbol.upper()
        prediction_uuid = str(datetime.now().timestamp()) # Fallback UUID or similar, we can map to prediction timestamp/id
        
        # Wait, the Prediction model does not contain a prediction_id!
        # But we can generate a unique tracking ID using symbol and timestamp
        record_id = f"{symbol}_{int(prediction.timestamp.timestamp())}"
        
        logger.info(f"Tracking new prediction for {symbol} (ID: {record_id})")

        from app.config.settings import settings
        entry_price = None

        if settings.BACKTEST_SPEED_MODE:
            from app.features.services.feature_engine import feature_engine
            candles = feature_engine.history.get(symbol, [])
            if candles:
                entry_price = candles[-1].close
            else:
                entry_price = 1.0  # Fallback
        else:
            try:
                # 1. Fetch current price from market cache in Redis
                market_key = f"market:{symbol}"
                raw_tick = await self.redis.get(market_key)
                
                if not raw_tick:
                    logger.warning(f"No current tick price available for {symbol} in Redis. Cannot track prediction.")
                    return

                tick_dict = json.loads(raw_tick)
                entry_price = float(tick_dict["price"])
            except Exception as e:
                logger.error(f"Error loading price for {symbol} from Redis: {e}")
                return

        try:
            # 2. Construct PredictionRecord
            record = PredictionRecord(
                prediction_id=record_id,
                symbol=symbol,
                timeframe=prediction.timeframe,
                direction=prediction.direction,
                confidence=prediction.confidence,
                predicted_move=prediction.expected_move_percent,
                entry_price=entry_price,
                prediction_time=prediction.timestamp,
            )

            # 3. Store record in Redis
            if not settings.BACKTEST_SPEED_MODE:
                redis_key = f"perf_pred:{record_id}"
                await self.redis.set(
                    name=redis_key,
                    value=record.model_dump_json(),
                    ex=86400 * 7,  # Cache prediction records for 7 days
                )
            else:
                self._local_records[record_id] = record
                logger.debug(f"Speed mode enabled. Bypassing Redis cache for prediction record: {record_id}")

            # Persist to PostgreSQL permanent history
            try:
                from app.database.session import async_session_factory
                from app.database.models import PredictionRecord as DbPredictionRecord
                from app.database.repositories.prediction_repository import PredictionRepository
                
                db_record = DbPredictionRecord(
                    prediction_id=record_id,
                    symbol=symbol,
                    timeframe=prediction.timeframe,
                    direction=prediction.direction,
                    confidence=prediction.confidence,
                    predicted_move=prediction.expected_move_percent,
                    entry_price=entry_price,
                    prediction_time=prediction.timestamp
                )
                async with async_session_factory() as session:
                    async with session.begin():
                        await PredictionRepository.save(session, db_record)
                logger.info(f"Persisted PENDING PredictionRecord {record_id} to PostgreSQL.")
            except Exception as e:
                logger.error(f"Failed to persist PENDING PredictionRecord {record_id} to PostgreSQL: {e}")

            # 4. Update health tracker metrics
            performance_health_tracker.receive_prediction(symbol, prediction.confidence)

            # 5. Schedule asynchronous delayed evaluation
            eval_delay = 0 if settings.BACKTEST_SPEED_MODE else settings.PERFORMANCE_EVALUATION_PERIOD_SECONDS
            asyncio.create_task(self._scheduled_evaluation(record_id, eval_delay))
            logger.info(f"Scheduled evaluation for prediction {record_id} in {eval_delay} seconds.")

        except Exception as e:
            logger.error(f"Error tracking prediction for {symbol}: {e}")

    async def _scheduled_evaluation(self, record_id: str, delay_seconds: int) -> None:
        """
        Asynchronous background task sleeping for a configured period
        before calling the accuracy engine to evaluate the prediction.
        """
        await asyncio.sleep(delay_seconds)
        await accuracy_engine.evaluate_prediction(record_id)


# Global tracker service instance
prediction_tracker = PredictionTracker()
