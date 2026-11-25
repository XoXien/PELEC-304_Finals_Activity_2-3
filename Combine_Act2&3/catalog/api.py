from django.db.models.deletion import ProtectedError
from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError

from .models import Game, Product
from .permissions import StaffWriteOrReadOnly
from .serializers import GameSerializer, ProductQuerySerializer, ProductSerializer


class StableOrderingFilter(filters.OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering = list(super().get_ordering(request, queryset, view) or ["id"])
        if not any(field.lstrip("-") in {"id", "pk"} for field in ordering):
            ordering.append("id")
        return ordering


class GameViewSet(viewsets.ModelViewSet):
    """Game resources with public GET access and staff-only create, update, and delete."""

    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [StaffWriteOrReadOnly]
    pagination_class = None

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError({"detail": "Remove or reassign this game's products before deleting it."})


class ProductViewSet(viewsets.ModelViewSet):
    """Game-credit products with full CRUD support.

    GET: list or read a product. POST: create a product.
    PUT: replace a product. PATCH: edit selected fields. DELETE: remove a product.

    Filters: game, search, min_price, max_price, available, and featured.
    Sorting: ordering=price, -price, name, or credit_amount.
    Use ?format=json for raw JSON, or view this URL normally for the browsable API.
    Sample prices are for this classroom catalog; this API does not deliver real credits.
    Use the Log in link above with an administrator account to use the write forms.
    """

    serializer_class = ProductSerializer
    permission_classes = [StaffWriteOrReadOnly]
    filter_backends = [filters.SearchFilter, StableOrderingFilter]
    search_fields = ["name", "sku", "description", "game__name"]
    ordering_fields = ["id", "name", "price", "credit_amount", "created_at"]
    ordering = ["id"]

    def get_queryset(self):
        queryset = Product.objects.select_related("game").all()
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True)
        # A normal dictionary keeps omitted Boolean filters absent. QueryDict
        # otherwise uses checkbox semantics and turns an omitted value into False.
        query = ProductQuerySerializer(data=self.request.query_params.dict())
        query.is_valid(raise_exception=True)
        values = query.validated_data
        if "game" in values:
            queryset = queryset.filter(game__slug=values["game"])
        if "min_price" in values:
            queryset = queryset.filter(price__gte=values["min_price"])
        if "max_price" in values:
            queryset = queryset.filter(price__lte=values["max_price"])
        if "available" in values:
            queryset = queryset.filter(stock__gt=0) if values["available"] else queryset.filter(stock=0)
        if "featured" in values:
            queryset = queryset.filter(featured=values["featured"])
        return queryset
