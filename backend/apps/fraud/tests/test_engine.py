"""Integration tests for the fraud engine scoring a persisted batch."""
from decimal import Decimal

import pytest
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from apps.fraud.models import Alert, RuleHit
from apps.fraud.services.engine import FraudEngine
from apps.transactions.models import RiskLevel, Transaction, TransactionBatch


def _txn(batch, ts, amount, **kwargs):
    return Transaction.objects.create(
        batch=batch,
        external_id=kwargs.get("external_id", "x"),
        timestamp=make_aware(parse_datetime(ts)),
        amount=Decimal(str(amount)),
        currency="USD",
        category=kwargs.get("category", "retail"),
        country=kwargs.get("country", "US"),
        channel="online",
        card_last4=kwargs.get("card", "1111"),
        customer_id=kwargs.get("customer", "C1"),
    )


@pytest.mark.django_db
def test_score_batch_creates_alerts_and_rule_hits(analyst):
    batch = TransactionBatch.objects.create(uploaded_by=analyst, filename="t.csv")
    txns = [
        _txn(batch, "2026-05-10T11:00:00", 15000),                 # high + round -> medium
        _txn(batch, "2026-05-04T16:30:00", 12400, category="crypto"),  # high + mcc -> medium
        _txn(batch, "2026-05-01T13:00:00", 42),                    # clean -> low
    ]

    result = FraudEngine().score_batch(batch, txns)

    assert result.flagged_count == 2
    assert Alert.objects.count() == 2
    assert RuleHit.objects.count() >= 4  # at least 2 rules per flagged txn

    batch.refresh_from_db()
    assert batch.flagged_count == 2

    clean = Transaction.objects.get(pk=txns[2].pk)
    assert clean.risk_level == RiskLevel.LOW
    assert clean.risk_score == 0


@pytest.mark.django_db
def test_low_risk_transactions_do_not_create_alerts(analyst):
    batch = TransactionBatch.objects.create(uploaded_by=analyst, filename="t.csv")
    txns = [_txn(batch, "2026-05-01T13:00:00", 20 + i) for i in range(3)]

    result = FraudEngine().score_batch(batch, txns)

    assert result.flagged_count == 0
    assert Alert.objects.count() == 0


@pytest.mark.django_db
def test_engine_is_deterministic(analyst):
    """Scoring the same data twice yields identical scores."""
    def run():
        batch = TransactionBatch.objects.create(uploaded_by=analyst, filename="t.csv")
        txns = [
            _txn(batch, "2026-05-10T11:00:00", 15000, external_id="a"),
            _txn(batch, "2026-05-08T23:45:00", 500, category="gambling", country="NG"),
        ]
        FraudEngine().score_batch(batch, txns)
        return sorted(t.risk_score for t in txns)

    assert run() == run()
