from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse


def page_not_found(request, exception):
    if request.path.startswith(reverse("catalog:index")):
        return JsonResponse({"detail": "Not found."}, status=404)
    return render(request, "404.html", {"page_title": "Page not found"}, status=404)
