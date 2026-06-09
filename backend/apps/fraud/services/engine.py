"""
Fraud engine.

Scores a batch of transactions using the rule set in `rules.py`, persists the
computed risk score/level back onto each transaction, and creates an `Alert`
(with its `RuleHit` breakdown) for every medium- or high-risk transaction.

The engine is deterministic: given the same transactions and thresholds it
always produces the same scores and alerts.
"""
from dataclasses import dataclass, field

from django.db import transaction as db_transaction

from apps.transactions.models import RiskLevel, Transaction, TransactionBatch

from ..models import Alert, RuleHit
from . import rules


@dataclass
class ScoringResult:
    flagged_count: int = 0
    alert_ids: list[int] = field(default_factory=list)


class FraudEngine:
    def score_batch(
        self,
        batch: TransactionBatch,
        transactions: list[Transaction],
    ) -> ScoringResult:
        ctx = rules.BatchContext(transactions)
        result = ScoringResult()

        new_alerts: list[Alert] = []
        hits_by_txn: dict[str, list[rules.RuleResult]] = {}

        for txn in transactions:
            fired = rules.evaluate(txn, ctx)
            score = rules.score_from_results(fired)
            txn.risk_score = score
            txn.risk_level = rules.level_for_score(score)

            if txn.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH):
                new_alerts.append(
                    Alert(transaction=txn, risk_score=score, status=Alert.Status.OPEN)
                )
                hits_by_txn[str(txn.id)] = fired

        with db_transaction.atomic():
            Transaction.objects.bulk_update(
                transactions, ["risk_score", "risk_level"]
            )

            if new_alerts:
                Alert.objects.bulk_create(new_alerts)

                rule_hits: list[RuleHit] = []
                for alert in new_alerts:
                    for fired in hits_by_txn[str(alert.transaction_id)]:
                        rule_hits.append(
                            RuleHit(
                                alert=alert,
                                rule_code=fired.code,
                                rule_label=fired.label,
                                weight=fired.weight,
                                detail=fired.detail,
                            )
                        )
                RuleHit.objects.bulk_create(rule_hits)

            batch.flagged_count = len(new_alerts)
            batch.save(update_fields=["flagged_count"])

        result.flagged_count = len(new_alerts)
        result.alert_ids = [alert.id for alert in new_alerts]
        return result
