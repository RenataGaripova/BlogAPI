from typing import Any, Optional

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models import CustomUser
from apps.blog.models import Post


class CommentConsumer(AsyncJsonWebsocketConsumer):
    """Custom comment consumer."""

    async def connect(self) -> None:
        query_string: str = self.scope.get("query_string", b"").decode("utf-8")
        query_params: dict[str, Any] = dict(
            qp.split("=") for qp in query_string.split("&") if "=" in qp
        )
        token: str = query_params.get("token")

        user: Optional[CustomUser] = await self.get_user_from_token(token)

        if user is None:
            await self.close()
            return

        slug: str = self.scope["url_route"]["kwargs"].get("slug")

        post: Optional[Post] = await self.get_post_by_slug(slug)

        if post is None:
            await self.close()
            return

        self.group_name: str = f"post_{slug}_comments"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code) -> None:
        if hasattr(self, self.group_name):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def comment_created(self, event: dict[str, Any]) -> None:
        """Send message to client."""
        await self.send_json(event.get["data"])

    @database_sync_to_async
    def get_user_from_token(self, token: str) -> Optional[CustomUser]:
        """Returns a user from validated token or None."""
        try:
            validated_token = AccessToken(token)
            return CustomUser.objects.get(id=validated_token["user_id"])
        except Exception:
            return None

    @database_sync_to_async
    def get_post_by_slug(self, slug: str) -> Optional[Post]:
        """Returns a post by slug or None."""
        try:
            return Post.objects.get(slug=slug)
        except Exception:
            return None
