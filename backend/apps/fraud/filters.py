from django_filters import rest_framework as filters

from .models import Alert


class AlertFilter(filters.FilterSet):
    """Query-param filtering for the alert queue."""

    status = filters.CharFilter(field_name="status", lookup_expr="iexact")
    risk_level = filters.CharFilter(
        field_name="transaction__risk_level", lookup_expr="iexact"
    )
    min_score = filters.NumberFilter(field_name="risk_score", lookup_expr="gte")

    class Meta:
        model = Alert
        fields = ["status", "risk_level", "min_score"]
