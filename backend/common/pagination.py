"""Shared pagination used across all list endpoints."""
from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Page-number pagination with a client-tunable (but bounded) page size."""

    page_size_query_param = "page_size"
    max_page_size = 100
