# Python modules
import redis

# Django modules
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Subscribes to comments channel and
    prints incoming messages to the console.
    """

    def handle(self, *args, **options):
        """Handles the command."""

        r = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )
        p = r.pubsub()
        p.subscribe("comments")
        self.stdout.write(self.style.SUCCESS("Subscribed to comments"))

        for msg in p.listen():
            if msg and msg["type"] == "message":
                self.stdout.write(f"Received a message: {msg['data']}.")
