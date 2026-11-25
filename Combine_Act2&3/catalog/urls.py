from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from . import api

app_name = "catalog"
router = DefaultRouter()
router.register("products", api.ProductViewSet, basename="product")
router.register("games", api.GameViewSet, basename="game")
urlpatterns = [
    path("", RedirectView.as_view(pattern_name="catalog:api:product-list"), name="index"),
    path("products/<int:pk>/", RedirectView.as_view(pattern_name="catalog:api:product-detail"), name="legacy-detail"),
    path("api/", include((router.urls, "api"), namespace="api")),
]
