from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fraud.services.engine import FraudEngine

from .filters import TransactionFilter
from .models import Transaction, TransactionBatch
from .serializers import (
    TransactionBatchSerializer,
    TransactionSerializer,
    UploadResultSerializer,
)
from .services.csv_importer import CsvImportError, import_file


class TransactionUploadView(APIView):
    """
    POST /api/transactions/upload/ (multipart, field name: `file`)

    Imports a CSV, runs the fraud engine over the batch, and returns a summary.
    """

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.get("file")
        if uploaded is None:
            return Response(
                {"detail": "No file provided. Send a CSV as form field 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = import_file(uploaded, request.user)
        except CsvImportError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        scoring = FraudEngine().score_batch(result.batch, result.transactions)

        payload = {
            "batch_id": result.batch.id,
            "filename": result.batch.filename,
            "imported": result.batch.row_count,
            "flagged": scoring.flagged_count,
            "alert_ids": scoring.alert_ids,
        }
        return Response(
            UploadResultSerializer(payload).data,
            status=status.HTTP_201_CREATED,
        )


class TransactionListView(generics.ListAPIView):
    """GET /api/transactions/ — paginated, filterable, searchable list."""

    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    filterset_class = TransactionFilter
    search_fields = ["external_id", "merchant", "customer_id"]
    ordering_fields = ["timestamp", "amount", "risk_score"]


class TransactionDetailView(generics.RetrieveAPIView):
    """GET /api/transactions/{id}/"""

    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()


class BatchListView(generics.ListAPIView):
    """GET /api/transactions/batches/ — upload history."""

    serializer_class = TransactionBatchSerializer
    queryset = TransactionBatch.objects.all()
