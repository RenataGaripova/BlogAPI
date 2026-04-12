# Python modules
from typing import Any
import logging

# Django modules
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

# DRF modules
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.status import (
    HTTP_200_OK,
)
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
)
from rest_framework.status import (
    HTTP_403_FORBIDDEN,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_429_TOO_MANY_REQUESTS,
)

# Project modules
from apps.abstracts.serializers import (
    ErrorDetailSerializer,
    ResponseUserRegistrationSerializer,
)
from .serializers import UserRegistrationSerializer
from .models import CustomUser
from .tasks import send_welcome_email

logger = logging.getLogger(__name__)


@method_decorator(
    ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post"
)
@method_decorator(
    ratelimit(key="post:username", rate="5/m", method="POST", block=True),
    name="post",
)
class RateLimitTokenObtainPairView(TokenObtainPairView):
    """Rate limiting simple-jwt token obtain view."""


class CustomUserViewSet(ViewSet):
    @extend_schema(
        summary="Registrate a new user",
        description="The endpoint is responsible for users registration.",
        responses={
            HTTP_200_OK: OpenApiResponse(
                response=ResponseUserRegistrationSerializer(many=False),
                description="Successfully. You have signed up.",
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Forbidden. You do not have permission to perform this action.",
            ),
            HTTP_405_METHOD_NOT_ALLOWED: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Method not allowed. You used wrong HTTP request type."
                "Only POST can be used to reach this endpoint.",
            ),
            HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
                description="Server receives too many requests.",
                response=ErrorDetailSerializer,
            ),
        },
        tags=["Users"],
    )
    @action(
        methods=("post",),
        detail=False,
        url_path="register",
    )
    @ratelimit(key="ip", rate="5/m", method="POST", block=True)
    def register(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[Any, Any],
    ) -> DRFResponse:
        """
        Handles POST requests to register a new user.

        Parameters:
            request: DRFRequest,
                The request object.
            product_id: int,
                Product's id.
            *args: list,
                Additional positional arguments.
            **kwargs: dict,
                Additional keyword arguments.

        Returns:
            DRFResponse -
                A response containing data about created user.
        """

        logger.info(
            "Registration attempt for email: %s", request.data.get("email")
        )

        serializer: UserRegistrationSerializer = UserRegistrationSerializer(
            data=request.data
        )
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            logger.exception(
                "User registration failed: %s. Errors: %s",
                request.data,
                serializer.errrors,
            )
            raise
        user: CustomUser = serializer.save()

        # Generate JWT tokens
        refresh_token: RefreshToken = RefreshToken.for_user(user)
        access_token: AccessToken = refresh_token.access_token

        response_data: dict[str, Any] = serializer.data
        response_data["access"] = str(access_token)
        response_data["refresh"] = str(refresh_token)

        logger.info("User registered: %s", user.email)

        send_welcome_email.delay(
            user.id,
            subject="Welcome to our Blog!",
            context={
                "message": "You have successfuly registered on the Blog!",
                "receiver_name": user.first_name,
            },
        )

        return DRFResponse(
            data=response_data,
            status=HTTP_200_OK,
        )
