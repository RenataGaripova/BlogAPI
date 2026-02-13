# Python modules
from typing import Any

# Django modules
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db.models import (
    CharField,
    EmailField,
    ImageField,
    BooleanField,
    DateTimeField,
)


class CustomUserManager(BaseUserManager):
    """Custom user manager."""

    def create_user(
        self,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password: str,
        **kwargs: dict[Any, Any],
    ) -> "CustomUser":
        """Creates and saves a User with the given data."""

        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")
        if not first_name:
            raise ValueError("Users must have a first name")
        if not last_name:
            raise ValueError("Users must have a last name")

        created_user: "CustomUser" = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )
        created_user.set_password(password)
        created_user.save(using=self._db)
        return created_user

    def create_superuser(
        self,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        password: str,
        **kwargs: dict[Any, Any],
    ) -> "CustomUser":
        """Creates and saves a Super user with the given data."""

        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)

        if kwargs.get("is_active") is not True:
            raise ValueError("is_active should be True for superuser")
        if kwargs.get("is_staff") is not True:
            raise ValueError("is_staff should be True for superuser")
        if kwargs.get("is_superuser") is not True:
            raise ValueError("is_superuser should be True for superuser")

        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")
        if not first_name:
            raise ValueError("Users must have a first name")
        if not last_name:
            raise ValueError("Users must have a last name")

        created_user: "CustomUser" = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )
        created_user.set_password(password)
        created_user.save(using=self._db)
        return created_user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    CustomUser database (table) model.
    """

    MAX_FIRST_NAME_LENGTH = 64
    MAX_LAST_NAME_LENGTH = 64
    MAX_USERNAME_LENGTH = 32
    MAX_EMAIL_LENGTH = 64
    MAX_PASSWORD_LENGTH = 128

    username = CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        verbose_name="Username",
    )
    email = EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        verbose_name="Email",
    )
    first_name = CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
        verbose_name="First name",
    )
    last_name = CharField(
        max_length=MAX_LAST_NAME_LENGTH,
        verbose_name="Last name",
    )
    is_active = BooleanField(default=True, verbose_name="Is user active?")
    is_staff = BooleanField(default=False, verbose_name="Is staff?")
    date_joined = DateTimeField(auto_now_add=True)
    avatar = ImageField(
        upload_to="users",
        blank=True,
        null=True,
        verbose_name="Avatar",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        """Meta options for CustomUser model."""

        verbose_name = "Custom User"
        verbose_name_plural = "Custom Users"
        ordering = ["-date_joined"]

    def __str__(self):
        """Returns string representation of an object"""
        return self.email
