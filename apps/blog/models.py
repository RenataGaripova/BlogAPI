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
from django.utils.translation import gettext_lazy as _

# Project modules
from apps.abstracts.models import AbstractBaseModel
from apps.users.models import CustomUser


class Category(AbstractBaseModel):
    """Category model."""

    MAX_NAME_LENGTH = 100

    name_en = CharField(
        max_length=MAX_NAME_LENGTH, unique=True, verbose_name=_("Name")
    )
    name_ru = CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Name (Russian)"),
    )
    name_kz = CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Name (Kazakh)"),
    )
    slug = SlugField(unique=True, verbose_name=_("Slug"), auto_created=True)

    class Meta:
        """Metadata."""

        verbose_name_plural = "Categories"
        default_related_name = "categories"
        ordering = ("-created_at",)


class Tag(AbstractBaseModel):
    """Tag model."""

    MAX_NAME_LENGTH = 50

    name = CharField(
        max_length=MAX_NAME_LENGTH, unique=True, verbose_name=_("Name")
    )
    slug = SlugField(unique=True, auto_created=True, verbose_name=_("Slug"))

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
        to=CustomUser, on_delete=CASCADE, verbose_name=_("Author")
    )
    slug = SlugField(unique=True, verbose_name=_("Slug"), auto_created=True)
    title = CharField(max_length=MAX_TITLE_LENGTH, verbose_name=_("Title"))
    body = TextField(verbose_name=_("Body"))
    category = ForeignKey(
        to=Category, on_delete=CASCADE, verbose_name=_("Category")
    )
    tags = ManyToManyField(to=Tag, blank=True, verbose_name=_("Tags"))
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

    post = ForeignKey(to=Post, on_delete=CASCADE, verbose_name=_("Post"))
    author = ForeignKey(
        to=CustomUser, on_delete=CASCADE, verbose_name=_("Author")
    )
    body = TextField(verbose_name=_("Body"))

    class Meta:
        """Metadata."""

        default_related_name = "comments"
