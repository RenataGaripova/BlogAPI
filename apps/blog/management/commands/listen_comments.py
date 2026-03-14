# Python modules
import json
import asyncio
import redis.asyncio as redis
from typing import Any

# Django modules
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Subscribes to comments channel and
    prints incoming messages to the console.
    """

    async def listen(self, *args, **options):
        """Handles the command."""

        r = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )
        p = r.pubsub()
        await p.subscribe("comments")
        self.stdout.write(self.style.SUCCESS("Subscribed to comments"))
        # async is here because the program waiting for redis messages,
        # and async allows not to block the thread and perform other tasks.
        async for msg in p.listen():
            if msg and msg["type"] == "message":
                data: dict[str, Any] = json.loads(msg["data"])
                post_slug: str = data.get("post_slug")
                author: int = data.get("author_id")
                body: str = data.get("body")
                self.stdout.write(
                    f"Received a comment from author {author} on post {post_slug}: {body}."
                )

    def handle(self, *args, **kwargs) -> None:
        """Handles the command execution."""
        asyncio.run(self.listen())
