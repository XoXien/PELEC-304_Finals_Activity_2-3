from django import forms
from django.utils import timezone

from .models import Student


class StudentForm(forms.ModelForm):
    """Collect the information displayed in a student's profile."""

    class Meta:
        model = Student
        fields = [
            "student_id", "classroom", "status", "admission_type",
            "first_name", "last_name", "middle_initial", "sex", "date_of_birth",
            "place_of_birth", "nationality", "civil_status", "email", "mobile_number", "address",
            "guardian_name", "guardian_relationship", "guardian_contact", "guardian_address",
            "secondary_school", "strand", "graduation_year", "previous_school",
        ]
        labels = {
            "classroom": "Class", "status": "Enrollment status",
            "email": "Email address", "guardian_contact": "Guardian's contact number",
        }
        widgets = {
            "date_of_birth": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "guardian_address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "student_id": "e.g. 024A-123456", "first_name": "First name",
            "last_name": "Last name", "middle_initial": "e.g. C",
            "email": "e.g. student@example.com", "mobile_number": "Mobile number",
            "place_of_birth": "City / municipality, province", "nationality": "e.g. Filipino",
            "address": "House / street, barangay, city, province",
            "guardian_name": "Guardian's full name", "guardian_relationship": "e.g. Parent",
            "guardian_contact": "Contact number", "guardian_address": "Guardian's home address",
            "secondary_school": "Name of senior high school", "strand": "e.g. STEM or ICT",
            "graduation_year": "e.g. 2024", "previous_school": "Previous college, if applicable",
        }
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "student-input"
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]
        self.fields["student_id"].widget.attrs.update({"autofocus": True, "autocomplete": "off"})
        self.fields["date_of_birth"].widget.attrs["max"] = timezone.localdate().isoformat()
        self.fields["graduation_year"].widget.attrs.update({"min": 1900, "max": 2100})
        self.fields["middle_initial"].widget.attrs["autocapitalize"] = "characters"
        self.fields["mobile_number"].widget.attrs["type"] = "tel"
        self.fields["guardian_contact"].widget.attrs["type"] = "tel"
        self.fields["classroom"].empty_label = "Select a class"

    def clean_student_id(self):
        value = self.cleaned_data["student_id"].upper()
        if Student.objects.filter(student_id__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A student with this ID already exists.")
        return value

    def clean_middle_initial(self):
        return self.cleaned_data["middle_initial"].upper().rstrip(".")

    @property
    def sections(self):
        groups = [
            ("Enrollment details", "Assign the student to a class and set their enrollment status.",
             ["student_id", "classroom", "status", "admission_type"]),
            ("Personal information", "Add the student's name and contact information.",
             ["first_name", "last_name", "middle_initial", "sex", "date_of_birth",
              "place_of_birth", "nationality", "civil_status", "email", "mobile_number", "address"]),
            ("Family & guardian", "Provide the details of the student's parent or guardian.",
             ["guardian_name", "guardian_relationship", "guardian_contact", "guardian_address"]),
            ("Educational background", "Record the student's previous school and strand.",
             ["secondary_school", "strand", "graduation_year", "previous_school"]),
        ]
        return [
            {"title": title, "description": description, "fields": [self[name] for name in fields]}
            for title, description, fields in groups
        ]
