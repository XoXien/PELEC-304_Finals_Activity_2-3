from django.shortcuts import get_object_or_404, render

from .models import Game, Product


def store(request):
    return render(request, "credits/store.html", {
        "games": Game.objects.all(),
        "products": Product.objects.filter(is_active=True).select_related("game"),
        "page_title": "Game credits",
    })


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("game"), pk=pk, is_active=True)
    return render(request, "credits/detail.html", {
        "product": product, "page_title": product.name,
    })


def api_guide(request):
    return render(request, "credits/api_guide.html", {
        "product_count": Product.objects.filter(is_active=True).count(),
        "first_product": Product.objects.filter(is_active=True).first(),
        "page_title": "API guide",
    })
