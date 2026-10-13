from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def htmx_ping(request):
    return HttpResponse("HTMX works")
