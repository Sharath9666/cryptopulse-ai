"""
Tests for FeatureExtractor — feature column ordering, None-filling, and shape guarantees.
"""

import numpy as np
import pytest
from datetime import datetime, timezone

from app.features.models.feature_vector import FeatureVector
from app.ml.features import FeatureExtractor
from app.ml.config import FEATURE_COLUMNS


def _make_complete_fv(**kwargs) -> FeatureVector:
    """Create a fully populated FeatureVector."""
    defaults = dict(
        symbol="BTCUSDT",
        timeframe="1h",
        timestamp=datetime.now(timezone.utc),
        ema_9=65100.0,
        ema_20=64900.0,
        ema_50=63000.0,
        ema_200=58000.0,
        rsi_14=55.0,
        macd=120.0,
        macd_signal=80.0,
        macd_hist=40.0,
        stoch_rsi=0.65,
        atr_14=800.0,
        bb_upper=66000.0,
        bb_middle=65000.0,
        bb_lower=64000.0,
        bb_width=0.031,
        vwap=64800.0,
        obv=5_000_000.0,
    )
    defaults.update(kwargs)
    return FeatureVector(**defaults)


def _make_empty_fv() -> FeatureVector:
    """Create a FeatureVector with all optional fields set to None."""
    return FeatureVector(
        symbol="BTCUSDT",
        timeframe="1h",
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# to_array
# ---------------------------------------------------------------------------

class TestToArray:

    def test_returns_ndarray(self):
        fv = _make_complete_fv()
        result = FeatureExtractor.to_array(fv)
        assert isinstance(result, np.ndarray)

    def test_correct_shape(self):
        fv = _make_complete_fv()
        result = FeatureExtractor.to_array(fv)
        assert result.shape == (FeatureExtractor.N_FEATURES,)

    def test_dtype_is_float64(self):
        fv = _make_complete_fv()
        result = FeatureExtractor.to_array(fv)
        assert result.dtype == np.float64

    def test_correct_n_features_matches_config(self):
        assert FeatureExtractor.N_FEATURES == len(FEATURE_COLUMNS)

    def test_values_in_expected_positions(self):
        fv = _make_complete_fv()
        arr = FeatureExtractor.to_array(fv)
        for i, col in enumerate(FEATURE_COLUMNS):
            expected = getattr(fv, col, None)
            if expected is not None:
                assert arr[i] == pytest.approx(float(expected), rel=1e-6), (
                    f"Mismatch at column {col} (index {i})"
                )

    def test_none_values_filled_with_defaults(self):
        fv = _make_empty_fv()
        arr = FeatureExtractor.to_array(fv)
        # Should not contain NaN
        assert not np.any(np.isnan(arr))
        # RSI default should be 50.0
        rsi_idx = FEATURE_COLUMNS.index("rsi_14")
        assert arr[rsi_idx] == pytest.approx(50.0)
        # stoch_rsi default should be 0.5
        stoch_idx = FEATURE_COLUMNS.index("stoch_rsi")
        assert arr[stoch_idx] == pytest.approx(0.5)

    def test_no_nan_for_complete_vector(self):
        fv = _make_complete_fv()
        arr = FeatureExtractor.to_array(fv)
        assert not np.any(np.isnan(arr))

    def test_column_order_is_stable(self):
        """Calling to_array twice must return the same order."""
        fv = _make_complete_fv()
        arr1 = FeatureExtractor.to_array(fv)
        arr2 = FeatureExtractor.to_array(fv)
        np.testing.assert_array_equal(arr1, arr2)


# ---------------------------------------------------------------------------
# to_2d_array
# ---------------------------------------------------------------------------

class TestTo2dArray:

    def test_shape_is_1_by_n(self):
        fv = _make_complete_fv()
        result = FeatureExtractor.to_2d_array(fv)
        assert result.shape == (1, FeatureExtractor.N_FEATURES)

    def test_values_match_1d(self):
        fv = _make_complete_fv()
        arr1d = FeatureExtractor.to_array(fv)
        arr2d = FeatureExtractor.to_2d_array(fv)
        np.testing.assert_array_equal(arr1d, arr2d[0])


# ---------------------------------------------------------------------------
# batch_to_array
# ---------------------------------------------------------------------------

class TestBatchToArray:

    def test_empty_list_returns_empty_matrix(self):
        result = FeatureExtractor.batch_to_array([])
        assert result.shape == (0, FeatureExtractor.N_FEATURES)

    def test_n_rows_equals_n_vectors(self):
        fvs = [_make_complete_fv() for _ in range(10)]
        result = FeatureExtractor.batch_to_array(fvs)
        assert result.shape == (10, FeatureExtractor.N_FEATURES)

    def test_each_row_matches_single_extraction(self):
        fv = _make_complete_fv()
        batch = FeatureExtractor.batch_to_array([fv, fv])
        single = FeatureExtractor.to_array(fv)
        np.testing.assert_array_equal(batch[0], single)
        np.testing.assert_array_equal(batch[1], single)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

class TestValidate:

    def test_complete_vector_is_valid(self):
        fv = _make_complete_fv()
        is_complete, missing = FeatureExtractor.validate(fv)
        assert is_complete
        assert missing == []

    def test_empty_vector_reports_all_missing(self):
        fv = _make_empty_fv()
        is_complete, missing = FeatureExtractor.validate(fv)
        assert not is_complete
        assert len(missing) == len(FEATURE_COLUMNS)

    def test_partial_vector_reports_only_missing(self):
        fv = _make_complete_fv(rsi_14=None, macd=None)
        is_complete, missing = FeatureExtractor.validate(fv)
        assert not is_complete
        assert "rsi_14" in missing
        assert "macd" in missing
        assert "ema_9" not in missing
