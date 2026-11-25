from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import StudentForm
from .models import Classroom, Student


@never_cache
def student_list(request):
    all_students = Student.objects.all()
    students = all_students.select_related("classroom")
    query = request.GET.get("q", "").strip()[:150]
    class_id = request.GET.get("classroom", "")
    status = request.GET.get("status", "")

    # Only use class IDs returned by our own class list.
    classrooms = list(Classroom.objects.all())
    selected_class = next((room for room in classrooms if str(room.pk) == class_id), None)
    if selected_class:
        students = students.filter(classroom=selected_class)
    else:
        class_id = ""
    if status in Student.Status.values:
        students = students.filter(status=status)
    else:
        status = ""
    if query:
        for word in query.split():
            students = students.filter(
                Q(first_name__icontains=word) | Q(last_name__icontains=word)
                | Q(middle_initial__icontains=word) | Q(student_id__icontains=word)
                | Q(email__icontains=word)
            )

    page = Paginator(students, 8).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "students/list.html", {
        "page_obj": page,
        "query": query,
        "classrooms": classrooms,
        "class_id": class_id,
        "selected_class": selected_class,
        "status": status,
        "status_choices": Student.Status.choices,
        "filter_query": params.urlencode(),
        "total_students": all_students.count(),
        "enrolled_count": all_students.filter(status=Student.Status.ENROLLED).count(),
        "pending_count": all_students.filter(status=Student.Status.PENDING).count(),
        "classroom_count": len(classrooms),
        "page_title": "Student directory",
    })


@never_cache
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related("classroom"), pk=pk)
    classmates = Student.objects.filter(classroom=student.classroom).exclude(pk=pk)[:4]
    return render(request, "students/detail.html", {
        "student": student, "classmates": classmates, "page_title": "Student profile",
    })


@never_cache
@require_http_methods(["GET", "POST"])
def student_add(request):
    """Create a record, then open the new student's profile."""
    form = StudentForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        messages.success(request, "Student added successfully.")
        return redirect(student)
    return render(request, "students/form.html", {
        "form": form, "page_title": "Add student",
    })
