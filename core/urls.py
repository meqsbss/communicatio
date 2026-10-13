from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("htmx-ping/", views.htmx_ping, name="htmx_ping"),
]
