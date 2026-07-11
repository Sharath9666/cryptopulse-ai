"""
Prediction Engine coordinator service.

Orchestrates ML (XGBoost) → rule-engine fallback chain:
  1. Try XGBoost via MLPredictor.predict()
  2. If ML returns None (no model / low confidence / error) → fall back to ScoringEngine
  3. Build Prediction object and publish via PredictionPublisher

The source field in each Prediction records which path was taken.
"""

from datetime import datetime, timezone
import time
from loguru import logger

from app.features.models.feature_vector import FeatureVector
from app.prediction.models.prediction import Prediction
from app.prediction.services.scoring_engine import ScoringEngine
from app.prediction.publisher import PredictionPublisher
from app.prediction.health import prediction_health_tracker


class PredictionEngineService:
    """
    Orchestrates the ML prediction pipeline with rule-engine fallback.

    ML path (when XGBoost model is available and confident):
        FeatureVector → MLPredictor → Prediction(source="ml")

    Fallback path (no model, low confidence, or inference error):
        FeatureVector → ScoringEngine → Prediction(source="rules")
    """

    def __init__(self, publisher: PredictionPublisher = None) -> None:
        self.publisher = publisher or PredictionPublisher()
        # Import lazily to avoid circular imports at module load time
        self._ml_predictor = None

    @property
    def ml_predictor(self):
        if self._ml_predictor is None:
            from app.ml.predictor import ml_predictor
            self._ml_predictor = ml_predictor
        return self._ml_predictor

    # ------------------------------------------------------------------
    # Primary prediction path: FeatureVector → Prediction
    # ------------------------------------------------------------------

    async def generate_prediction(self, fv: FeatureVector) -> None:
        """
        Generate a prediction from a FeatureVector and publish the result.

        Tries XGBoost first; falls back to rule engine if ML is unavailable,
        has low confidence, or raises an exception.
        """
        start_time = time.perf_counter()
        symbol = fv.symbol.upper()

        try:
            # ---- ML path ----
            ml_result = await self.ml_predictor.predict(fv)

            if ml_result is not None:
                prediction = Prediction(
                    symbol=symbol,
                    timeframe=fv.timeframe,
                    timestamp=datetime.now(timezone.utc),
                    direction=ml_result.direction,
                    probability=ml_result.probability,
                    confidence=ml_result.confidence,
                    expected_move_percent=ml_result.expected_return,
                    features_used=ml_result.features_used,
                    reasoning=(
                        f"XGBoost model {ml_result.model_version}: "
                        f"{ml_result.direction} with p={ml_result.probability:.4f}. "
                        f"Class probs: {ml_result.class_probabilities}"
                    ),
                    source="ml",
                    model_version=ml_result.model_version,
                )
                path_label = f"ml/{ml_result.model_version}"
            else:
                # ---- Rule fallback ----
                direction, prob, conf, move, features_used, reasoning = (
                    ScoringEngine.score_features(fv)
                )
                prediction = Prediction(
                    symbol=symbol,
                    timeframe=fv.timeframe,
                    timestamp=datetime.now(timezone.utc),
                    direction=direction,
                    probability=prob,
                    confidence=conf,
                    expected_move_percent=move,
                    features_used=features_used,
                    reasoning=reasoning,
                    source="rules",
                    model_version=None,
                )
                path_label = "rules"

            # Publish
            await self.publisher.publish(prediction)

            # Update metrics
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            prediction_health_tracker.update_metrics(symbol, latency_ms, source=path_label)

            logger.info(
                f"Prediction [{symbol}|{fv.timeframe}] "
                f"src={path_label} dir={prediction.direction} "
                f"p={prediction.probability:.4f} conf={prediction.confidence} "
                f"latency={latency_ms:.2f}ms"
            )

        except Exception as e:
            logger.error(f"Error generating prediction for {symbol}: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Secondary path: StrategySignal → Prediction
    # ------------------------------------------------------------------

    async def generate_prediction_from_signal(self, signal: "StrategySignal") -> None:
        """
        Processes strategy signals directly into predictions.
        Strategy signals bypass the ML layer (they are already processed).
        """
        start_time = time.perf_counter()
        symbol = signal.symbol.upper()

        try:
            conf_level = "LOW"
            if signal.confidence >= 0.80:
                conf_level = "HIGH"
            elif signal.confidence >= 0.70:
                conf_level = "MEDIUM"

            prediction = Prediction(
                symbol=symbol,
                timeframe="1m",
                timestamp=datetime.now(timezone.utc),
                direction=signal.direction,
                probability=signal.confidence,
                confidence=conf_level,
                expected_move_percent=(
                    3.0 if signal.direction == "BULLISH"
                    else -2.0 if signal.direction == "BEARISH"
                    else 0.0
                ),
                features_used=["strategy_signal"],
                reasoning=signal.reasoning,
                source="rules",
                model_version=None,
            )

            await self.publisher.publish(prediction)

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            prediction_health_tracker.update_metrics(symbol, latency_ms, source="rules")

            logger.info(
                f"Prediction from StrategySignal [{symbol}] "
                f"dir={signal.direction} conf={signal.confidence:.4f} "
                f"latency={latency_ms:.2f}ms"
            )
        except Exception as e:
            logger.error(
                f"Error mapping strategy signal to prediction for {symbol}: {e}",
                exc_info=True,
            )


# Global service instance
prediction_engine = PredictionEngineService()
