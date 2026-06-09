from django_filters import rest_framework as filters

from .models import Transaction


class TransactionFilter(filters.FilterSet):
    """Query-param filtering for the transaction list endpoint."""

    risk_level = filters.CharFilter(field_name="risk_level", lookup_expr="iexact")
    country = filters.CharFilter(field_name="country", lookup_expr="iexact")
    batch = filters.NumberFilter(field_name="batch_id")
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr="gte")
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr="lte")

    class Meta:
        model = Transaction
        fields = ["risk_level", "country", "batch", "channel"]
