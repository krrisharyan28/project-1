from django.urls import path

from .views import AiPingView

urlpatterns = [
    path("ping/", AiPingView.as_view(), name="ai-ping"),
]
