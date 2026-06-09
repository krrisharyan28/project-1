from django.urls import path

from .views import (
    BatchListView,
    TransactionDetailView,
    TransactionListView,
    TransactionUploadView,
)

urlpatterns = [
    path("upload/", TransactionUploadView.as_view(), name="transaction-upload"),
    path("batches/", BatchListView.as_view(), name="batch-list"),
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("<uuid:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
]
