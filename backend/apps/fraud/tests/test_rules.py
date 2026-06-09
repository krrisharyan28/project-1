"""Unit tests for the deterministic fraud rules (no database required)."""
from decimal import Decimal

from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware

from apps.transactions.models import RiskLevel, Transaction
from apps.fraud.services import rules


def mk(ts, amount, *, category="retail", country="US", card="1111", customer="C1"):
    return Transaction(
        external_id="x",
        timestamp=make_aware(parse_datetime(ts)),
        amount=Decimal(str(amount)),
        currency="USD",
        category=category,
        country=country,
        channel="online",
        card_last4=card,
        customer_id=customer,
    )


def ctx_for(txns):
    return rules.BatchContext(txns)


def test_high_amount_fires_above_threshold():
    txn = mk("2026-05-01T12:00:00", 15000)
    result = rules.rule_high_amount(txn, ctx_for([txn]))
    assert result is not None
    assert result.code == "HIGH_AMOUNT"
    assert result.weight == 35


def test_high_amount_silent_below_threshold():
    txn = mk("2026-05-01T12:00:00", 9999)
    assert rules.rule_high_amount(txn, ctx_for([txn])) is None


def test_odd_hour_fires_in_early_morning():
    txn = mk("2026-05-01T02:30:00", 50)
    assert rules.rule_odd_hour(txn, ctx_for([txn])).code == "ODD_HOUR"


def test_odd_hour_silent_in_daytime():
    txn = mk("2026-05-01T14:30:00", 50)
    assert rules.rule_odd_hour(txn, ctx_for([txn])) is None


def test_velocity_fires_on_third_in_window():
    txns = [
        mk("2026-05-05T02:01:00", 80),
        mk("2026-05-05T02:05:00", 95),
        mk("2026-05-05T02:09:00", 60),
    ]
    ctx = ctx_for(txns)
    # First two are within the window count < 3; the third completes the burst.
    assert rules.rule_velocity(txns[0], ctx) is None
    assert rules.rule_velocity(txns[2], ctx).code == "VELOCITY"


def test_country_mismatch_uses_home_country():
    txns = [
        mk("2026-05-01T10:00:00", 50, country="US"),
        mk("2026-05-02T10:00:00", 50, country="US"),
        mk("2026-05-03T10:00:00", 50, country="NG"),
    ]
    ctx = ctx_for(txns)
    assert rules.rule_country_mismatch(txns[0], ctx) is None
    hit = rules.rule_country_mismatch(txns[2], ctx)
    assert hit.code == "COUNTRY_MISMATCH"


def test_high_risk_category():
    txn = mk("2026-05-01T12:00:00", 50, category="crypto")
    assert rules.rule_high_risk_category(txn, ctx_for([txn])).code == "HIGH_RISK_MCC"


def test_round_amount():
    assert rules.rule_round_amount(mk("2026-05-01T12:00:00", 5000), ctx_for([])).code == "ROUND_AMOUNT"
    assert rules.rule_round_amount(mk("2026-05-01T12:00:00", 5050), ctx_for([])) is None
    # Below 1000 is not considered a "large" round amount.
    assert rules.rule_round_amount(mk("2026-05-01T12:00:00", 500), ctx_for([])) is None


def test_new_card_burst():
    txns = [
        mk("2026-05-01T12:00:00", 30, card="1010"),
        mk("2026-05-02T12:00:00", 2500, card="5566"),  # first use of 5566, > 2000
    ]
    ctx = ctx_for(txns)
    assert rules.rule_new_card_burst(txns[1], ctx).code == "NEW_CARD_BURST"


def test_score_is_capped_at_100():
    results = [rules.RuleResult("A", "a", 60, ""), rules.RuleResult("B", "b", 60, "")]
    assert rules.score_from_results(results) == 100


def test_level_thresholds():
    assert rules.level_for_score(0) == RiskLevel.LOW
    assert rules.level_for_score(39) == RiskLevel.LOW
    assert rules.level_for_score(40) == RiskLevel.MEDIUM
    assert rules.level_for_score(69) == RiskLevel.MEDIUM
    assert rules.level_for_score(70) == RiskLevel.HIGH


def test_evaluate_combines_multiple_rules():
    # High amount (35) + crypto (20) + round (10) on a clean-hour txn.
    txn = mk("2026-05-01T12:00:00", 12000, category="crypto")
    fired = rules.evaluate(txn, ctx_for([txn]))
    codes = {r.code for r in fired}
    assert {"HIGH_AMOUNT", "HIGH_RISK_MCC"}.issubset(codes)
