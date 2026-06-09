from rest_framework import serializers

from .models import Transaction, TransactionBatch


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "external_id",
            "timestamp",
            "amount",
            "currency",
            "merchant",
            "category",
            "country",
            "channel",
            "card_last4",
            "customer_id",
            "risk_score",
            "risk_level",
        )
        read_only_fields = fields


class TransactionBatchSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.CharField(source="uploaded_by.username", read_only=True)

    class Meta:
        model = TransactionBatch
        fields = (
            "id",
            "filename",
            "row_count",
            "flagged_count",
            "uploaded_by",
            "created_at",
        )
        read_only_fields = fields


class UploadResultSerializer(serializers.Serializer):
    """Response shape returned by the CSV upload endpoint."""

    batch_id = serializers.IntegerField()
    filename = serializers.CharField()
    imported = serializers.IntegerField()
    flagged = serializers.IntegerField()
    alert_ids = serializers.ListField(child=serializers.IntegerField())
