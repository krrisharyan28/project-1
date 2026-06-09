"""
Thin HTTP client for a local Ollama server.

Wraps Ollama's `/api/generate` endpoint. Configuration (base URL, model,
timeout) comes from settings. There is no offline fallback — the stack requires
Ollama to be running with the configured model pulled.
"""
import requests
from django.conf import settings


class OllamaError(Exception):
    """Raised when the Ollama server is unreachable or returns an error."""


def generate(prompt: str, system: str | None = None) -> str:
    """Send a prompt to Ollama and return the generated text (non-streaming)."""
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    try:
        response = requests.post(
            url, json=payload, timeout=settings.OLLAMA_TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise OllamaError(
            f"Could not reach Ollama at {settings.OLLAMA_BASE_URL}: {exc}"
        ) from exc

    data = response.json()
    text = (data.get("response") or "").strip()
    if not text:
        raise OllamaError("Ollama returned an empty response.")
    return text
