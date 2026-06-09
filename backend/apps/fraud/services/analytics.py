"""
Dashboard analytics service.

Aggregates transactions and alerts into the KPI + chart series consumed by the
React dashboard. Kept in the service layer so the view stays a thin pass-through.
"""
from django.db.models import Count
from django.db.models.functions import TruncDate

from apps.transactions.models import RiskLevel, Transaction

from ..models import Alert, RuleHit


def build_dashboard_stats() -> dict:
    total_transactions = Transaction.objects.count()

    level_counts = {
        row["risk_level"]: row["n"]
        for row in Transaction.objects.values("risk_level").annotate(n=Count("id"))
    }
    risk_distribution = {
        "low": level_counts.get(RiskLevel.LOW, 0),
        "medium": level_counts.get(RiskLevel.MEDIUM, 0),
        "high": level_counts.get(RiskLevel.HIGH, 0),
    }

    alert_status_counts = {
        row["status"]: row["n"]
        for row in Alert.objects.values("status").annotate(n=Count("id"))
    }

    # Flagged transactions per day (for the trend line).
    fraud_trend = [
        {"date": row["day"].isoformat(), "count": row["n"]}
        for row in (
            Transaction.objects.exclude(risk_level=RiskLevel.LOW)
            .annotate(day=TruncDate("timestamp"))
            .values("day")
            .annotate(n=Count("id"))
            .order_by("day")
        )
    ]

    # Top countries by flagged transaction volume.
    top_countries = [
        {"country": row["country"] or "—", "count": row["n"]}
        for row in (
            Transaction.objects.exclude(risk_level=RiskLevel.LOW)
            .exclude(country="")
            .values("country")
            .annotate(n=Count("id"))
            .order_by("-n")[:5]
        )
    ]

    # Most frequently fired rules.
    top_rules = [
        {"rule_code": row["rule_code"], "label": row["rule_label"], "count": row["n"]}
        for row in (
            RuleHit.objects.values("rule_code", "rule_label")
            .annotate(n=Count("id"))
            .order_by("-n")[:5]
        )
    ]

    return {
        "total_transactions": total_transactions,
        "total_alerts": Alert.objects.count(),
        "open_alerts": alert_status_counts.get(Alert.Status.OPEN, 0),
        "confirmed_fraud": alert_status_counts.get(Alert.Status.CONFIRMED, 0),
        "dismissed": alert_status_counts.get(Alert.Status.DISMISSED, 0),
        "risk_distribution": risk_distribution,
        "fraud_trend": fraud_trend,
        "top_countries": top_countries,
        "top_rules": top_rules,
    }
