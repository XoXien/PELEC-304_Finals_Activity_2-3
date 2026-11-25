from django.contrib import admin

from .models import Classroom, Student


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ["code", "program_name", "school_year", "semester"]
    list_filter = ["program", "year_level", "school_year", "semester"]
    search_fields = ["program", "section", "program_name"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["student_id", "full_name", "classroom", "status", "email"]
    list_filter = ["classroom", "status", "admission_type"]
    search_fields = ["student_id", "first_name", "last_name", "email"]
    list_select_related = ["classroom"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        ("Enrollment information", {"fields": ["student_id", "classroom", "status", "admission_type"]}),
        ("Personal information", {"fields": [
            "first_name", "last_name", "middle_initial", "sex", "date_of_birth",
            "place_of_birth", "nationality", "civil_status", "email", "mobile_number", "address",
        ]}),
        ("Family and guardian", {"fields": [
            "guardian_name", "guardian_relationship", "guardian_contact", "guardian_address",
        ]}),
        ("Educational background", {"fields": [
            "secondary_school", "strand", "graduation_year", "previous_school",
        ]}),
        ("Record history", {"fields": ["created_at", "updated_at"]}),
    ]
