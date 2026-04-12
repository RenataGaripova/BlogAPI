# Python modules
from typing import Any, Type

# Django modules
from django.db.models.signals import post_save
from django.dispatch import receiver

# Project modules
from apps.blog.models import Comment
from apps.users.models import CustomUser
from .models import Notification


@receiver(post_save, sender=Comment)
def create_notification_on_comment(
    sender: Type[Comment],
    instance: Comment,
    created: bool,
    **kwargs: dict[str, Any],
) -> None:
    """Notifies user when someone comments on his (her) post."""
    if not created:
        return

    author: CustomUser = instance.post.author
    Notification.objects.create(
        recipient=author,
        comment=instance,
    )
