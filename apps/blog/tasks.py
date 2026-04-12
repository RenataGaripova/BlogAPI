# Python modules
import logging
from datetime import datetime, timedelta

# Django + Third party modules
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def invalidate_post_cache() -> None:
    """Invalidates posts cache version."""
    try:
        cache.incr("posts_list_v")
    except ValueError:
        cache.set("posts_list_v", 2)


@shared_task
def publish_scheduled_posts() -> None:
    """Finds scheduled posts with time equal (or before) current and published them."""
    from .models import Post, Status
    from .events import publish_post_event

    now: datetime = timezone.now()
    posts: list[Post] = list(
        Post.objects.filter(status=Status.SCHEDULES, publish_at__lte=now)
    )
    Post.objects.filter(id__in=[p.id for p in posts]).update(
        status=Status.PUBLISHED
    )
    for post in posts:
        publish_post_event(post)


@shared_task
def clear_expired_notifications() -> None:
    """Deletes notifications older than 30 days."""
    from notifications.models import Notification

    relevant: datetime = timezone.now() - timedelta(days=30)
    Notification.objects.filter(created_at__lt=relevant).delete()


@shared_task
def generate_daily_stats():
    """Logs the number of new posts, comments, and users created in the last 24 hours."""
    from .models import Post, Comment
    from apps.users.models import CustomUser

    start_time: datetime = timezone.now() - timedelta(hours=24)
    new_posts: int = Post.objects.filter(created_at__gte=start_time).count()
    new_comments: int = Comment.objects.filter(
        created_at__gte=start_time
    ).count()
    new_users: int = CustomUser.objects.filter(
        date_joined__gte=start_time
    ).count()
    logger.info(
        "New posts created: %s; New comments created: %s; New users joined: %s.",
        new_posts,
        new_users,
        new_comments,
    )
