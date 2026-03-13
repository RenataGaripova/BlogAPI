# Python modules
import json
import logging
import redis
import asyncio
from typing import Any, Optional, Sequence
from asgiref.sync import sync_to_async
from httpx import AsyncClient

# Django modules
from django_ratelimit.decorators import ratelimit
from django.db.models import QuerySet
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.http import JsonResponse

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
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_401_UNAUTHORIZED,
)

# Project modules
from apps.abstracts.serializers import ErrorDetailSerializer
from apps.users.models import CustomUser
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
        return cache.get("posts_list_v", 1)

    def get_cache_key(self, request: DRFRequest) -> str:
        """Returns cache key for a viewset."""
        cache_version = self.get_cache_version()
        query = "&".join(
            f"{k}={v}" for k, v in sorted(request.query_params.items())
        )
        lang: str = request.LANGUAGE_CODE
        if request.user.is_authenticated:
            user: int = request.user.id
        else:
            user: str = "anon"

        return f"posts_list_v{cache_version}_user_{user}_{query}_{lang}"

    def increase_cache_version(self):
        """Increases cache version."""
        try:
            cache.incr("posts_list_v")
        except ValueError:
            cache.set("posts_list_v", 2)

    @extend_schema(
        summary="List posts",
        description="The endpoint is responsible for listing existing posts.",
        responses={
            HTTP_200_OK: OpenApiResponse(
                response=PostReadSerializer(many=True),
                description="Successfully. You got the list of paginated posts.",
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Forbidden. You do not have permission to perform this action.",
            ),
            HTTP_405_METHOD_NOT_ALLOWED: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Method not allowed. You used wrong HTTP request type."
                "Only GET and POST can be used to reach this endpoint.",
            ),
            HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
                description="Server receives too many requests.",
                response=ErrorDetailSerializer,
            ),
        },
        tags=["Posts"],
    )
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

    @extend_schema(
        summary="Create a new post",
        description=(
            "The endpoint is responsible for creating a new post."
            " Contains created_at and updated_at timestamps, according to user's timezone."
        ),
        responses={
            HTTP_201_CREATED: OpenApiResponse(
                response=PostReadSerializer(many=True),
                description="Successfully. You created a new post.",
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="User is not authorized.",
                response=ErrorDetailSerializer,
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Forbidden. You do not have permission to perform this action.",
            ),
            HTTP_405_METHOD_NOT_ALLOWED: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Method not allowed. You used wrong HTTP request type."
                "Only GET and POST can be used to reach this endpoint.",
            ),
            HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
                description="Server receives too many requests.",
                response=ErrorDetailSerializer,
            ),
        },
        tags=["Posts"],
    )
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

    @extend_schema(
        summary="Update a post",
        description="The endpoint is responsible for updating a post.",
        responses={
            HTTP_200_OK: OpenApiResponse(
                response=PostReadSerializer(many=True),
                description="Successfully. You've updated a post.",
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="User is not authorized.",
                response=ErrorDetailSerializer,
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Forbidden. You do not have permission to perform this action.",
            ),
            HTTP_405_METHOD_NOT_ALLOWED: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Method not allowed. You used wrong HTTP request type."
                "Only PATCH can be used to reach this endpoint.",
            ),
            HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
                description="Server receives too many requests.",
                response=ErrorDetailSerializer,
            ),
        },
        tags=["Posts"],
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
                data={
                    "detail": _("Post with slug=%(slug)s does not exist.")
                    % {"slug": slug}
                },
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

    @extend_schema(
        summary="Delete a post",
        description="The endpoint is responsible for deleting a post.",
        responses={
            HTTP_200_OK: OpenApiResponse(
                response=PostReadSerializer(many=True),
                description="Successfully. You've deleted a post.",
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="User is not authorized.",
                response=ErrorDetailSerializer,
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Forbidden. You do not have permission to perform this action.",
            ),
            HTTP_405_METHOD_NOT_ALLOWED: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Method not allowed. You used wrong HTTP request type."
                "Only DELETE can be used to reach this endpoint.",
            ),
            HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
                description="Server receives too many requests.",
                response=ErrorDetailSerializer,
            ),
        },
        tags=["Posts"],
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
                data={
                    "detail": _("Post with slug=%(slug)s does not exist.")
                    % {"slug": slug}
                },
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

    @extend_schema(
        summary="List comments",
        description=(
            "The endpoint is responsible for listing existing comments."
            " Contains created_at and updated_at timestamps, according to user's timezone."
        ),
        responses={
            HTTP_200_OK: OpenApiResponse(
                response=PostReadSerializer(many=True),
                description="Successfully. You got the list of paginated comments.",
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Forbidden. You do not have permission to perform this action.",
            ),
            HTTP_405_METHOD_NOT_ALLOWED: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Method not allowed. You used wrong HTTP request type."
                "Only GET and POST can be used to reach this endpoint.",
            ),
            HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
                description="Server receives too many requests.",
                response=ErrorDetailSerializer,
            ),
        },
        tags=["Comments"],
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
                    "detail": _(
                        "Post with slug=%(posts_slug)s does not exist."
                    )
                    % {"slug": posts_slug}
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

    @extend_schema(
        summary="Create a new comment",
        description="The endpoint is responsible for creating a new comment.",
        responses={
            HTTP_201_CREATED: OpenApiResponse(
                response=PostReadSerializer(many=True),
                description="Successfully. You created a new comment.",
            ),
            HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="User is not authorized.",
                response=ErrorDetailSerializer,
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Forbidden. You do not have permission to perform this action.",
            ),
            HTTP_405_METHOD_NOT_ALLOWED: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Method not allowed. You used wrong HTTP request type."
                "Only GET and POST can be used to reach this endpoint.",
            ),
            HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
                description="Server receives too many requests.",
                response=ErrorDetailSerializer,
            ),
        },
        tags=["Comments"],
    )
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
                    "detail": _(
                        "Post with slug=%(posts_slug)s does not exist."
                    )
                    % {"slug": posts_slug}
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


async def get_blog_stats() -> dict[str, Any]:
    """Returns statistics of a blog."""
    users_count: int = await sync_to_async(
        CustomUser.objects.count, thread_sensitive=True
    )()
    posts_count: int = await sync_to_async(
        Post.objects.count, thread_sensitive=True
    )()
    comments_count: int = await sync_to_async(
        Comment.objects.count, thread_sensitive=True
    )()
    return {
        {
            "total_posts": posts_count,
            "total_comments": comments_count,
            "total_users": users_count,
        }
    }


async def get_exchange_rates(client: AsyncClient) -> dict[str, Any]:
    """Returns current exchange rate."""
    response = await client.get("https://open.er-api.com/v6/latest/USD")
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    rates: dict[str, Any] = data.get("rates")
    return {
        "KZT": rates.get("KZT"),
        "EUR": rates.get("EUR"),
        "RUB": rates.get("RUB"),
    }


async def get_current_time(client: AsyncClient) -> dict[str, Any]:
    """Returns current time."""
    response = await client.get(
        "https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty"
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    return data.get("dateTime")


async def get_stats(request: DRFRequest) -> DRFResponse:
    "Return some common statistics."
    async with AsyncClient() as client:
        blog_answ: dict[str, Any] = get_blog_stats()
        exchange_rates_answ: dict[str, Any] = get_exchange_rates(client=client)
        current_time_answ: dict[str, Any] = get_current_time(client=client)
        blog, exchange_rates, current_time = await asyncio.gather(
            blog_answ,
            exchange_rates_answ,
            current_time_answ,
        )
    return JsonResponse(
        data={
            "blog": blog,
            "exchange_rates": exchange_rates,
            "current_time": current_time,
        }
    )
