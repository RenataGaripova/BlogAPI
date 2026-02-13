# DRF modules
from rest_framework.pagination import CursorPagination


class CustomCursorPagination(CursorPagination):
    """Customized cursor pagination."""

    ordering = "-created_at"
    page_size = 10
