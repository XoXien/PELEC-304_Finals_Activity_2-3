from io import StringIO

from django.core.management import call_command
from django.db import connections
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from catalog.models import Product
from students.models import Student


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"])
class CombinedDeploymentTests(TestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def test_both_sites_and_the_product_api_work_from_the_same_project(self):
        self.assertContains(self.client.get("/"), "Student directory")
        self.assertContains(self.client.get("/gamecredits/"), "LEVELUP")
        response = APIClient().get(reverse("catalog:api:product-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 24)
        self.assertTrue(all("/gamecredits/api/products/" in item["url"] for item in response.data["results"]))

    def test_each_application_uses_its_own_database(self):
        enrollment_tables = connections["default"].introspection.table_names()
        credit_tables = connections["gamecredits"].introspection.table_names()
        self.assertIn("students_student", enrollment_tables)
        self.assertNotIn("catalog_product", enrollment_tables)
        self.assertIn("catalog_product", credit_tables)
        self.assertNotIn("students_student", credit_tables)
        self.assertEqual(Student.objects.count(), 12)
        self.assertEqual(Product.objects.count(), 24)

    def test_adding_a_student_does_not_modify_the_game_credit_catalog(self):
        example = Student.objects.first()
        response = self.client.post(reverse("students:add"), {
            "student_id": "024A-900001", "first_name": "Combined", "last_name": "Example",
            "classroom": example.classroom_id, "status": "enrolled",
            "admission_type": "regular", "sex": "unspecified",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Student.objects.count(), 13)
        self.assertEqual(Product.objects.count(), 24)

    @override_settings(DEBUG=False)
    def test_missing_game_credit_pages_keep_the_game_credit_navigation(self):
        response = self.client.get("/gamecredits/products/999999/")
        self.assertContains(response, "Back to game credits", status_code=404)
        self.assertNotContains(response, 'href="/"', status_code=404)
