from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Classroom(models.Model):
    """A class groups students by program, year, section, and school year."""

    program = models.CharField(max_length=20, default="BSIT")
    program_name = models.CharField(
        max_length=140, default="Bachelor of Science in Information Technology"
    )
    year_level = models.PositiveSmallIntegerField(
        choices=[(1, "1st year"), (2, "2nd year"), (3, "3rd year"), (4, "4th year")]
    )
    section = models.CharField(max_length=10)
    school_year = models.CharField(max_length=20, default="2026-2027")
    semester = models.CharField(
        max_length=12,
        choices=[("first", "1st semester"), ("second", "2nd semester"), ("summer", "Summer")],
        default="first",
    )

    class Meta:
        ordering = ["program", "year_level", "section", "school_year", "semester"]
        constraints = [
            models.UniqueConstraint(
                fields=["program", "year_level", "section", "school_year", "semester"],
                name="unique_class_per_term",
            )
        ]

    @property
    def code(self):
        return f"{self.program} {self.year_level}{self.section}"

    def __str__(self):
        return f"{self.code} · {self.school_year} · {self.get_semester_display()}"


class Student(models.Model):
    class Status(models.TextChoices):
        ENROLLED = "enrolled", "Enrolled"
        PENDING = "pending", "Pending"
        INACTIVE = "inactive", "Inactive"

    student_id = models.CharField("Student ID", max_length=25, unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    middle_initial = models.CharField(max_length=3, blank=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.PROTECT, related_name="students")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ENROLLED)
    admission_type = models.CharField(
        max_length=15,
        choices=[("regular", "Regular"), ("transferee", "Transferee"), ("returnee", "Returnee")],
        default="regular",
    )
    sex = models.CharField(
        max_length=15,
        choices=[("female", "Female"), ("male", "Male"), ("unspecified", "Not specified")],
        default="unspecified",
    )
    date_of_birth = models.DateField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=150, blank=True)
    nationality = models.CharField(max_length=60, blank=True)
    civil_status = models.CharField(
        max_length=15,
        choices=[("single", "Single"), ("married", "Married"), ("other", "Other")],
        blank=True,
    )
    email = models.EmailField(blank=True)
    mobile_number = models.CharField(max_length=25, blank=True)
    address = models.TextField("Home address", blank=True)
    guardian_name = models.CharField(max_length=140, blank=True)
    guardian_relationship = models.CharField(max_length=50, blank=True)
    guardian_contact = models.CharField(max_length=25, blank=True)
    guardian_address = models.TextField(blank=True)
    secondary_school = models.CharField("Senior high school", max_length=180, blank=True)
    strand = models.CharField("Senior high school strand", max_length=100, blank=True)
    graduation_year = models.PositiveSmallIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1900), MaxValueValidator(2100)]
    )
    previous_school = models.CharField("Previous college (if applicable)", max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name", "pk"]

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"

    def clean(self):
        if self.date_of_birth and self.date_of_birth > timezone.localdate():
            raise ValidationError({"date_of_birth": "Date of birth cannot be in the future."})

    @property
    def full_name(self):
        middle = self.middle_initial.strip().rstrip(".")
        return " ".join(part for part in [self.first_name, f"{middle}." if middle else "", self.last_name] if part)

    @property
    def initials(self):
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()

    @property
    def avatar_color(self):
        return ["mint", "lilac", "peach", "blue"][self.pk % 4 if self.pk else 0]

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def get_absolute_url(self):
        return reverse("students:detail", kwargs={"pk": self.pk})
