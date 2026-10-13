from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("register/check-email/", views.check_email, name="check_email"),
    path("verify/resend/", views.resend_verification, name="resend_verification"),
    path("verify/<str:token>/", views.verify_email, name="verify_email"),
]
