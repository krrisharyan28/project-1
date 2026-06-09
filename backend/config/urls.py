"""Root URL configuration. App routers are mounted under /api/."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/transactions/", include("apps.transactions.urls")),
    path("api/fraud/", include("apps.fraud.urls")),
    path("api/ai/", include("apps.ai.urls")),
    path("api/", include("apps.core.urls")),  # health, etc.
]
