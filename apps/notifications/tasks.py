# Python modules
from typing import Any

# Django + Third party modules
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.blog.models import Post


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_new_comment(comment_id: int) -> None:
    """Handles creating the Notification record and publishing the WebSocket message when new comment is created."""
    from apps.blog.models import Comment
    from apps.users.models import CustomUser
    from .models import Notification

    comment = (
        Comment.objects
        .select_related("author", "post", "post__author")
        .filter(id=comment_id)
        .first()
    )
    if not comment:
        return

    post: Post = comment.post
    post_author: CustomUser = post.author

    if comment.author == post_author:  # ignore comments added by post's author
        return
    notification: Notification
    created: bool
    notification, created = Notification.objects.get_or_create(
        recipient=post_author,
        comment=comment,
    )
    channel_layer: Any | None = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"post_{post.slug}_comments",
        {
            "type": "comment_created",
            "data": {
                "comment_id": comment.id,
                "author": {
                    "id": comment.author.id,
                    "email": comment.author.email,
                },
                "body": comment.body,
                "created_at": comment.created_at,
            },
        },
    )
