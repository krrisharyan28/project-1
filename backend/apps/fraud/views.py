from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.services.explainer import ExplanationError, explain_alert

from .filters import AlertFilter
from .models import Alert
from .serializers import (
    AlertDetailSerializer,
    AlertListSerializer,
    AlertReviewSerializer,
)
from .services.analytics import build_dashboard_stats

ALERT_QUERYSET = Alert.objects.select_related("transaction", "reviewed_by")


class AlertListView(generics.ListAPIView):
    """GET /api/fraud/alerts/ — paginated, filterable alert queue."""

    serializer_class = AlertListSerializer
    queryset = ALERT_QUERYSET
    filterset_class = AlertFilter
    ordering_fields = ["risk_score", "created_at"]


class AlertDetailView(generics.RetrieveAPIView):
    """GET /api/fraud/alerts/{id}/ — alert with rule hits and AI explanation."""

    serializer_class = AlertDetailSerializer
    queryset = ALERT_QUERYSET.prefetch_related("rule_hits")


class AlertExplainView(APIView):
    """
    POST /api/fraud/alerts/{id}/explain/

    Returns the cached Llama-3 explanation, generating it on first request.
    """

    def post(self, request, pk):
        alert = get_object_or_404(ALERT_QUERYSET.prefetch_related("rule_hits"), pk=pk)
        try:
            explanation = explain_alert(alert)
        except ExplanationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(
            {"id": alert.id, "ai_explanation": explanation},
            status=status.HTTP_200_OK,
        )


class AlertReviewView(APIView):
    """PATCH /api/fraud/alerts/{id}/review/ — confirm or dismiss an alert."""

    def patch(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk)
        serializer = AlertReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert.status = serializer.validated_data["status"]
        alert.review_note = serializer.validated_data["note"]
        alert.reviewed_by = request.user
        alert.reviewed_at = timezone.now()
        alert.save(
            update_fields=["status", "review_note", "reviewed_by", "reviewed_at"]
        )

        return Response(AlertDetailSerializer(alert).data, status=status.HTTP_200_OK)


class StatsView(APIView):
    """GET /api/fraud/stats/ — dashboard KPIs and chart series."""

    def get(self, request):
        return Response(build_dashboard_stats())
