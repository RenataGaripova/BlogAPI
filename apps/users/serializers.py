# Python modules
from typing import Any

# Django modules
from django.contrib.auth.password_validation import validate_password

# DRF modules
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    SerializerMethodField,
)
from drf_extra_fields.fields import Base64ImageField

# Project modules
from .models import CustomUser


class UserRegistrationSerializer(ModelSerializer):
    """Serializer for user registration."""

    password = CharField(
        max_length=CustomUser.MAX_PASSWORD_LENGTH,
        write_only=True,
    )

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
            "date_joined",
        )

    def validate_password(self, value: str) -> str:
        """Validates user's password."""
        validate_password(value)
        return value

    def create(self, validated_data: dict[str, Any]):
        """Creates a new custom user."""
        return CustomUser.objects.create(**validated_data)


class AuthorSerializer(ModelSerializer):
    """Serializer responsible for post / comment author representation."""

    avatar = Base64ImageField()
    full_name = SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "username",
            "full_name",
            "avatar",
        )

    def get_full_name(self, obj: CustomUser):
        """Returns full name of a user."""
        return f"{obj.first_name} {obj.last_name}"
