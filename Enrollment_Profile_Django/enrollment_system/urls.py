from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Enrollment Administration"
admin.site.site_title = "Enrollment Admin"
admin.site.index_title = "Manage classes and student records"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("students.urls")),
]
