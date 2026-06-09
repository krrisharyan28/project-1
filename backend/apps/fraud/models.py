from django.conf import settings
from django.db import models

from apps.transactions.models import Transaction


class Alert(models.Model):
    """
    Created when a transaction's risk level is medium or high. Carries the
    review workflow state and the cached Llama-3 explanation.
    """

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CONFIRMED = "confirmed_fraud", "Confirmed fraud"
        DISMISSED = "dismissed", "Dismissed"

    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name="alert",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    risk_score = models.PositiveSmallIntegerField()

    ai_explanation = models.TextField(blank=True)
    ai_explained_at = models.DateTimeField(null=True, blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_alerts",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-risk_score", "-created_at"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self) -> str:
        return f"Alert #{self.pk} — {self.get_status_display()} ({self.risk_score})"


class RuleHit(models.Model):
    """A single rule that fired for an alert — the transparency record."""

    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name="rule_hits",
    )
    rule_code = models.CharField(max_length=50)
    rule_label = models.CharField(max_length=120)
    weight = models.PositiveSmallIntegerField()
    detail = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.rule_code} (+{self.weight})"
