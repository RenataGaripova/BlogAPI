# Python modules
import json
import redis

# Django modules
from django.conf import settings

# Project modules
from .models import Post


r = redis.from_url(settings.REDIS_SSE_URL, decode_responses=True)


def publish_post_event(post: Post) -> None:
    data = json.dumps({
        "post_id": post.id,
        "title": post.title,
        "body": post.body,
        "author": post.author.id,
        "created_at": post.created_at.isoformat(),
    })
    r.publish("posts.published", data)
