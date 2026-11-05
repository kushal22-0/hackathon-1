"""Detection orchestration: rules, model, scoring, and alert persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.config import DetectionSettings
from app.core.errors import AppError
from app.ml.anomaly import MODEL_READY, AnomalyModelManager
from app.ml.features import (
    TransactionContext,
    build_transaction_contexts,
)
from app.models.alert import (
    Alert,
    DetectionResult,
    DetectionRunRequest,
    DetectionRunResult,
    RuleHit,
)
from app.models.transaction import Transaction
from app.repositories.container import RepositoryContainer
from app.services.detection_rules import combine_rule_scores, evaluate_rules
from app.services.risk_scoring import (
    build_alert_evidence,
    build_explanation,
    combine_scores,
)


class DetectionService:
    def __init__(
        self,
        repositories: RepositoryContainer,
        settings: DetectionSettings,
        model_manager: AnomalyModelManager,
    ) -> None:
        self.repositories = repositories
        self.settings = settings
        self.model_manager = model_manager

    def assess_transaction(self, transaction_id: UUID) -> DetectionResult:
        transaction = self.repositories.transactions.get_by_id(transaction_id)
        if transaction is None:
            raise AppError(
                code="transaction_not_found",
                message="Transaction not found",
                status_code=404,
                details={"transaction_id": str(transaction_id)},
            )
        return self._detect([transaction])[0]

    def scan(self, request: DetectionRunRequest) -> DetectionRunResult:
        targets = self._resolve_targets(request)
        if not targets:
            return DetectionRunResult(
                scanned=0,
                alerts_required=0,
                alerts_created=0,
                alerts_updated=0,
                alert_ids=[],
                model_status="insufficient_data",
                training_rows=0,
            )

        results = self._detect(targets)
        return DetectionRunResult(
            scanned=len(results),
            alerts_required=sum(
                1 for result in results if result.alert_required
            ),
            alerts_created=sum(
                1 for result in results if result.alert_created
            ),
            alerts_updated=sum(
                1 for result in results if result.alert_updated
            ),
            alert_ids=[
                result.alert.id
                for result in results
                if result.alert is not None
            ],
            model_status=results[0].model_status,
            training_rows=results[0].training_rows,
        )

    def _resolve_targets(
        self, request: DetectionRunRequest
    ) -> list[Transaction]:
        if request.transaction_ids is not None:
            transaction_ids = list(dict.fromkeys(request.transaction_ids))
            self._ensure_batch_size(len(transaction_ids))
            if not transaction_ids:
                return []

            transactions = self.repositories.transactions.get_by_ids(
                transaction_ids
            )
            by_id = {transaction.id: transaction for transaction in transactions}
            missing = [
                str(transaction_id)
                for transaction_id in transaction_ids
                if transaction_id not in by_id
            ]
            if missing:
                raise AppError(
                    code="transactions_not_found",
                    message="One or more transactions were not found",
                    status_code=404,
                    details={
                        "missing_transaction_count": len(missing),
                        "missing_transaction_ids": missing,
                    },
                )
            return [by_id[transaction_id] for transaction_id in transaction_ids]

        self._ensure_batch_size(request.limit)
        return self.repositories.transactions.list_recent(request.limit)

    def _ensure_batch_size(self, size: int) -> None:
        if size > self.settings.max_batch_size:
            raise AppError(
                code="batch_too_large",
                message=(
                    "Detection batches are limited to "
                    f"{self.settings.max_batch_size} transactions"
                ),
                status_code=422,
                details={"max_batch_size": self.settings.max_batch_size},
            )

    def _detect(self, targets: list[Transaction]) -> list[DetectionResult]:
        max_target_time = max(
            transaction.timestamp for transaction in targets
        )

        # The model trains on a stable recent population; feature context is
        # bounded to events at or before the newest target.
        training_transactions = (
            self.repositories.transactions.list_recent(
                self.settings.ml_max_training_rows
            )
        )
        history_transactions = self.repositories.transactions.list_window(
            until=max_target_time,
            limit=self.settings.ml_max_training_rows + len(targets),
        )

        union_by_id = {
            transaction.id: transaction
            for transaction in training_transactions
        }
        union_by_id.update(
            {
                transaction.id: transaction
                for transaction in history_transactions
            }
        )
        union_by_id.update(
            {transaction.id: transaction for transaction in targets}
        )
        contexts = build_transaction_contexts(
            list(union_by_id.values()),
            rapid_window_seconds=self.settings.rapid_succession_seconds,
            frequency_window_seconds=(
                self.settings.high_frequency_window_minutes * 60
            ),
        )

        training_contexts = [
            contexts[transaction.id]
            for transaction in training_transactions
            if transaction.id in contexts
        ]
        if (
            len(training_contexts) < self.settings.ml_min_training_rows
            and len(contexts) >= self.settings.ml_min_training_rows
        ):
            training_contexts = list(contexts.values())

        target_contexts = [contexts[target.id] for target in targets]
        evaluation = self.model_manager.evaluate(
            training_contexts, target_contexts
        )
        model_available = evaluation.status == MODEL_READY

        results: list[DetectionResult] = []
        for context in target_contexts:
            hits = evaluate_rules(context, self.settings)
            rule_score = combine_rule_scores(hits)
            ml_score = round(
                evaluation.scores.get(context.transaction.id, 0.0), 2
            )
            risk_score = combine_scores(
                rule_score=rule_score,
                ml_score=ml_score,
                settings=self.settings,
                model_available=model_available,
            )
            alert_required = risk_score >= self.settings.alert_threshold
            explanation = build_explanation(
                risk_score=risk_score,
                rule_hits=hits,
                ml_score=ml_score,
                model_status=evaluation.status,
                training_rows=evaluation.training_rows,
                alert_threshold=self.settings.alert_threshold,
                alert_required=alert_required,
            )
            evidence = build_alert_evidence(
                context,
                rule_hits=hits,
                rule_score=rule_score,
                ml_score=ml_score,
                risk_score=risk_score,
                model_status=evaluation.status,
                training_rows=evaluation.training_rows,
                settings=self.settings,
            )

            alert: Alert | None = None
            alert_created = False
            alert_updated = False
            if alert_required:
                alert, alert_created, alert_updated = self._upsert_alert(
                    context,
                    risk_score=risk_score,
                    ml_score=ml_score,
                    hits=hits,
                    explanation=explanation,
                    evidence=evidence,
                )

            results.append(
                DetectionResult(
                    transaction_id=context.transaction.id,
                    risk_score=risk_score,
                    rule_score=rule_score,
                    ml_score=ml_score,
                    alert_threshold=self.settings.alert_threshold,
                    rule_hits=hits,
                    explanation=explanation,
                    alert_required=alert_required,
                    alert_created=alert_created,
                    alert_updated=alert_updated,
                    alert=alert,
                    model_status=evaluation.status,
                    training_rows=evaluation.training_rows,
                )
            )

        self.repositories.commit()
        return results

    def _upsert_alert(
        self,
        context: TransactionContext,
        *,
        risk_score: float,
        ml_score: float,
        hits: list[RuleHit],
        explanation: str,
        evidence: dict,
    ) -> tuple[Alert, bool, bool]:
        now = datetime.now(UTC)
        existing = self.repositories.alerts.get_active_by_transaction_id(
            context.transaction.id
        )
        if existing is not None:
            updated = existing.model_copy(
                update={
                    "risk_score": risk_score,
                    "rule_hits": hits,
                    "ml_score": ml_score,
                    "explanation": explanation,
                    "evidence": evidence,
                    "updated_at": now,
                }
            )
            self.repositories.alerts.update(updated)
            return updated, False, True

        alert = Alert(
            id=uuid4(),
            transaction_id=context.transaction.id,
            risk_score=risk_score,
            rule_hits=hits,
            ml_score=ml_score,
            explanation=explanation,
            evidence=evidence,
            created_at=now,
            updated_at=now,
        )
        self.repositories.alerts.add(alert)
        return alert, True, False
