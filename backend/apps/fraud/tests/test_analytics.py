"""Tests for the dashboard analytics aggregation."""
from decimal import Decimal

import pytest
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from apps.fraud.models import Alert, RuleHit
from apps.fraud.services.analytics import build_dashboard_stats
from apps.transactions.models import RiskLevel, Transaction, TransactionBatch


@pytest.mark.django_db
def test_dashboard_stats_shape_and_counts(analyst):
    batch = TransactionBatch.objects.create(uploaded_by=analyst, filename="t.csv")

    high = Transaction.objects.create(
        batch=batch, external_id="H", amount=Decimal("15000"), currency="USD",
        timestamp=make_aware(parse_datetime("2026-05-10T11:00:00")),
        country="US", risk_score=80, risk_level=RiskLevel.HIGH,
    )
    Transaction.objects.create(
        batch=batch, external_id="L", amount=Decimal("10"), currency="USD",
        timestamp=make_aware(parse_datetime("2026-05-11T11:00:00")),
        country="US", risk_score=0, risk_level=RiskLevel.LOW,
    )
    alert = Alert.objects.create(transaction=high, risk_score=80)
    RuleHit.objects.create(
        alert=alert, rule_code="HIGH_AMOUNT", rule_label="High amount",
        weight=35, detail="x",
    )

    stats = build_dashboard_stats()

    assert stats["total_transactions"] == 2
    assert stats["total_alerts"] == 1
    assert stats["open_alerts"] == 1
    assert stats["risk_distribution"]["high"] == 1
    assert stats["risk_distribution"]["low"] == 1
    assert stats["top_rules"][0]["rule_code"] == "HIGH_AMOUNT"
    # Only flagged (non-low) transactions appear in the trend.
    assert sum(point["count"] for point in stats["fraud_trend"]) == 1


@pytest.mark.django_db
def test_stats_endpoint(auth_client):
    resp = auth_client.get("/api/fraud/stats/")
    assert resp.status_code == 200
    assert "risk_distribution" in resp.data
    assert "top_rules" in resp.data
