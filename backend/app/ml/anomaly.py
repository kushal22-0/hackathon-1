"""IsolationForest training, caching, and percentile scoring."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from uuid import UUID

import numpy as np
from sklearn.ensemble import IsolationForest

from app.core.config import DetectionSettings
from app.ml.features import TransactionContext, feature_vector

logger = logging.getLogger("fraudnet.ml")

MODEL_READY = "ready"
MODEL_INSUFFICIENT_DATA = "insufficient_data"
MODEL_FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ModelEvaluation:
    status: str
    training_rows: int
    scores: dict[UUID, float]


class AnomalyModelManager:
    """Fit one process-wide model and reuse it until the training data changes.

    Raw IsolationForest decision values are not intuitive, so scores are
    expressed as the percentile of a transaction's anomaly score within the
    training population. A score of 95 means the transaction is more anomalous
    than 95% of recent activity.
    """

    def __init__(self, settings: DetectionSettings) -> None:
        self.settings = settings
        self._lock = RLock()
        self._model: IsolationForest | None = None
        self._training_anomaly_scores: np.ndarray | None = None
        self._signature: tuple[int, datetime, datetime, int] | None = None
        self._training_rows = 0

    def evaluate(
        self,
        training: Sequence[TransactionContext],
        targets: Sequence[TransactionContext],
    ) -> ModelEvaluation:
        if len(training) < self.settings.ml_min_training_rows:
            return ModelEvaluation(
                status=MODEL_INSUFFICIENT_DATA,
                training_rows=len(training),
                scores={target.transaction.id: 0.0 for target in targets},
            )

        signature = self._signature_for(training)
        with self._lock:
            if signature != self._signature or self._model is None:
                fitted = self._fit(training)
                if fitted is None:
                    return ModelEvaluation(
                        status=MODEL_FAILED,
                        training_rows=len(training),
                        scores={
                            target.transaction.id: 0.0 for target in targets
                        },
                    )

            assert self._model is not None
            assert self._training_anomaly_scores is not None
            if not targets:
                return ModelEvaluation(
                    status=MODEL_READY,
                    training_rows=self._training_rows,
                    scores={},
                )

            target_matrix = self._matrix(targets)
            target_scores = -self._model.decision_function(target_matrix)
            scores = {
                target.transaction.id: self._percentile(score)
                for target, score in zip(targets, target_scores, strict=True)
            }

        return ModelEvaluation(
            status=MODEL_READY,
            training_rows=self._training_rows,
            scores=scores,
        )

    def _fit(self, training: Sequence[TransactionContext]) -> bool:
        try:
            matrix = self._matrix(training)
            model = IsolationForest(
                n_estimators=self.settings.ml_estimators,
                contamination=self.settings.ml_contamination,
                random_state=self.settings.ml_random_state,
                n_jobs=1,
            )
            model.fit(matrix)
            training_scores = -model.decision_function(matrix)
        except (ValueError, TypeError):
            logger.exception("Unable to fit IsolationForest model")
            self._model = None
            self._training_anomaly_scores = None
            self._signature = None
            self._training_rows = 0
            return False

        self._model = model
        self._training_anomaly_scores = np.sort(training_scores)
        self._signature = self._signature_for(training)
        self._training_rows = len(training)
        return True

    def _percentile(self, anomaly_score: float) -> float:
        assert self._training_anomaly_scores is not None
        values = self._training_anomaly_scores
        left = int(np.searchsorted(values, anomaly_score, side="left"))
        right = int(np.searchsorted(values, anomaly_score, side="right"))
        percentile = ((left + right) / 2.0) / len(values) * 100.0
        return float(min(100.0, max(0.0, percentile)))

    @staticmethod
    def _matrix(contexts: Sequence[TransactionContext]) -> np.ndarray:
        matrix = np.asarray(
            [feature_vector(context) for context in contexts], dtype=float
        )
        return np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)

    @staticmethod
    def _signature_for(
        training: Sequence[TransactionContext],
    ) -> tuple[int, datetime, datetime, int]:
        timestamps = [context.transaction.timestamp for context in training]
        return (
            len(training),
            min(timestamps),
            max(timestamps),
            hash(tuple(context.transaction.id for context in training)),
        )

    @property
    def training_rows(self) -> int:
        return self._training_rows
