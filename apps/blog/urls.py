# Django modules
from django.urls import include, path

# DRF modules
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

# Project modules
from .views import PostViewSet, CommentViewSet, get_stats


router_v1 = DefaultRouter()
router_v1.register("posts", PostViewSet, basename="posts")

comments_router_v1 = NestedDefaultRouter(
    router_v1,
    "posts",
    lookup="posts",
)
comments_router_v1.register(
    "comments",
    CommentViewSet,
    basename="comments",
)

urlpatterns = [
    path("", include(router_v1.urls)),
    path("", include(comments_router_v1.urls)),
    path(
        "stats/",
        get_stats,
        name="stats",
    ),
]
