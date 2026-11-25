from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api, views

app_name = "catalog"
router = DefaultRouter()
router.register("products", api.ProductViewSet, basename="product")
router.register("games", api.GameViewSet, basename="game")
urlpatterns = [
    path("", views.store, name="store"),
    path("products/<int:pk>/", views.product_detail, name="detail"),
    path("api-guide/", views.api_guide, name="api-guide"),
    path("api/", include((router.urls, "api"), namespace="api")),
]
