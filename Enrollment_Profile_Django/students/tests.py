from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Classroom, Student


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"])
class EnrollmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.student = Student.objects.get(student_id="024A-100001")

    def test_directory_and_every_student_profile_open_without_an_account(self):
        client = Client(enforce_csrf_checks=True)
        self.assertContains(client.get(reverse("students:list")), "Student directory")
        for student in Student.objects.all():
            self.assertContains(client.get(student.get_absolute_url()), student.email)
        self.assertNotIn("_auth_user_id", client.session)

    def test_profile_pages_have_no_signin_or_signout_controls(self):
        for url in [reverse("students:list"), self.student.get_absolute_url()]:
            response = self.client.get(url)
            for removed_text in ["Sign in", "Sign out", "Admin portal", "Administrator"]:
                self.assertNotContains(response, removed_text)

    def test_custom_authentication_pages_are_removed(self):
        self.assertEqual(self.client.get("/login/").status_code, 404)
        self.assertEqual(self.client.get("/logout/").status_code, 404)

    def test_each_profile_displays_the_selected_students_information(self):
        response = self.client.get(self.student.get_absolute_url())
        for value in [self.student.full_name, self.student.email, self.student.guardian_name,
                      self.student.secondary_school, self.student.classroom.program_name,
                      self.student.student_id]:
            self.assertContains(response, value)
        other = Student.objects.get(student_id="024A-100002")
        response = self.client.get(other.get_absolute_url())
        self.assertContains(response, other.email)
        self.assertNotContains(response, self.student.email)

    def test_full_name_and_student_id_search(self):
        for query in ["Aurelia Mendoza", "024A-100001"]:
            response = self.client.get(reverse("students:list"), {"q": query})
            self.assertEqual(response.context["page_obj"].paginator.count, 1)
            self.assertContains(response, self.student.email)

    def test_class_and_status_filters_work_together(self):
        room = Classroom.objects.get(year_level=2, section="A")
        response = self.client.get(reverse("students:list"), {"classroom": room.pk, "status": "pending"})
        results = list(response.context["page_obj"])
        self.assertEqual([item.student_id for item in results], ["024A-100003"])

    def test_pagination_and_filter_query_preservation(self):
        response = self.client.get(reverse("students:list"), {"q": "example.com"})
        self.assertEqual(len(response.context["page_obj"]), 8)
        self.assertContains(response, "q=example.com&amp;page=2")
        second = self.client.get(reverse("students:list"), {"q": "example.com", "page": 2})
        self.assertEqual(len(second.context["page_obj"]), 4)
        first_ids = {item.pk for item in response.context["page_obj"]}
        self.assertFalse(first_ids.intersection(item.pk for item in second.context["page_obj"]))

    def test_invalid_filters_and_pages_do_not_crash(self):
        response = self.client.get(reverse("students:list"), {
            "classroom": "9" * 200, "status": "invalid", "page": "not-a-number",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 12)
        response = self.client.get(reverse("students:list"), {"q": "no-such-student"})
        self.assertContains(response, "No students found")

    def test_untrusted_search_text_is_escaped(self):
        response = self.client.get(reverse("students:list"), {"q": '<script>alert("x")</script>'})
        self.assertNotContains(response, '<script>alert("x")</script>')
        self.assertContains(response, "&lt;script&gt;")

    def test_profile_pages_display_fresh_information(self):
        for url in [reverse("students:list"), self.student.get_absolute_url()]:
            self.assertIn("no-store", self.client.get(url)["Cache-Control"])

    def test_missing_student_has_a_404_and_empty_optional_fields_render(self):
        self.assertEqual(self.client.get(reverse("students:detail", kwargs={"pk": 999999})).status_code, 404)
        student = Student.objects.create(
            student_id="024A-999999", first_name="Minimal", last_name="Example",
            classroom=self.student.classroom,
        )
        self.assertContains(self.client.get(student.get_absolute_url()), "Minimal Example")

    def test_sample_data_can_be_loaded_again_without_overwriting_edits(self):
        self.student.first_name = "Updated"
        self.student.save()
        call_command("seed_demo", stdout=StringIO())
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, "Updated")
        self.assertEqual(Student.objects.count(), 12)
        self.assertEqual(Classroom.objects.count(), 3)

    def test_django_administration_requires_its_own_account(self):
        response = self.client.get(reverse("admin:students_student_add"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("admin:login") + "?next="))

    def student_payload(self, **changes):
        data = {
            "student_id": "024A-200001", "classroom": str(self.student.classroom.pk),
            "status": "enrolled", "admission_type": "regular", "first_name": "Alessia",
            "last_name": "Rosales", "middle_initial": "m", "sex": "female",
            "email": "alessia.rosales@example.com", "date_of_birth": "2006-03-15",
            "address": "Sample student address", "guardian_name": "Sample Guardian",
            "secondary_school": "Sample School", "graduation_year": "2024",
        }
        data.update(changes)
        return data

    def test_add_student_form_opens_without_an_account_and_creates_nothing_on_get(self):
        response = self.client.get(reverse("students:add"))
        self.assertContains(response, "Save student")
        self.assertContains(response, "csrfmiddlewaretoken")
        for name in ["student_id", "first_name", "guardian_name", "secondary_school"]:
            self.assertContains(response, f'name="{name}"')
        self.assertEqual(Student.objects.count(), 12)

    def test_new_student_is_saved_and_their_profile_opens_with_a_success_message(self):
        response = self.client.post(reverse("students:add"), self.student_payload(), follow=True)
        student = Student.objects.get(student_id="024A-200001")
        self.assertEqual(response.redirect_chain, [(student.get_absolute_url(), 302)])
        self.assertContains(response, "Student added successfully.")
        self.assertContains(response, "Alessia M. Rosales")
        self.assertContains(response, student.guardian_name)
        self.assertContains(response, student.secondary_school)
        self.assertEqual(Student.objects.count(), 13)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_optional_student_details_can_be_left_blank(self):
        data = {key: value for key, value in self.student_payload().items() if key in {
            "student_id", "first_name", "last_name", "classroom", "status", "admission_type", "sex",
        }}
        response = self.client.post(reverse("students:add"), data)
        student = Student.objects.get(student_id=data["student_id"])
        self.assertRedirects(response, student.get_absolute_url())
        self.assertIsNone(student.date_of_birth)
        self.assertEqual(student.guardian_name, "")

    def test_duplicate_student_id_is_rejected_without_overwriting_the_original(self):
        original_name = self.student.first_name
        response = self.client.post(reverse("students:add"), self.student_payload(
            student_id=self.student.student_id.lower(),
        ))
        self.assertEqual(response.status_code, 200)
        self.assertIn("student_id", response.context["form"].errors)
        self.assertContains(response, "A student with this ID already exists.")
        self.assertContains(response, 'value="Alessia"')
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, original_name)
        self.assertEqual(Student.objects.count(), 12)

    def test_invalid_details_show_errors_and_preserve_entered_values(self):
        response = self.client.post(reverse("students:add"), self.student_payload(
            first_name="", email="invalid-email", classroom="999999",
            date_of_birth=(timezone.localdate() + timedelta(days=1)).isoformat(),
        ))
        self.assertEqual(response.status_code, 200)
        for field in ["first_name", "email", "classroom", "date_of_birth"]:
            self.assertIn(field, response.context["form"].errors)
        self.assertContains(response, 'value="Rosales"')
        self.assertEqual(Student.objects.count(), 12)

    def test_student_creation_requires_a_valid_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("students:add"))
        self.assertEqual(client.post(reverse("students:add"), self.student_payload()).status_code, 403)
        token = client.cookies["csrftoken"].value
        response = client.post(reverse("students:add"), {
            **self.student_payload(), "csrfmiddlewaretoken": token,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Student.objects.count(), 13)
