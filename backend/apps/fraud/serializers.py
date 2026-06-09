from rest_framework import serializers

from apps.transactions.serializers import TransactionSerializer

from .models import Alert, RuleHit


class RuleHitSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleHit
        fields = ("rule_code", "rule_label", "weight", "detail")


class AlertListSerializer(serializers.ModelSerializer):
    """Compact alert representation for the alert queue."""

    transaction = TransactionSerializer(read_only=True)
    reviewed_by = serializers.CharField(
        source="reviewed_by.username", read_only=True, default=None
    )

    class Meta:
        model = Alert
        fields = (
            "id",
            "status",
            "risk_score",
            "transaction",
            "reviewed_by",
            "reviewed_at",
            "created_at",
        )
        read_only_fields = fields


class AlertDetailSerializer(AlertListSerializer):
    """Full alert: rule hits + AI explanation + review note."""

    rule_hits = RuleHitSerializer(many=True, read_only=True)

    class Meta(AlertListSerializer.Meta):
        fields = AlertListSerializer.Meta.fields + (
            "rule_hits",
            "ai_explanation",
            "ai_explained_at",
            "review_note",
        )
        read_only_fields = fields


class AlertReviewSerializer(serializers.Serializer):
    """Input for confirming or dismissing an alert."""

    status = serializers.ChoiceField(
        choices=[Alert.Status.CONFIRMED, Alert.Status.DISMISSED]
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")
