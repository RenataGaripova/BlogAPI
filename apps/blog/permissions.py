# DRF modules
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request as DRFRequest
from rest_framework.views import APIView
from typing import Any


class IsAuthorOrReadOnly(BasePermission):
    """Only author has access to his content."""

    def has_object_permission(
        self,
        request: DRFRequest,
        view: APIView,
        obj: Any,
    ):
        """Check if user has permission to access the object."""
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.author
