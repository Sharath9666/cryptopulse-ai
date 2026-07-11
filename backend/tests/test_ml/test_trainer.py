"""
Tests for ModelTrainer — synthetic data training, label generation, and model save/load.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.ml.trainer import ModelTrainer
from app.ml.model import ModelRegistry
from app.ml.features import FeatureExtractor
from app.ml.config import DIRECTION_TO_LABEL


class TestLabelGeneration:

    def test_labels_are_valid_integers(self):
        trainer = ModelTrainer()
        fvs, _ = ModelTrainer.generate_synthetic_data(n_samples=50, seed=0)
        labels = trainer.generate_labels(fvs)
        assert len(labels) == 50
        assert all(l in (0, 1, 2) for l in labels)

    def test_labels_cover_multiple_classes(self):
        """A diverse set of feature vectors should produce at least 2 distinct labels."""
        trainer = ModelTrainer()
        fvs, _ = ModelTrainer.generate_synthetic_data(n_samples=200, seed=1)
        labels = trainer.generate_labels(fvs)
        unique_labels = set(labels)
        assert len(unique_labels) >= 2, (
            f"Expected ≥2 distinct labels, got {unique_labels}"
        )


class TestSyntheticData:

    def test_generate_returns_correct_count(self):
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=100)
        assert len(fvs) == 100
        assert len(labels) == 100

    def test_labels_are_in_valid_range(self):
        _, labels = ModelTrainer.generate_synthetic_data(n_samples=100)
        assert all(l in (0, 1, 2) for l in labels)

    def test_labels_are_balanced_roughly(self):
        _, labels = ModelTrainer.generate_synthetic_data(n_samples=300, seed=42)
        counts = {l: labels.count(l) for l in (0, 1, 2)}
        # Each class should appear at least 10% of the time
        for cls, cnt in counts.items():
            assert cnt >= 20, f"Class {cls} underrepresented: {cnt}"

    def test_feature_vectors_are_extractable(self):
        fvs, _ = ModelTrainer.generate_synthetic_data(n_samples=50)
        X = FeatureExtractor.batch_to_array(fvs)
        assert X.shape == (50, FeatureExtractor.N_FEATURES)
        assert not np.any(np.isnan(X))


class TestTrainWithSyntheticData:

    def test_train_completes_without_error(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=200, seed=42)
        result = trainer.train("TESTUSDT", fvs, labels=labels)
        assert result is not None

    def test_accuracy_above_chance(self, tmp_path):
        """
        XGBoost on correlated synthetic data should beat random guessing (33%)
        by a meaningful margin.
        """
        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=500, seed=42)
        result = trainer.train("TESTUSDT", fvs, labels=labels)
        assert result.accuracy > 0.45, (
            f"Accuracy {result.accuracy:.4f} too low — expected > 0.45"
        )

    def test_model_version_is_v1_for_first_training(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=200, seed=10)
        result = trainer.train("ETHUSDT", fvs, labels=labels)
        assert result.version == "v1"

    def test_second_training_increments_version(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=200, seed=10)
        trainer.train("BTCUSDT", fvs, labels=labels)
        result2 = trainer.train("BTCUSDT", fvs, labels=labels)
        assert result2.version == "v2"

    def test_n_samples_matches_input(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=150, seed=7)
        result = trainer.train("SOLUSDT", fvs, labels=labels)
        assert result.n_samples == 150

    def test_cv_scores_are_reasonable(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=300, seed=42)
        result = trainer.train("BTCUSDT", fvs, labels=labels, cv_folds=3)
        assert len(result.cv_scores) == 3
        assert all(0.0 <= s <= 1.0 for s in result.cv_scores)

    def test_raises_on_insufficient_samples(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=10)
        with pytest.raises(ValueError, match="Insufficient training data"):
            trainer.train("BTCUSDT", fvs, labels=labels, min_samples=50)


class TestModelPersistence:

    def test_saved_model_is_loadable(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=200, seed=42)
        result = trainer.train("DOGEUSDT", fvs, labels=labels)

        # Load it back
        pipeline, meta = registry.load("DOGEUSDT")
        assert pipeline is not None
        assert meta.version == result.version
        assert meta.symbol == "DOGEUSDT"

    def test_loaded_pipeline_can_predict(self, tmp_path):
        from app.features.models.feature_vector import FeatureVector
        from datetime import datetime, timezone

        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=200, seed=42)
        trainer.train("XRPUSDT", fvs, labels=labels)

        pipeline, _ = registry.load("XRPUSDT")
        X = FeatureExtractor.to_2d_array(fvs[0])
        probs = pipeline.predict_proba(X)
        assert probs.shape == (1, 3)
        assert abs(sum(probs[0]) - 1.0) < 1e-5

    def test_registry_lists_correct_symbol(self, tmp_path):
        registry = ModelRegistry(models_dir=tmp_path)
        trainer = ModelTrainer(registry=registry)
        fvs, labels = ModelTrainer.generate_synthetic_data(n_samples=200)
        trainer.train("SOLUSDT", fvs, labels=labels)

        assert registry.has_model("SOLUSDT")
        assert not registry.has_model("BTCUSDT")
        assert "SOLUSDT" in registry.available_symbols()
