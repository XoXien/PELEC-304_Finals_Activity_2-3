from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


class Game(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    short_name = models.CharField(max_length=10)
    credit_unit = models.CharField(max_length=40)
    theme = models.CharField(
        max_length=12,
        choices=[("coral", "Coral"), ("gold", "Gold"), ("mint", "Mint"), ("violet", "Violet")],
        default="mint",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """One denomination of game credits is one product row."""

    sku = models.CharField("SKU", max_length=30, unique=True)
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    description = models.TextField()
    credit_amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    stock = models.PositiveIntegerField(default=100)
    featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gt=0), name="product_price_positive"),
            models.CheckConstraint(condition=models.Q(credit_amount__gt=0), name="product_credits_positive"),
        ]

    @property
    def available(self):
        return self.is_active and self.stock > 0

    def get_absolute_url(self):
        return reverse("catalog:detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.name} ({self.sku})"
