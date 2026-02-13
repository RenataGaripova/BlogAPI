# Django modules
from django.urls import include, path

# DRF modules
from rest_framework.routers import DefaultRouter

# Project modules
from .views import CustomUserViewSet


router_v1 = DefaultRouter()
router_v1.register("auth", CustomUserViewSet, basename="register")


urlpatterns = [path("", include(router_v1.urls))]
