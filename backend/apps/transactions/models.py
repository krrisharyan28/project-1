import uuid

from django.conf import settings
from django.db import models


class RiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class TransactionBatch(models.Model):
    """One uploaded CSV file and a summary of what it produced."""

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="batches",
    )
    filename = models.CharField(max_length=255)
    row_count = models.PositiveIntegerField(default=0)
    flagged_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.filename} ({self.row_count} rows)"


class Transaction(models.Model):
    """A single financial transaction parsed from a CSV row, plus its score."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        TransactionBatch,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    external_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    merchant = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, blank=True)  # ISO-2
    channel = models.CharField(max_length=20, blank=True)  # online | pos | atm
    card_last4 = models.CharField(max_length=4, blank=True)
    customer_id = models.CharField(max_length=100, blank=True)

    risk_score = models.PositiveSmallIntegerField(default=0)
    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        default=RiskLevel.LOW,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["risk_level"]),
            models.Index(fields=["customer_id"]),
            models.Index(fields=["country"]),
        ]

    def __str__(self) -> str:
        return f"{self.external_id} — {self.amount} {self.currency}"
