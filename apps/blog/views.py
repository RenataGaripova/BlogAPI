# Python modules
import json
import logging
import redis
from typing import Any, Optional, Sequence

# Django modules
from django_ratelimit.decorators import ratelimit
from django.db.models import QuerySet
from django.core.cache import cache

# DRF modules
from rest_framework.viewsets import ViewSet
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_204_NO_CONTENT,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError

# Project modules
from .models import Post, Comment
from .pagination import CustomCursorPagination
from .serializers import (
    PostReadSerializer,
    PostWriteSerializer,
    CommentSerializer,
)
from .permissions import IsAuthorOrReadOnly

logger = logging.getLogger(__name__)


class PostViewSet(ViewSet):
    """Viewset responsible for handling post-related endpoints."""

    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    )
    pagination_class = CustomCursorPagination
    lookup_field = "slug"

    def get_cache_version(self):
        """Returns cache version."""
        return cache.get("posts_list_version", 1)

    def get_cache_key(self, request: DRFRequest) -> str:
        """Returns cache key for a viewset."""
        cache_version = self.get_cache_version()
        if request.user.is_authenticated:
            user = request.user.id
        else:
            user = "anon"

        return f"posts_list_version{cache_version}_user_{user}_{request.query_params.urlencode()}"

    def increase_cache_version(self):
        """Increases cache version."""
        try:
            cache.incr("posts_list_version")
        except ValueError:
            cache.set("posts_list_version", 2)

    def list(
        self,
        request: DRFRequest,
        cursor_id: Optional[int] = None,
        page_size: int = 20,
        *args: tuple[Any, ...],
        **kwargs: dict[Any, Any],
    ) -> DRFResponse:
        """
        Handles GET requests to get a list of posts.

        Parameters:
            request: DRFRequest,
                The request object.
            *args: list,
                Additional positional arguments.
            **kwargs: dict,
                Additional keyword arguments.

        Returns:
            DRFResponse -
                A response containing a paginated list of posts.
        """

        cache_key = self.get_cache_key(request=request)
        timeout = 60

        data = cache.get(cache_key)

        if data:
            return DRFResponse(data)

        posts: QuerySet[Post] = Post.objects.all()

        paginator: CustomCursorPagination = self.pagination_class()
        page: Optional[Sequence[Any]] = paginator.paginate_queryset(
            queryset=posts, request=request, view=self
        )
        if page is not None:
            serializer: PostReadSerializer = PostReadSerializer(
                page,
                many=True,
            )
            response = paginator.get_paginated_response(serializer.data)
        else:
            serializer: PostReadSerializer = PostReadSerializer(
                posts,
                many=True,
            )
            response = DRFResponse(serializer.data)
        # Manual cache set because of cursor pagination
        cache.set(key=cache_key, value=response.data, timeout=timeout)
        return response

    @ratelimit(key="user", rate="20/m", method="POST", block=True)
    def create(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[Any, Any],
    ) -> DRFResponse:
        """
        Handles POST requests to create a new post.

        Parameters:
            request: DRFRequest,
                The request object.
            *args: list,
                Additional positional arguments.
            **kwargs: dict,
                Additional keyword arguments.

        Returns:
            DRFResponse -
                A response containing info about created post.
        """
        serializer: PostWriteSerializer = PostWriteSerializer(
            data=request.data,
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            logger.exception(
                "New post creation failed: %s. Errors: %s",
                request.data,
                serializer.errors,
            )
            raise
        serializer.save(author=request.user)
        self.increase_cache_version()
        logger.info("New post was created: %s", serializer.validated_data)
        return DRFResponse(
            data=serializer.data,
            status=HTTP_201_CREATED,
        )

    def partial_update(
        self,
        request: DRFRequest,
        slug: str,
        *args: tuple[Any, ...],
        **kwargs: dict[Any, Any],
    ) -> DRFResponse:
        """
        Handles PATCH requests to update an exisiting post.

        Parameters:
            request: DRFRequest,
                The request object.
            *args: list,
                Additional positional arguments.
            **kwargs: dict,
                Additional keyword arguments.

        Returns:
            DRFResponse -
                A response containing info about updated post.
        """
        try:
            post: Post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            return DRFResponse(
                data={"detail": f"Post with slug={slug} does not exist."},
                status=HTTP_404_NOT_FOUND,
            )
        self.check_object_permissions(request=request, obj=post)
        serializer: PostWriteSerializer = PostWriteSerializer(
            instance=post,
            data=request.data,
            partial=True,
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            logger.exception(
                "Post with id %s update failed. Errors: %s",
                post.id,
                serializer.errors,
            )
            raise
        serializer.save()
        self.increase_cache_version()
        logger.info("Post with slug %s was updated.", slug)
        return DRFResponse(
            data=serializer.data,
            status=HTTP_201_CREATED,
        )

    def destroy(
        self,
        request: DRFRequest,
        slug: str,
        *args: tuple[Any, ...],
        **kwargs: dict[Any, Any],
    ) -> DRFResponse:
        """
        Handles DELETE requests to delete an exisiting post.

        Parameters:
            request: DRFRequest,
                The request object.
            *args: list,
                Additional positional arguments.
            **kwargs: dict,
                Additional keyword arguments.

        Returns:
            DRFResponse -
                Status HTTP 204 - No content.
        """
        try:
            post: Post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            return DRFResponse(
                data={"detail": f"Post with slug={slug} does not exist."},
                status=HTTP_404_NOT_FOUND,
            )
        self.check_object_permissions(request=request, obj=post)
        try:
            post.delete()
        except Exception as e:
            logger.exception(
                "Post delete with id %s failed. Error: %s", post.id, e
            )
        logger.info("Post with slug %s was deleted.", slug)
        return DRFResponse(
            data={},
            status=HTTP_204_NO_CONTENT,
        )


class CommentViewSet(ViewSet):
    """Viewset responsible for handling comments-related endpoints."""

    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    )
    pagination_class = CustomCursorPagination

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.redis_client = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )

    def list(
        self,
        request: DRFRequest,
        posts_slug: str,
        *args: tuple[Any, ...],
        **kwargs: dict[Any, Any],
    ) -> DRFResponse:
        """
        Handles GET requests to get a list of comments related to specific post.

        Parameters:
            request: DRFRequest,
                The request object.
            *args: list,
                Additional positional arguments.
            **kwargs: dict,
                Additional keyword arguments.

        Returns:
            DRFResponse -
                A response containing a list of comments.
        """
        try:
            post: Post = Post.objects.get(slug=posts_slug)
        except Post.DoesNotExist:
            return DRFResponse(
                data={
                    "detail": f"Post with slug={posts_slug} does not exist."
                },
                status=HTTP_404_NOT_FOUND,
            )
        comments: QuerySet[Comment] = post.comments.all()
        paginator: CustomCursorPagination = self.pagination_class()
        page: Optional[Sequence[Any]] = paginator.paginate_queryset(
            queryset=comments, request=request, view=self
        )
        serializer: CommentSerializer = CommentSerializer(
            page,
            many=True,
        )
        return paginator.get_paginated_response(serializer.data)

    def create(
        self,
        request: DRFRequest,
        posts_slug: str,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        """
        Handles POST requests to create a new comment for a specific post.

        Parameters:
            request: DRFRequest,
                The request object.
            *args: list,
                Additional positional arguments.
            **kwargs: dict,
                Additional keyword arguments.

        Returns:
            DRFResponse -
                A response containing info about created comment.
        """
        try:
            post: Post = Post.objects.get(slug=posts_slug)
        except Post.DoesNotExist:
            return DRFResponse(
                data={
                    "detail": f"Post with slug={posts_slug} does not exist."
                },
                status=HTTP_404_NOT_FOUND,
            )
        serializer: CommentSerializer = CommentSerializer(
            data=request.data,
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            logger.exception(
                "New comment creation failed: %s. Errors: %s",
                request.data,
                serializer.errrors,
            )
            raise

        channel = "comments"
        message = {
            "event": "create",
            "data": serializer.data,
            "user": request.user.id,
        }

        self.redis_client.publish(channel, json.dumps(message))
        serializer.save(author=request.user, post=post)
        logger.info("New comment was posted: %s", serializer.validated_data)
        return DRFResponse(
            data=serializer.data,
            status=HTTP_201_CREATED,
        )
