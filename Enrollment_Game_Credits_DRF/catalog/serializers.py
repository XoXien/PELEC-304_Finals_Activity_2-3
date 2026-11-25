from rest_framework import serializers

from .models import Game, Product


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["id", "name", "slug", "short_name", "credit_unit", "theme"]


class ProductSerializer(serializers.ModelSerializer):
    game_name = serializers.CharField(source="game.name", read_only=True)
    game_slug = serializers.CharField(source="game.slug", read_only=True)
    short_name = serializers.CharField(source="game.short_name", read_only=True)
    theme = serializers.CharField(source="game.theme", read_only=True)
    credit_unit = serializers.CharField(source="game.credit_unit", read_only=True)
    currency = serializers.CharField(default="PHP", read_only=True)
    available = serializers.BooleanField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="catalog:api:product-detail")
    product_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "url", "product_url", "sku", "name", "description", "game", "game_name",
            "game_slug", "short_name", "theme", "credit_amount", "credit_unit", "price",
            "currency", "stock", "available", "featured", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_product_url(self, obj):
        return self.context["request"].build_absolute_uri(obj.get_absolute_url())


class ProductQuerySerializer(serializers.Serializer):
    game = serializers.SlugField(required=False)
    min_price = serializers.DecimalField(max_digits=9, decimal_places=2, min_value=0, required=False)
    max_price = serializers.DecimalField(max_digits=9, decimal_places=2, min_value=0, required=False)
    available = serializers.BooleanField(required=False)
    featured = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if "min_price" in attrs and "max_price" in attrs and attrs["min_price"] > attrs["max_price"]:
            raise serializers.ValidationError({"max_price": "Must be greater than or equal to min_price."})
        return attrs
