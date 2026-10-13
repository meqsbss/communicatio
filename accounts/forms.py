from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegistrationForm(forms.Form):
    email = forms.EmailField()
    nickname = forms.CharField(max_length=30)  # strips whitespace; blank is rejected
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput, strip=False
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two password fields didn't match.")
        elif p1:
            user = User(email=cleaned.get("email", ""), nickname=cleaned.get("nickname", ""))
            try:
                validate_password(p1, user)
            except forms.ValidationError as e:
                self.add_error("password1", e)
        return cleaned

    def save(self):
        return User.objects.create_user(
            self.cleaned_data["email"],
            self.cleaned_data["nickname"],
            self.cleaned_data["password1"],
        )
