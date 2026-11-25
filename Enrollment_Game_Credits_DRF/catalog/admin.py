from django.contrib import admin

from .models import Game, Product


class CreditsAdminSite(admin.AdminSite):
    site_header = "LEVELUP Catalog Administration"
    site_title = "Game credits admin"
    index_title = "Manage games and credit packages"

    def each_context(self, request):
        context = super().each_context(request)
        from django.urls import reverse
        context["site_url"] = reverse("catalog:store")
        return context


credits_admin_site = CreditsAdminSite(name="credits_admin")


@admin.register(Game, site=credits_admin_site)
class GameAdmin(admin.ModelAdmin):
    list_display = ["name", "credit_unit", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


@admin.register(Product, site=credits_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["sku", "name", "game", "price", "stock", "featured", "is_active"]
    list_filter = ["game", "featured", "is_active"]
    search_fields = ["sku", "name", "game__name"]
    list_select_related = ["game"]
    readonly_fields = ["created_at", "updated_at"]
