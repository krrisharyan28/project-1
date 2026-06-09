"""
Project-wide DRF exception handling.

Produces a consistent error envelope so the frontend can rely on one shape:

    {
        "error": {
            "status": 400,
            "message": "Human-readable summary",
            "details": { ...field errors or extra context... }
        }
    }
"""
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Wrap DRF's default handler output in a stable error envelope."""
    response = exception_handler(exc, context)
    if response is None:
        # Unhandled (non-DRF) exceptions propagate to Django's 500 handling.
        return None

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
        message = str(detail["detail"])
        details = {}
    else:
        message = "Request could not be processed."
        details = detail

    response.data = {
        "error": {
            "status": response.status_code,
            "message": message,
            "details": details,
        }
    }
    return response
