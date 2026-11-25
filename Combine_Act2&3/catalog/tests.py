from decimal import Decimal
from io import StringIO
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Game, Product


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"])
class CatalogTests(TestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser(
            username="catalog_test_admin", password="Test-Only-2026-Catalog"
        )
        cls.regular = get_user_model().objects.create_user(username="catalog_test_user")

    def setUp(self):
        self.api = APIClient()
        self.list_url = reverse("catalog:api:product-list")

    def test_database_contains_24_products_and_four_games_after_migration(self):
        self.assertEqual(Product.objects.count(), 24)
        self.assertEqual(Game.objects.count(), 4)

    def test_public_product_list_returns_all_24_rows_as_json(self):
        response = self.api.get(self.list_url, {"format": "json"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 24)
        self.assertEqual(len(response.data["results"]), 24)
        product = response.data["results"][0]
        self.assertEqual(product["currency"], "PHP")
        self.assertIsInstance(product["price"], str)
        self.assertEqual(urlsplit(product["url"]).path, reverse("catalog:api:product-detail", args=[product["id"]]))
        self.assertNotIn("student_id", product)
        self.assertNotIn("product_url", product)
        self.assertNotIn("theme", product)

    def test_every_product_id_opens_its_own_record(self):
        for product in Product.objects.select_related("game"):
            response = self.api.get(reverse("catalog:api:product-detail", args=[product.pk]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["sku"], product.sku)
            self.assertEqual(response.data["game_name"], product.game.name)

    def test_api_root_and_game_list_are_public(self):
        root = self.api.get(reverse("catalog:api:api-root"))
        self.assertEqual(root.status_code, 200)
        self.assertIn("products", root.data)
        games = self.api.get(reverse("catalog:api:game-list"))
        self.assertEqual(len(games.data), 4)

    def test_browsable_api_renders_in_html(self):
        response = self.client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LEVELUP")
        self.assertContains(response, "VALORANT")
        self.assertContains(response, "HTTP 200 OK")
        self.assertContains(response, reverse("rest_framework:login"))

    def test_game_filter_returns_six_packages_for_the_selected_game(self):
        response = self.api.get(self.list_url, {"game": "valorant"})
        self.assertEqual(response.data["count"], 6)
        self.assertTrue(all(item["game_slug"] == "valorant" for item in response.data["results"]))

    def test_search_finds_the_credit_unit_or_sku(self):
        response = self.api.get(self.list_url, {"search": "diamonds"})
        self.assertEqual(response.data["count"], 6)
        sample = Product.objects.first()
        response = self.api.get(self.list_url, {"search": sample.sku})
        self.assertEqual(response.data["count"], 1)

    def test_price_filter_and_ordering(self):
        response = self.api.get(self.list_url, {"min_price": "100", "max_price": "500", "ordering": "price"})
        prices = [Decimal(item["price"]) for item in response.data["results"]]
        self.assertTrue(prices)
        self.assertEqual(prices, sorted(prices))
        self.assertTrue(all(100 <= price <= 500 for price in prices))

    def test_availability_and_featured_filters(self):
        self.assertEqual(self.api.get(self.list_url, {"available": "false"}).data["count"], 1)
        self.assertEqual(self.api.get(self.list_url, {"available": "true"}).data["count"], 23)
        self.assertEqual(self.api.get(self.list_url, {"featured": "true"}).data["count"], 4)

    def test_invalid_query_values_return_400(self):
        for params in [
            {"min_price": "invalid"}, {"max_price": "NaN"}, {"min_price": "-1"},
            {"min_price": "500", "max_price": "100"}, {"available": "maybe"},
        ]:
            self.assertEqual(self.api.get(self.list_url, params).status_code, 400)

    def test_pagination_has_stable_distinct_pages(self):
        first = self.api.get(self.list_url, {"page_size": 5, "ordering": "price"})
        second = self.api.get(self.list_url, {"page_size": 5, "ordering": "price", "page": 2})
        self.assertEqual(first.data["count"], 24)
        self.assertEqual(len(first.data["results"]), 5)
        self.assertIsNotNone(first.data["next"])
        ids = {item["id"] for item in first.data["results"]}
        self.assertFalse(ids.intersection(item["id"] for item in second.data["results"]))

    def test_missing_products_and_invalid_pages_have_a_404(self):
        self.assertEqual(self.api.get(reverse("catalog:api:product-detail", args=[999999])).status_code, 404)
        self.assertEqual(self.api.get(self.list_url, {"page": 999999}).status_code, 404)

    def test_inactive_products_are_hidden_from_public_requests(self):
        product = Product.objects.first()
        product.is_active = False
        product.save()
        self.assertEqual(self.api.get(self.list_url).data["count"], 23)
        self.assertEqual(self.api.get(reverse("catalog:api:product-detail", args=[product.pk])).status_code, 404)

    def new_product(self, **changes):
        data = {
            "sku": "TEST-2500", "name": "Test credit package", "game": Game.objects.first().pk,
            "description": "A temporary product for testing.", "credit_amount": 2500,
            "price": "100.50", "stock": 25, "featured": False, "is_active": True,
        }
        data.update(changes)
        return data

    def test_anonymous_users_cannot_change_the_catalog(self):
        self.assertEqual(self.api.post(self.list_url, self.new_product(), format="json").status_code, 403)
        product = Product.objects.first()
        url = reverse("catalog:api:product-detail", args=[product.pk])
        self.assertEqual(self.api.patch(url, {"price": "1.00"}, format="json").status_code, 403)
        self.assertEqual(self.api.delete(url).status_code, 403)
        self.assertEqual(Product.objects.count(), 24)

    def test_regular_accounts_cannot_write_products(self):
        self.api.force_authenticate(self.regular)
        self.assertEqual(self.api.post(self.list_url, self.new_product(), format="json").status_code, 403)

    def test_staff_can_create_update_and_delete_a_product(self):
        self.api.force_authenticate(self.staff)
        response = self.api.post(self.list_url, self.new_product(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        url = reverse("catalog:api:product-detail", args=[response.data["id"]])
        replacement = self.api.put(url, self.new_product(name="Replaced credit package", price="110.00"), format="json")
        self.assertEqual(replacement.status_code, 200, replacement.data)
        self.assertEqual(replacement.data["name"], "Replaced credit package")
        self.assertEqual(replacement.data["price"], "110.00")
        updated = self.api.patch(url, {"price": "125.75"}, format="json")
        self.assertEqual(updated.data["price"], "125.75")
        self.assertEqual(self.api.delete(url).status_code, 204)
        self.assertEqual(Product.objects.count(), 24)

    def test_invalid_products_and_duplicate_skus_are_rejected(self):
        self.api.force_authenticate(self.staff)
        for changes in [
            {"price": "-1.00"}, {"credit_amount": 0}, {"game": 999999},
            {"stock": -1}, {"sku": Product.objects.first().sku},
        ]:
            response = self.api.post(self.list_url, self.new_product(**changes), format="json")
            self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(Product.objects.count(), 24)

    def test_old_game_credit_entry_points_open_the_api(self):
        self.assertRedirects(self.client.get(reverse("catalog:index")), self.list_url)
        product = Product.objects.first()
        self.assertEqual(product.get_absolute_url(), reverse("catalog:api:product-detail", args=[product.pk]))
        self.assertRedirects(self.client.get(f"/gamecredits/products/{product.pk}/"), product.get_absolute_url())

    def test_sample_seed_is_repeatable_and_preserves_product_edits(self):
        product = Product.objects.first()
        product.price = Decimal("201.25")
        product.save()
        call_command("seed_products", stdout=StringIO())
        product.refresh_from_db()
        self.assertEqual(product.price, Decimal("201.25"))
        self.assertEqual(Product.objects.count(), 24)

    def test_browsable_api_login_is_available_without_restoring_enrollment_login(self):
        response = self.client.get(reverse("rest_framework:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password")
        self.assertEqual(self.client.get("/login/").status_code, 404)

    def test_games_also_support_staff_crud(self):
        self.api.force_authenticate(self.staff)
        list_url = reverse("catalog:api:game-list")
        payload = {"name": "Test Game", "slug": "test-game", "short_name": "TG", "credit_unit": "Credits"}
        created = self.api.post(list_url, payload, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        url = reverse("catalog:api:game-detail", args=[created.data["id"]])
        replaced = self.api.put(url, {**payload, "name": "Updated Test Game"}, format="json")
        self.assertEqual(replaced.status_code, 200)
        updated = self.api.patch(url, {"credit_unit": "Coins"}, format="json")
        self.assertEqual(updated.data["credit_unit"], "Coins")
        self.assertEqual(self.api.delete(url).status_code, 204)
        self.assertEqual(Game.objects.count(), 4)

    def test_a_game_with_existing_products_cannot_be_deleted(self):
        self.api.force_authenticate(self.staff)
        response = self.api.delete(reverse("catalog:api:game-detail", args=[Game.objects.first().pk]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Game.objects.count(), 4)
        self.assertEqual(Product.objects.count(), 24)

    def test_real_staff_session_can_create_products_with_csrf_protection(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        login_url = reverse("rest_framework:login")
        client.get(login_url)
        response = client.post(login_url, {
            "username": "catalog_test_admin", "password": "Test-Only-2026-Catalog",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value, "next": self.list_url,
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", client.session)
        self.assertEqual(client.post(self.list_url, self.new_product()).status_code, 403)
        response = client.post(self.list_url, self.new_product(), HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 201)
