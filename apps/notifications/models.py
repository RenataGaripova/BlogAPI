# Django modules
from django.db.models import ForeignKey, BooleanField, CASCADE
from django.utils.translation import gettext_lazy as _

# Project modules
from apps.abstracts.models import AbstractBaseModel
from apps.users.models import CustomUser
from apps.blog.models import Comment


class Notification(AbstractBaseModel):
    """Notification model."""

    recipient: ForeignKey = ForeignKey(
        to=CustomUser,
        on_delete=CASCADE,
        verbose_name=_("Recipient"),
    )
    comment: ForeignKey = ForeignKey(
        to=Comment,
        on_delete=CASCADE,
        verbose_name=_("Comment"),
    )
    is_read: BooleanField = BooleanField(
        verbose_name=_("Is read?"), default=False
    )

    class Meta:
        """Metadata."""

        default_related_name = "notifications"
        ordering = ("-created_at",)
