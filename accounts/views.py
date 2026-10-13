from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render

from . import verification
from .forms import RegistrationForm, ResendForm

User = get_user_model()


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            verification.send_verification_email(request, user)
            return redirect("check_email")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def check_email(request):
    return render(request, "accounts/check_email.html")


def verify_email(request, token):
    uid = verification.read_user_id(token)
    user = User.objects.filter(pk=uid).first() if uid is not None else None
    if user is None:
        return render(request, "accounts/verify_error.html", status=400)
    if user.is_email_verified:
        return render(request, "accounts/verify_done.html", {"already": True, "login_url": settings.LOGIN_URL})
    user.is_email_verified = True
    user.save(update_fields=["is_email_verified"])
    return render(request, "accounts/verify_done.html", {"already": False, "login_url": settings.LOGIN_URL})


def resend_verification(request):
    context = {}
    if request.method == "POST":
        form = ResendForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            if verification.claim_resend_slot(email):
                user = User.objects.filter(email=email, is_email_verified=False).first()
                if user is not None:
                    verification.send_verification_email(request, user)
                context["sent"] = True
            else:
                context["wait"] = True
    else:
        form = ResendForm()
    context["form"] = form
    return render(request, "accounts/resend.html", context)
