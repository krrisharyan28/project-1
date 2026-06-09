"""Tests for the alert queue, review workflow, and AI explanation endpoint."""
from decimal import Decimal

import pytest
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from apps.fraud.models import Alert, RuleHit
from apps.transactions.models import RiskLevel, Transaction, TransactionBatch


@pytest.fixture
def alert(analyst):
    batch = TransactionBatch.objects.create(uploaded_by=analyst, filename="t.csv")
    txn = Transaction.objects.create(
        batch=batch,
        external_id="TX1",
        timestamp=make_aware(parse_datetime("2026-05-10T11:00:00")),
        amount=Decimal("15000"),
        currency="USD",
        merchant="Rolex",
        category="jewelry",
        country="US",
        channel="pos",
        card_last4="4821",
        customer_id="C1",
        risk_score=45,
        risk_level=RiskLevel.MEDIUM,
    )
    a = Alert.objects.create(transaction=txn, risk_score=45)
    RuleHit.objects.create(
        alert=a, rule_code="HIGH_AMOUNT", rule_label="Unusually high amount",
        weight=35, detail="15000 USD exceeds 10000 threshold",
    )
    return a


@pytest.mark.django_db
def test_list_alerts(auth_client, alert):
    resp = auth_client.get("/api/fraud/alerts/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["risk_score"] == 45


@pytest.mark.django_db
def test_alert_detail_includes_rule_hits(auth_client, alert):
    resp = auth_client.get(f"/api/fraud/alerts/{alert.id}/")
    assert resp.status_code == 200
    assert resp.data["rule_hits"][0]["rule_code"] == "HIGH_AMOUNT"


@pytest.mark.django_db
def test_review_confirms_fraud(auth_client, alert, analyst):
    resp = auth_client.patch(
        f"/api/fraud/alerts/{alert.id}/review/",
        {"status": "confirmed_fraud", "note": "Card reported stolen"},
        format="json",
    )
    assert resp.status_code == 200
    alert.refresh_from_db()
    assert alert.status == Alert.Status.CONFIRMED
    assert alert.review_note == "Card reported stolen"
    assert alert.reviewed_by == analyst
    assert alert.reviewed_at is not None


@pytest.mark.django_db
def test_review_rejects_invalid_status(auth_client, alert):
    resp = auth_client.patch(
        f"/api/fraud/alerts/{alert.id}/review/",
        {"status": "not_a_status"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_explain_generates_and_caches(auth_client, alert, monkeypatch):
    calls = {"n": 0}

    def fake_generate(prompt, system=None):
        calls["n"] += 1
        return "This transaction is suspicious because the amount is very high."

    # Patch the symbol used inside the explainer service.
    monkeypatch.setattr(
        "apps.ai.services.explainer.generate", fake_generate
    )

    resp = auth_client.post(f"/api/fraud/alerts/{alert.id}/explain/")
    assert resp.status_code == 200
    assert "suspicious" in resp.data["ai_explanation"]

    alert.refresh_from_db()
    assert alert.ai_explanation
    assert alert.ai_explained_at is not None

    # Second call should return the cached value without calling the model again.
    auth_client.post(f"/api/fraud/alerts/{alert.id}/explain/")
    assert calls["n"] == 1


@pytest.mark.django_db
def test_explain_handles_ollama_failure(auth_client, alert, monkeypatch):
    from apps.ai.services.ollama_client import OllamaError

    def boom(prompt, system=None):
        raise OllamaError("Ollama unreachable")

    monkeypatch.setattr("apps.ai.services.explainer.generate", boom)

    resp = auth_client.post(f"/api/fraud/alerts/{alert.id}/explain/")
    assert resp.status_code == 502
