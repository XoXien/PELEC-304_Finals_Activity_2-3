from django.contrib import admin
from django.urls import include, path
from catalog.admin import credits_admin_site

admin.site.site_header = "Enrollment Administration"
admin.site.site_title = "Enrollment Admin"
admin.site.index_title = "Manage classes and student records"

handler404 = "enrollment_system.views.page_not_found"

urlpatterns = [
    path("gamecredits/admin/", credits_admin_site.urls),
    path("gamecredits/", include("catalog.urls")),
    path("admin/", admin.site.urls),
    path("", include("students.urls")),
]
