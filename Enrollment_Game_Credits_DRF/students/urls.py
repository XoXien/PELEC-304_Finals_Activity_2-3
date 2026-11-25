from django.urls import path

from . import views

app_name = "students"
urlpatterns = [
    path("", views.student_list, name="list"),
    path("students/add/", views.student_add, name="add"),
    path("students/<int:pk>/", views.student_detail, name="detail"),
]
