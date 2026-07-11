"""
Prediction Accuracy Evaluation Engine.
Evaluates directional predictions against actual historical outcomes over configured periods.
"""

from datetime import datetime, timezone
import json
from loguru import logger
from redis.asyncio import Redis

from app.cache.redis import get_redis_client
from app.performance.models.prediction_record import PredictionRecord
from app.performance.health import performance_health_tracker


class AccuracyEngine:
    """
    Evaluates historical predictions against market price realities.
    """
    def __init__(self, redis_client: Redis = None) -> None:
        self._redis_client = redis_client

    @property
    def redis(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    async def evaluate_prediction(self, record_id: str) -> None:
        """
        Loads the prediction snapshot from Redis, fetches the current price,
        determines directional accuracy, and saves the evaluation.
        """
        redis_key = f"perf_pred:{record_id}"
        
        try:
            from app.config.settings import settings
            if settings.BACKTEST_SPEED_MODE:
                from app.performance.services.prediction_tracker import prediction_tracker
                record = prediction_tracker._local_records.get(record_id)
                if not record:
                    logger.error(f"Cannot find prediction record {record_id} in local fallback for evaluation.")
                    return
                symbol = record.symbol.upper()
                
                from app.features.services.feature_engine import feature_engine
                candles = feature_engine.history.get(symbol, [])
                if candles:
                    current_price = candles[-1].close
                else:
                    current_price = record.entry_price
            else:
                try:
                    # 1. Fetch prediction record
                    data = await self.redis.get(redis_key)
                    if not data:
                        logger.error(f"Cannot find prediction record {record_id} in Redis for evaluation.")
                        return

                    record = PredictionRecord.model_validate_json(data)
                    symbol = record.symbol.upper()
                    
                    # 2. Query current price from market cache
                    market_key = f"market:{symbol}"
                    raw_tick = await self.redis.get(market_key)
                    
                    if not raw_tick:
                        logger.warning(
                            f"No current tick price available for {symbol} to evaluate {record_id}. "
                            f"Skipping evaluation."
                        )
                        return

                    tick_dict = json.loads(raw_tick)
                    current_price = float(tick_dict["price"])
                except Exception as e:
                    logger.error(f"Error reading prediction details from Redis: {e}")
                    return

            # 3. Calculate profit movement
            profit = current_price - record.entry_price
            direction_upper = record.direction.upper()

            # Rules:
            # - BULLISH: profit > 0 (current_price > entry_price) -> correct
            # - BEARISH: profit < 0 (current_price < entry_price) -> correct
            # - NEUTRAL: profit == 0 (current_price == entry_price) -> correct
            if direction_upper == "BULLISH":
                correct = profit > 0.0
            elif direction_upper == "BEARISH":
                correct = profit < 0.0
            else:
                correct = profit == 0.0

            # Calculate actual percentage move
            actual_move = 0.0
            if record.entry_price > 0.0:
                actual_move = (profit / record.entry_price) * 100.0

            # 4. Update the record
            record.evaluation_time = datetime.now(timezone.utc)
            record.actual_price = current_price
            record.actual_move = actual_move
            record.correct = correct

            # 5. Persist the updated record back to Redis
            if not settings.BACKTEST_SPEED_MODE:
                try:
                    await self.redis.set(
                        name=redis_key,
                        value=record.model_dump_json(),
                        ex=86400 * 7,  # Cache results for 7 days
                    )
                except Exception as e:
                    logger.error(f"Error persisting evaluation back to Redis: {e}")
            else:
                # Update local fallback
                from app.performance.services.prediction_tracker import prediction_tracker
                prediction_tracker._local_records[record_id] = record

            # Update in PostgreSQL permanent history
            try:
                from app.database.session import async_session_factory
                from app.database.repositories.prediction_repository import PredictionRepository
                
                async with async_session_factory() as session:
                    async with session.begin():
                        db_record = await PredictionRepository.get_by_prediction_id(session, record_id)
                        if db_record:
                            db_record.evaluation_time = record.evaluation_time
                            db_record.actual_price = record.actual_price
                            db_record.actual_move = record.actual_move
                            db_record.correct = record.correct
                            logger.info(f"Updated PredictionRecord {record_id} evaluation in PostgreSQL.")
                        else:
                            logger.error(f"PredictionRecord {record_id} not found in PostgreSQL to update.")
            except Exception as e:
                logger.error(f"Failed to update PredictionRecord {record_id} in PostgreSQL: {e}")

            # 6. Update global accuracy tracking metrics
            performance_health_tracker.register_evaluation(correct)
            
            logger.info(
                f"Evaluated Prediction {record_id} ({symbol}) | "
                f"Entry: {record.entry_price:.4f} | Actual: {current_price:.4f} | "
                f"Dir: {record.direction} | Correct: {correct}"
            )

        except Exception as e:
            logger.error(f"Error evaluating prediction {record_id}: {e}")


# Global accuracy engine instance
accuracy_engine = AccuracyEngine()
