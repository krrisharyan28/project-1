from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.ollama_client import OllamaError, generate


class AiPingView(APIView):
    """
    GET /api/ai/ping/ — quick reachability check for the Ollama model.
    Useful for verifying the AI dependency from the dashboard.
    """

    def get(self, request):
        try:
            generate("Reply with the single word: ok")
        except OllamaError as exc:
            return Response(
                {"model": settings.OLLAMA_MODEL, "available": False, "detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"model": settings.OLLAMA_MODEL, "available": True})
