# Python modules
from typing import Any, Optional, Sequence

# Django modules
from django.core.cache import cache
from django.db.models import QuerySet

#  DRF modules
from rest_framework.viewsets import ViewSet
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
)

# Project modules
from apps.blog.pagination import CustomCursorPagination
from .models import Notification
from .serializers import NotificationReadSerializer

# Polling provides a simple logic: client asks a server for some new data every N seconds.
# It does not require constant connection, unlike SSE or WebSockets.
# Disadvantages: notifications may arrive with a delay to N seconds;
# Each client will send a request every N seconds, which could create a large load.
# Polling is good when interval can be long and time delay is fine.
# SSE is better when we want to transfer info from server to client instantly.
# WebSockets are preferrable when we want to create a bi-directional communication.


class NotificationViewSet(ViewSet):
    """Notifications ViewSet."""

    permission_classes = (IsAuthenticated,)
    pagination_class = CustomCursorPagination

    @action(
        methods=("GET",),
        detail=False,
        url_name="notification_count",
        url_path="count",
    )
    def count(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> DRFResponse:
        """Returns count of unread notifications."""

        cache_key: str = f"unread_notif_{request.user.id}"
        data: int = cache.get(cache_key)

        if data:
            return DRFResponse(data={"unread_count": data})

        unread_count: int = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        cache.set(cache_key, unread_count, timeout=10)
        return DRFResponse(
            data={"unread_count": unread_count}, status=HTTP_200_OK
        )

    def list(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> DRFResponse:
        """Returns a list of notifications."""

        queryset: QuerySet[Notification] = Notification.objects.filter(
            recipient=request.user,
        ).select_related("comment", "comment__post", "comment__author")

        paginator: CustomCursorPagination = self.pagination_class()
        page: Optional[Sequence[Any]] = paginator.paginate_queryset(
            queryset=queryset, request=request, view=self
        )
        if page is not None:
            serializer: NotificationReadSerializer = (
                NotificationReadSerializer(
                    page,
                    many=True,
                )
            )
            response = paginator.get_paginated_response(serializer.data)
        else:
            serializer: NotificationReadSerializer = (
                NotificationReadSerializer(
                    queryset,
                    many=True,
                )
            )
            response = DRFResponse(serializer.data, status=HTTP_200_OK)

        return response

    @action(
        methods=("POST",),
        detail=False,
        url_name="notifications_read",
        url_path="read",
    )
    def read(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> DRFResponse:
        """Reads all notifications."""

        queryset: QuerySet[Notification] = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        cache.delete(f"unread_notif_{request.user.id}")
        return DRFResponse(status=HTTP_200_OK)
