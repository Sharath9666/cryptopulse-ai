"""
ModelTrainer — builds, trains, evaluates, and saves XGBoost classifiers.

Training pipeline:
    1. Accept list[FeatureVector] + corresponding labels
    2. Extract numpy feature matrix via FeatureExtractor
    3. Train StandardScaler → XGBClassifier pipeline
    4. Evaluate on held-out test set (80/20 split)
    5. Save versioned model via ModelRegistry

Label generation (bootstrapped):
    The trainer accepts pre-computed integer labels OR can auto-label via
    ScoringEngine when only FeatureVectors are supplied.

    Direction → label mapping:
        BEARISH → 0
        NEUTRAL → 1
        BULLISH → 2

CLI usage:
    python -m app.ml.trainer --symbol BTCUSDT [--min-samples 50]
"""

from __future__ import annotations

import asyncio
import argparse
from typing import Optional

import numpy as np
from loguru import logger
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier

from app.features.models.feature_vector import FeatureVector
from app.ml.config import (
    DIRECTION_TO_LABEL,
    FEATURE_COLUMNS,
    XGBOOST_PARAMS,
)
from app.ml.features import FeatureExtractor
from app.ml.model import ModelRegistry, model_registry


class TrainingResult:
    """Holds the outcome of a completed training run."""

    def __init__(
        self,
        symbol: str,
        version: str,
        accuracy: float,
        n_samples: int,
        classification_report_str: str,
        cv_scores: list[float],
    ) -> None:
        self.symbol = symbol
        self.version = version
        self.accuracy = accuracy
        self.n_samples = n_samples
        self.classification_report_str = classification_report_str
        self.cv_scores = cv_scores

    def __repr__(self) -> str:
        return (
            f"TrainingResult(symbol={self.symbol}, version={self.version}, "
            f"accuracy={self.accuracy:.4f}, n_samples={self.n_samples}, "
            f"cv_mean={np.mean(self.cv_scores):.4f})"
        )


class ModelTrainer:
    """
    Trains XGBoost classifiers on FeatureVector data.

    Usage:
        trainer = ModelTrainer()

        # With pre-labelled data:
        result = trainer.train(symbol="BTCUSDT", feature_vectors=fvs, labels=labels)

        # Auto-labelled via ScoringEngine:
        result = trainer.train(symbol="BTCUSDT", feature_vectors=fvs)
    """

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        self._registry = registry or model_registry

    # ------------------------------------------------------------------
    # Label generation (bootstrapped from rule engine)
    # ------------------------------------------------------------------

    @staticmethod
    def generate_labels(feature_vectors: list[FeatureVector]) -> list[int]:
        """
        Auto-label FeatureVectors using the existing ScoringEngine.

        This bootstraps supervised training from the rule engine's output.
        Labels can be replaced with actual price-outcome labels in future.

        Returns:
            list of integer labels (0=BEARISH, 1=NEUTRAL, 2=BULLISH)
        """
        from app.prediction.services.scoring_engine import ScoringEngine

        labels: list[int] = []
        for fv in feature_vectors:
            direction, _, _, _, _, _ = ScoringEngine.score_features(fv)
            labels.append(DIRECTION_TO_LABEL.get(direction, 1))
        return labels

    # ------------------------------------------------------------------
    # Synthetic data generation (for testing / cold-start)
    # ------------------------------------------------------------------

    @staticmethod
    def generate_synthetic_data(
        n_samples: int = 500,
        symbol: str = "BTCUSDT",
        timeframe: str = "1h",
        seed: int = 42,
    ) -> tuple[list[FeatureVector], list[int]]:
        """
        Generate synthetic FeatureVectors and balanced labels for testing.

        Produces realistic-range values for all 13 features with enough
        variance to train a meaningful classifier.
        """
        from datetime import datetime, timezone

        rng = np.random.default_rng(seed)
        feature_vectors: list[FeatureVector] = []
        labels: list[int] = []

        base_price = 65_000.0

        for i in range(n_samples):
            # Simulate price regime (trend direction)
            regime = rng.choice([0, 1, 2])  # 0=bear, 1=neutral, 2=bull
            regime_bias = (regime - 1) * 0.3  # -0.3, 0, +0.3

            # Generate correlated technical indicators
            rsi = float(np.clip(50.0 + regime_bias * 30 + rng.normal(0, 12), 10, 90))
            macd_val = float(regime_bias * 200 + rng.normal(0, 80))
            macd_sig = float(macd_val * 0.8 + rng.normal(0, 30))
            macd_hist = macd_val - macd_sig

            ema9 = float(base_price * (1 + regime_bias * 0.01 + rng.normal(0, 0.005)))
            ema20 = float(base_price * (1 + regime_bias * 0.008 + rng.normal(0, 0.004)))
            ema50 = float(base_price * (1 + regime_bias * 0.005 + rng.normal(0, 0.003)))
            ema200 = float(base_price * (1 + rng.normal(0, 0.002)))

            atr = float(abs(rng.normal(800, 300)))
            bb_width = float(abs(rng.normal(0.04, 0.02)))
            vwap = float(base_price + rng.normal(0, 200))
            stoch_rsi = float(np.clip(0.5 + regime_bias * 0.4 + rng.normal(0, 0.2), 0, 1))
            obv = float(rng.normal(0, 1e8))

            fv = FeatureVector(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.now(timezone.utc),
                ema_9=ema9,
                ema_20=ema20,
                ema_50=ema50,
                ema_200=ema200,
                rsi_14=rsi,
                macd=macd_val,
                macd_signal=macd_sig,
                macd_hist=macd_hist,
                stoch_rsi=stoch_rsi,
                atr_14=atr,
                bb_upper=None,
                bb_middle=None,
                bb_lower=None,
                bb_width=bb_width,
                vwap=vwap,
                obv=obv,
            )
            feature_vectors.append(fv)
            labels.append(regime)

        return feature_vectors, labels

    # ------------------------------------------------------------------
    # Core training method
    # ------------------------------------------------------------------

    def train(
        self,
        symbol: str,
        feature_vectors: list[FeatureVector],
        labels: Optional[list[int]] = None,
        test_size: float = 0.2,
        min_samples: int = 30,
        cv_folds: int = 5,
    ) -> TrainingResult:
        """
        Train an XGBoost classifier for the given symbol.

        Args:
            symbol: Trading pair (e.g. "BTCUSDT").
            feature_vectors: Training data as FeatureVector objects.
            labels: Integer class labels (0/1/2). If None, auto-labelled via ScoringEngine.
            test_size: Fraction of data held out for evaluation (default 0.2).
            min_samples: Minimum sample count required to proceed.
            cv_folds: Number of cross-validation folds.

        Returns:
            TrainingResult with accuracy, version, and diagnostics.

        Raises:
            ValueError: if fewer than min_samples samples are provided.
        """
        n_samples = len(feature_vectors)
        if n_samples < min_samples:
            raise ValueError(
                f"Insufficient training data for {symbol}: "
                f"{n_samples} samples (minimum {min_samples} required). "
                "Collect more market data or lower --min-samples."
            )

        logger.info(f"Training XGBoost model for {symbol} | samples={n_samples}")

        # 1. Generate labels if not provided
        if labels is None:
            logger.info(f"Auto-labelling {n_samples} samples via ScoringEngine...")
            labels = self.generate_labels(feature_vectors)

        # 2. Extract feature matrix
        X = FeatureExtractor.batch_to_array(feature_vectors)
        y = np.array(labels, dtype=np.int32)

        # Sanity check
        assert X.shape == (n_samples, FeatureExtractor.N_FEATURES), (
            f"Feature matrix shape mismatch: {X.shape}"
        )

        # 3. Train/test split (stratified to preserve class balance)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        logger.info(
            f"Split: train={len(X_train)}, test={len(X_test)} | "
            f"class dist: {dict(zip(*np.unique(y_train, return_counts=True)))}"
        )

        # 4. Build pipeline
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("xgb", XGBClassifier(**XGBOOST_PARAMS)),
        ])

        # 5. Fit
        pipeline.fit(X_train, y_train)

        # 6. Evaluate on held-out test set
        y_pred = pipeline.predict(X_test)
        accuracy = float(accuracy_score(y_test, y_pred))
        report_str = classification_report(
            y_test, y_pred,
            target_names=["BEARISH", "NEUTRAL", "BULLISH"],
            zero_division=0,
        )

        logger.info(f"Test accuracy for {symbol}: {accuracy:.4f}")
        logger.info(f"Classification report:\n{report_str}")

        # 7. Cross-validation
        cv_scores = cross_val_score(
            pipeline, X, y, cv=cv_folds, scoring="accuracy"
        ).tolist()
        logger.info(
            f"Cross-val ({cv_folds}-fold) for {symbol}: "
            f"mean={np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}"
        )

        # 8. Save via registry
        meta = self._registry.save(
            symbol=symbol,
            pipeline=pipeline,
            n_samples=n_samples,
            accuracy=accuracy,
            feature_columns=FEATURE_COLUMNS,
            xgboost_params=XGBOOST_PARAMS,
            extra={
                "cv_mean": float(np.mean(cv_scores)),
                "cv_std": float(np.std(cv_scores)),
                "cv_scores": cv_scores,
                "test_size": test_size,
            },
        )

        return TrainingResult(
            symbol=symbol,
            version=meta.version,
            accuracy=accuracy,
            n_samples=n_samples,
            classification_report_str=report_str,
            cv_scores=cv_scores,
        )

    async def train_from_database(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 2000,
    ) -> TrainingResult:
        """
        Pull historical candles from PostgreSQL, recompute features, and train.

        Falls back to synthetic data if insufficient candles are available.
        """
        from app.database.session import async_session_factory
        from sqlalchemy import select, text

        logger.info(f"Loading historical candles for {symbol} from database...")
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    text(
                        "SELECT open, high, low, close, volume, start_time "
                        "FROM market_candles "
                        "WHERE symbol = :symbol AND timeframe = :tf "
                        "ORDER BY start_time ASC "
                        "LIMIT :limit"
                    ),
                    {"symbol": symbol, "tf": timeframe, "limit": limit},
                )
                rows = result.fetchall()

            if len(rows) < 50:
                logger.warning(
                    f"Only {len(rows)} candles for {symbol}. "
                    "Using synthetic data for training."
                )
                fvs, labels = self.generate_synthetic_data(500, symbol=symbol)
                return self.train(symbol, fvs, labels=labels)

            logger.info(f"Loaded {len(rows)} candles for {symbol}. Building features...")
            feature_vectors = _candles_to_feature_vectors(rows, symbol, timeframe)
            return self.train(symbol, feature_vectors)

        except Exception as e:
            logger.error(f"Database training failed for {symbol}: {e}. Using synthetic data.")
            fvs, labels = self.generate_synthetic_data(500, symbol=symbol)
            return self.train(symbol, fvs, labels=labels)


def _candles_to_feature_vectors(
    rows: list,
    symbol: str,
    timeframe: str,
) -> list[FeatureVector]:
    """
    Convert raw OHLCV database rows into FeatureVectors using in-memory
    indicator calculations. Returns one FeatureVector per candle (with
    enough history to compute all indicators).
    """
    from datetime import datetime, timezone
    import math

    closes = [float(r[3]) for r in rows]
    highs = [float(r[2]) for r in rows]
    lows = [float(r[1]) for r in rows]
    volumes = [float(r[4]) for r in rows]
    timestamps = [r[5] for r in rows]

    def ema(prices: list[float], period: int) -> list[float]:
        result = [None] * len(prices)
        if len(prices) < period:
            return result
        k = 2.0 / (period + 1)
        result[period - 1] = sum(prices[:period]) / period
        for i in range(period, len(prices)):
            result[i] = prices[i] * k + result[i - 1] * (1 - k)
        return result

    def rsi(prices: list[float], period: int = 14) -> list[float | None]:
        result: list[float | None] = [None] * len(prices)
        if len(prices) <= period:
            return result
        gains, losses = [], []
        for i in range(1, period + 1):
            d = prices[i] - prices[i - 1]
            gains.append(max(d, 0))
            losses.append(max(-d, 0))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        for i in range(period, len(prices)):
            d = prices[i] - prices[i - 1]
            avg_gain = (avg_gain * (period - 1) + max(d, 0)) / period
            avg_loss = (avg_loss * (period - 1) + max(-d, 0)) / period
            rs = avg_gain / avg_loss if avg_loss != 0 else 100
            result[i] = 100 - (100 / (1 + rs))
        return result

    ema9 = ema(closes, 9)
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    ema200 = ema(closes, 200)
    rsi14 = rsi(closes, 14)

    # Simple MACD
    macd_line = [
        (a - b) if a is not None and b is not None else None
        for a, b in zip(ema(closes, 12), ema(closes, 26))
    ]
    macd_vals = [v for v in macd_line if v is not None]
    macd_signal_raw = ema(macd_vals, 9) if len(macd_vals) >= 9 else []

    # ATR
    atr_vals: list[float | None] = [None] * len(closes)
    if len(closes) > 14:
        trs = []
        for i in range(1, len(closes)):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            trs.append(tr)
        atr_period = 14
        if len(trs) >= atr_period:
            atr_run = sum(trs[:atr_period]) / atr_period
            atr_vals[atr_period] = atr_run
            for i in range(atr_period + 1, len(closes)):
                atr_run = (atr_run * (atr_period - 1) + trs[i - 1]) / atr_period
                atr_vals[i] = atr_run

    # OBV
    obv_vals = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            obv_vals.append(obv_vals[-1] + volumes[i])
        elif closes[i] < closes[i-1]:
            obv_vals.append(obv_vals[-1] - volumes[i])
        else:
            obv_vals.append(obv_vals[-1])

    feature_vectors: list[FeatureVector] = []
    min_idx = 200  # need at least 200 candles for EMA200

    for i in range(min_idx, len(closes)):
        # Align MACD signal
        macd_raw_idx = i  # approximate alignment
        macd_v = macd_line[i]
        sig_offset = i - (len(macd_vals) - len(macd_signal_raw))
        macd_sig_v = macd_signal_raw[sig_offset] if 0 <= sig_offset < len(macd_signal_raw) else None
        macd_hist_v = (macd_v - macd_sig_v) if macd_v is not None and macd_sig_v is not None else None

        ts = timestamps[i] if isinstance(timestamps[i], datetime) else datetime.now(timezone.utc)

        fv = FeatureVector(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc),
            ema_9=ema9[i],
            ema_20=ema20[i],
            ema_50=ema50[i],
            ema_200=ema200[i],
            rsi_14=rsi14[i],
            macd=macd_v,
            macd_signal=macd_sig_v,
            macd_hist=macd_hist_v,
            stoch_rsi=None,
            atr_14=atr_vals[i],
            bb_upper=None,
            bb_middle=None,
            bb_lower=None,
            bb_width=None,
            vwap=None,
            obv=obv_vals[i],
        )
        feature_vectors.append(fv)

    return feature_vectors


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

async def _cli_train(symbol: str, min_samples: int) -> None:
    trainer = ModelTrainer()
    result = await trainer.train_from_database(symbol=symbol)
    logger.info(f"Training complete: {result}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train XGBoost model for a symbol")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading pair symbol")
    parser.add_argument("--min-samples", type=int, default=30, help="Minimum training samples")
    args = parser.parse_args()

    asyncio.run(_cli_train(args.symbol, args.min_samples))
