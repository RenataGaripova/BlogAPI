# Python modules
from typing import Type

# DRF modules
from rest_framework.serializers import ModelSerializer


# Project modules
from apps.blog.serializers import CommentSerializer
from .models import Notification


class NotificationBaseSerializer(ModelSerializer):
    """Notification serializer."""

    class Meta:
        """Metadata."""

        model: Type[Notification] = Notification
        fields: tuple[str, ...] = (
            "id",
            "recipient",
            "comment",
            "is_read",
            "created_at",
        )


class NotificationReadSerializer(NotificationBaseSerializer):
    """Notification read serializer."""

    comment: CommentSerializer = CommentSerializer(many=False)
