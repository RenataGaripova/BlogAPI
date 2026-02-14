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

# Project modules
from .serializers import UserRegistrationSerializer
from .models import CustomUser

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
        return DRFResponse(
            data=response_data,
            status=HTTP_200_OK,
        )
