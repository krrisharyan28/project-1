"""
Fraud detection rules.

Each rule is a small, pure function that inspects one transaction (with some
precomputed batch context) and returns a `RuleResult` when it fires, or `None`.
Rules are deterministic and independently unit-testable — the score is simply
the sum of the weights of the rules that fired, capped at 100.

Thresholds come from `settings.FRAUD` so they can be tuned via environment
variables without changing code.
"""
from __future__ import annotations

import bisect
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.conf import settings

from apps.transactions.models import RiskLevel, Transaction

# Merchant categories considered inherently higher-risk for card fraud.
HIGH_RISK_CATEGORIES = {
    "crypto",
    "gambling",
    "gift_card",
    "wire",
    "money_transfer",
}

SCORE_CAP = 100


@dataclass(frozen=True)
class RuleResult:
    code: str
    label: str
    weight: int
    detail: str


class BatchContext:
    """
    Precomputed, per-customer context shared by the cross-row rules
    (velocity, country mismatch, new-card burst). Built once per batch.
    """

    def __init__(self, transactions: list[Transaction]):
        self._home_country: dict[str, str] = {}
        self._customer_timestamps: dict[str, list] = defaultdict(list)
        self._first_card_ts: dict[tuple[str, str], object] = {}

        country_counts: dict[str, Counter] = defaultdict(Counter)
        for txn in transactions:
            cust = txn.customer_id
            if not cust:
                continue
            if txn.country:
                country_counts[cust][txn.country] += 1
            self._customer_timestamps[cust].append(txn.timestamp)

            if txn.card_last4:
                key = (cust, txn.card_last4)
                seen = self._first_card_ts.get(key)
                if seen is None or txn.timestamp < seen:
                    self._first_card_ts[key] = txn.timestamp

        for cust, counts in country_counts.items():
            self._home_country[cust] = counts.most_common(1)[0][0]
        for cust in self._customer_timestamps:
            self._customer_timestamps[cust].sort()

    def home_country(self, customer_id: str) -> str | None:
        return self._home_country.get(customer_id)

    def velocity_count(self, customer_id: str, ts, window_minutes: int) -> int:
        """Number of this customer's transactions within the preceding window."""
        stamps = self._customer_timestamps.get(customer_id)
        if not stamps:
            return 0
        start = ts - timedelta(minutes=window_minutes)
        lo = bisect.bisect_left(stamps, start)
        hi = bisect.bisect_right(stamps, ts)
        return hi - lo

    def is_first_card_use(self, customer_id: str, card_last4: str, ts) -> bool:
        first = self._first_card_ts.get((customer_id, card_last4))
        return first is not None and ts == first


# --------------------------------------------------------------------------- #
# Individual rules
# --------------------------------------------------------------------------- #
def rule_high_amount(txn: Transaction, ctx: BatchContext) -> RuleResult | None:
    threshold = settings.FRAUD["HIGH_AMOUNT_THRESHOLD"]
    if txn.amount > threshold:
        return RuleResult(
            "HIGH_AMOUNT",
            "Unusually high amount",
            35,
            f"{txn.amount} {txn.currency} exceeds {threshold} threshold",
        )
    return None


def rule_odd_hour(txn: Transaction, ctx: BatchContext) -> RuleResult | None:
    hour = txn.timestamp.hour
    if 0 <= hour <= 5:
        return RuleResult(
            "ODD_HOUR",
            "Transaction at odd hour",
            15,
            f"Occurred at {txn.timestamp.strftime('%H:%M')} UTC",
        )
    return None


def rule_velocity(txn: Transaction, ctx: BatchContext) -> RuleResult | None:
    count = settings.FRAUD["VELOCITY_COUNT"]
    window = settings.FRAUD["VELOCITY_WINDOW_MINUTES"]
    hits = ctx.velocity_count(txn.customer_id, txn.timestamp, window)
    if hits >= count:
        return RuleResult(
            "VELOCITY",
            "Rapid repeat spending",
            25,
            f"{hits} transactions within {window} minutes",
        )
    return None


def rule_country_mismatch(txn: Transaction, ctx: BatchContext) -> RuleResult | None:
    home = ctx.home_country(txn.customer_id)
    if home and txn.country and txn.country != home:
        return RuleResult(
            "COUNTRY_MISMATCH",
            "Foreign / unexpected country",
            20,
            f"Country {txn.country} differs from usual {home}",
        )
    return None


def rule_high_risk_category(txn: Transaction, ctx: BatchContext) -> RuleResult | None:
    if txn.category in HIGH_RISK_CATEGORIES:
        return RuleResult(
            "HIGH_RISK_MCC",
            "High-risk merchant category",
            20,
            f"Category '{txn.category}' is high-risk",
        )
    return None


def rule_round_amount(txn: Transaction, ctx: BatchContext) -> RuleResult | None:
    if txn.amount >= 1000 and txn.amount % Decimal(1000) == 0:
        return RuleResult(
            "ROUND_AMOUNT",
            "Suspicious round amount",
            10,
            f"Amount {txn.amount} is an exact multiple of 1000",
        )
    return None


def rule_new_card_burst(txn: Transaction, ctx: BatchContext) -> RuleResult | None:
    threshold = settings.FRAUD["NEW_CARD_AMOUNT_THRESHOLD"]
    if (
        txn.card_last4
        and txn.customer_id
        and ctx.is_first_card_use(txn.customer_id, txn.card_last4, txn.timestamp)
        and txn.amount > threshold
    ):
        return RuleResult(
            "NEW_CARD_BURST",
            "New card, immediate large spend",
            15,
            f"First use of card ••{txn.card_last4} for {txn.amount} {txn.currency}",
        )
    return None


# Registry of all active rules, evaluated in order.
RULES = (
    rule_high_amount,
    rule_odd_hour,
    rule_velocity,
    rule_country_mismatch,
    rule_high_risk_category,
    rule_round_amount,
    rule_new_card_burst,
)


def evaluate(txn: Transaction, ctx: BatchContext) -> list[RuleResult]:
    """Run every rule against a transaction and return those that fired."""
    return [result for rule in RULES if (result := rule(txn, ctx)) is not None]


def score_from_results(results: list[RuleResult]) -> int:
    """Sum rule weights, capped at the maximum score."""
    return min(sum(r.weight for r in results), SCORE_CAP)


def level_for_score(score: int) -> str:
    """Map a 0–100 score to a risk level. Alerts are created for medium/high."""
    if score >= 70:
        return RiskLevel.HIGH
    if score >= 40:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
