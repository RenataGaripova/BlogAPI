# Python modules
from zoneinfo import ZoneInfo
from datetime import datetime

# Django modules
from django.utils import timezone

# DRF modules
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
)
from rest_framework.request import Request as DRFRequest

# Project modules
from .models import Category, Tag, Post, Comment
from apps.users.serializers import AuthorSerializer


class TagReadSerializer(ModelSerializer):
    """Serializer for handling tags-related GET endpoints."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class CategoryBaseSerializer(ModelSerializer):
    """Serializer for handling tags-related GET endpoints."""

    name = SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug")

    def get_name(self, obj: Category) -> str:
        request: DRFRequest = self.context.get("request")
        lang: str = request.LANGUAGE_CODE
        return getattr(obj, f"name{lang}", obj.name_en)


class CategoryReadSerializer(CategoryBaseSerializer):
    """Serializer for handling tags-related GET endpoints."""

    pass


class PostBaseSerializer(ModelSerializer):
    """Serializer for handling post-related requests."""

    created_at = SerializerMethodField()
    updated_at = SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "slug",
            "title",
            "body",
            "category",
            "tags",
            "status",
            "created_at",
            "updated_at",
        )

    def get_created_at(self, obj: Post) -> datetime:
        """Returns created_at in client's timezone."""
        request = self.context.get("request")
        if request.user.is_authenticated:
            tz: ZoneInfo = ZoneInfo(request.user.timezone)
        else:
            tz: ZoneInfo = ZoneInfo("UTC")
        return timezone.localtime(obj.created_at, tz)

    def get_updated_at(self, obj: Post) -> datetime:
        """Returns created_at in client's timezone."""
        request = self.context.get("request")
        if request.user.is_authenticated:
            tz: ZoneInfo = ZoneInfo(request.user.timezone)
        else:
            tz: ZoneInfo = ZoneInfo("UTC")
        return timezone.localtime(obj.updated_at, tz)


class PostReadSerializer(PostBaseSerializer):
    """Serializer for handling post-related GET requests."""

    author = AuthorSerializer(read_only=True)
    tags = TagReadSerializer(many=True)
    category = CategoryReadSerializer()


class PostWriteSerializer(PostBaseSerializer):
    """Serializer for handling post-related POST, PATCH requests."""

    author = AuthorSerializer(read_only=True)


class PostCommentSerializer(PostBaseSerializer):
    """Serializer for post representation in comments-related endpoints."""

    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "slug",
            "title",
            "body",
            "created_at",
            "updated_at",
        )


class CommentSerializer(ModelSerializer):
    """Serializer for handling post-related requests."""

    author = AuthorSerializer(read_only=True)
    post = PostCommentSerializer(read_only=True)
    created_at = SerializerMethodField()
    updated_at = SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "author",
            "body",
            "created_at",
            "updated_at",
        )

    def get_created_at(self, obj: Post) -> datetime:
        """Returns created_at in client's timezone."""
        request = self.context.get("request")
        if request.user.is_authenticated:
            tz: ZoneInfo = ZoneInfo(request.user.timezone)
        else:
            tz: ZoneInfo = ZoneInfo("UTC")
        return timezone.localtime(obj.created_at, tz)

    def get_updated_at(self, obj: Post) -> datetime:
        """Returns created_at in client's timezone."""
        request = self.context.get("request")
        if request.user.is_authenticated:
            tz: ZoneInfo = ZoneInfo(request.user.timezone)
        else:
            tz: ZoneInfo = ZoneInfo("UTC")
        return timezone.localtime(obj.updated_at, tz)
