# Python modules

# Django modules

# DRF modules
from rest_framework.serializers import (
    ModelSerializer,
)

# Project modules
from .models import Category, Tag, Post, Comment
from apps.users.serializers import AuthorSerializer


class TagReadSerializer(ModelSerializer):
    """Serializer for handling tags-related GET endpoints."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class CategoryReadSerializer(ModelSerializer):
    """Serializer for handling tags-related GET endpoints."""

    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class PostReadSerializer(ModelSerializer):
    """Serializer for handling post-related GET requests."""

    author = AuthorSerializer(read_only=True)
    tags = TagReadSerializer(many=True)
    category = CategoryReadSerializer()

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


class PostWriteSerializer(ModelSerializer):
    """Serializer for handling post-related POST, PATCH requests."""

    author = AuthorSerializer(read_only=True)

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


class PostCommentSerializer(ModelSerializer):
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
