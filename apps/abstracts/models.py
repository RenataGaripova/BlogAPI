# Python modules

# Django modules
from django.db.models import (
    Model,
    DateTimeField,
)


class AbstractBaseModel(Model):
    """Abstract Base Model with common fields."""

    created_at = DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        """Meta class."""

        abstract = True
