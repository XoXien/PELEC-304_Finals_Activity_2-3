from django.shortcuts import render
from django.urls import reverse


def page_not_found(request, exception):
    template = "credits/not_found.html" if request.path.startswith(reverse("catalog:store")) else "404.html"
    return render(request, template, {"page_title": "Page not found"}, status=404)
