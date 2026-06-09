from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.services.ollama_client import OllamaError, generate


class HealthView(APIView):
    """
    GET /api/health/ — liveness probe reporting database and Ollama status.
    Open endpoint; returns 200 if the database is reachable.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:  # pragma: no cover - defensive
            db_ok = False

        ollama_ok = True
        try:
            generate("ok")
        except OllamaError:
            ollama_ok = False

        payload = {
            "status": "ok" if db_ok else "degraded",
            "database": db_ok,
            "ollama": ollama_ok,
            "model": settings.OLLAMA_MODEL,
        }
        code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=code)
