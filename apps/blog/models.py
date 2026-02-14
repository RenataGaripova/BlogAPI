# Django modules
from django.db.models import (
    CharField,
    SlugField,
    ForeignKey,
    CASCADE,
    TextField,
    ManyToManyField,
    TextChoices,
)

# Project modules
from apps.abstracts.models import AbstractBaseModel
from apps.users.models import CustomUser


class Category(AbstractBaseModel):
    """Category model."""

    MAX_NAME_LENGTH = 100

    name = CharField(
        max_length=MAX_NAME_LENGTH, unique=True, verbose_name="Name"
    )
    slug = SlugField(unique=True, verbose_name="Slug")

    class Meta:
        """Metadata."""

        verbose_name_plural = "Categories"
        default_related_name = "categories"
        ordering = ("-created_at",)


class Tag(AbstractBaseModel):
    """Tag model."""

    MAX_NAME_LENGTH = 50

    name = CharField(
        max_length=MAX_NAME_LENGTH, unique=True, verbose_name="Name"
    )
    slug = SlugField(unique=True, verbose_name="Slug")

    class Meta:
        """Metadata."""

        default_related_name = "tags"
        ordering = ("-created_at",)


class Status(TextChoices):
    """Statuses text choices."""

    DRAFT = "DR", "Draft"
    PUBLISHED = "PB", "Published"


class Post(AbstractBaseModel):
    """Post model."""

    MAX_TITLE_LENGTH = 200
    MAX_CODE_LENGTH = 4

    author = ForeignKey(
        to=CustomUser, on_delete=CASCADE, verbose_name="Author"
    )
    slug = SlugField(unique=True, verbose_name="Slug")
    title = CharField(max_length=MAX_TITLE_LENGTH, verbose_name="Title")
    body = TextField(verbose_name="Body")
    category = ForeignKey(
        to=Category, on_delete=CASCADE, verbose_name="Category"
    )
    tags = ManyToManyField(to=Tag, blank=True, verbose_name="Tags")
    status = CharField(
        choices=Status.choices,
        default=Status.DRAFT,
        max_length=MAX_CODE_LENGTH,
    )

    class Meta:
        """Metadata."""

        default_related_name = "posts"
        ordering = ("-created_at",)


class Comment(AbstractBaseModel):
    """Comment model."""

    post = ForeignKey(to=Post, on_delete=CASCADE, verbose_name="Post")
    author = ForeignKey(
        to=CustomUser, on_delete=CASCADE, verbose_name="Author"
    )
    body = TextField(verbose_name="Body")

    class Meta:
        """Metadata."""

        default_related_name = "comments"
