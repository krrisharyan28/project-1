from django.urls import path

from .views import (
    AlertDetailView,
    AlertExplainView,
    AlertListView,
    AlertReviewView,
    StatsView,
)

urlpatterns = [
    path("alerts/", AlertListView.as_view(), name="alert-list"),
    path("alerts/<int:pk>/", AlertDetailView.as_view(), name="alert-detail"),
    path("alerts/<int:pk>/explain/", AlertExplainView.as_view(), name="alert-explain"),
    path("alerts/<int:pk>/review/", AlertReviewView.as_view(), name="alert-review"),
    path("stats/", StatsView.as_view(), name="fraud-stats"),
]
