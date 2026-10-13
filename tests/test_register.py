import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()
GOOD = {
    "email": "a@x.com",
    "nickname": "Ann",
    "password1": "s3cure-Pass-phrase",
    "password2": "s3cure-Pass-phrase",
}


def post(client, **over):
    return client.post("/register/", {**GOOD, **over})


@pytest.mark.django_db
def test_model_setup(settings):
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert User.USERNAME_FIELD == "email"
    u = User.objects.create_user("b@x.com", "Bob", "pw")
    assert u.is_email_verified is False and u.is_active and not u.is_staff
    assert u.date_joined


@pytest.mark.django_db
def test_createsuperuser_with_email_and_nickname():
    call_command(
        "createsuperuser", interactive=False, email="Root@x.com", nickname="Root"
    )
    u = User.objects.get(email="root@x.com")
    assert u.is_superuser and u.is_staff and u.nickname == "Root"


def test_form_shown(client):
    r = client.get("/register/")
    assert r.status_code == 200
    html = r.content.decode()
    for name in ("email", "nickname", "password1", "password2"):
        assert f'name="{name}"' in html


@pytest.mark.django_db
def test_valid_registration(client):
    r = post(client)
    assert r.status_code == 302
    assert r.url == "/register/check-email/"
    u = User.objects.get(email="a@x.com")
    assert u.is_email_verified is False
    assert u.password != GOOD["password1"] and u.check_password(GOOD["password1"])
    assert client.get(r.url).status_code == 200


@pytest.mark.django_db
def test_email_stored_lowercase(client):
    post(client, email="MiXed@X.com")
    assert User.objects.get().email == "mixed@x.com"


@pytest.mark.django_db
@pytest.mark.parametrize("dup", ["a@x.com", "A@x.com"])
def test_duplicate_email_rejected(client, dup):
    User.objects.create_user("a@x.com", "Old", "pw")
    r = post(client, email=dup)
    assert r.status_code == 200
    assert "A user with this email already exists" in r.content.decode()
    assert User.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "over,field",
    [
        ({"email": "not-an-email"}, "email"),
        ({"nickname": ""}, "nickname"),
        ({"nickname": "x" * 31}, "nickname"),
        ({"password2": "different-Pass-1"}, "password2"),
    ],
)
def test_invalid_input_field_errors(client, over, field):
    r = post(client, **over)
    assert r.status_code == 200
    assert field in r.context["form"].errors
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_nickname_30_ok(client):
    assert post(client, nickname="x" * 30).status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize("pw", ["short1A", "password123", "1234567890123"])
def test_weak_passwords_rejected(client, pw):
    r = post(client, password1=pw, password2=pw)
    assert r.status_code == 200
    assert "password1" in r.context["form"].errors
    assert User.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("nick", ["   ", "\t\n"])
def test_whitespace_nickname_rejected(client, nick):
    r = post(client, nickname=nick)
    assert "nickname" in r.context["form"].errors
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_nickname_trimmed(client):
    post(client, nickname="  Ann  ")
    assert User.objects.get().nickname == "Ann"


@pytest.mark.django_db
def test_nickname_not_unique(client):
    User.objects.create_user("o@x.com", "Ann", "pw")
    assert post(client).status_code == 302
    assert User.objects.filter(nickname="Ann").count() == 2


@pytest.mark.django_db
def test_logged_in_user_redirected_home(client):
    u = User.objects.create_user("l@x.com", "L", "pw")
    client.force_login(u)
    r = client.get("/register/")
    assert r.status_code == 302 and r.url == "/"
    assert client.post("/register/", GOOD).status_code == 302
    assert User.objects.count() == 1
