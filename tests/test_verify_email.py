import re
import time
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail, signing
from django.core.cache import cache

from accounts import verification

User = get_user_model()
GOOD = {
    "email": "a@x.com",
    "nickname": "Ann",
    "password1": "s3cure-Pass-phrase",
    "password2": "s3cure-Pass-phrase",
}


def link_from(message):
    return re.search(r"https?://\S+/verify/[^/\s]+/", message.body).group(0)


def path_of(link):
    return "/" + link.split("/", 3)[3]


def register(client, **over):
    return client.post("/register/", {**GOOD, **over})


@pytest.fixture
def user(db):
    return User.objects.create_user("u@x.com", "U", "pw")


def test_console_backend_configured():
    from config import settings as project_settings

    backend = project_settings.MAILERS["default"]["BACKEND"]
    assert backend == "django.core.mail.backends.console.EmailBackend"


@pytest.mark.django_db
def test_registration_sends_one_email_with_link(client):
    register(client)
    assert len(mail.outbox) == 1
    m = mail.outbox[0]
    assert m.to == ["a@x.com"]
    assert "/verify/" in m.body


@pytest.mark.django_db
def test_failed_registration_sends_nothing(client):
    register(client, email="bad")
    assert mail.outbox == []


@pytest.mark.django_db
def test_valid_link_verifies(client):
    register(client)
    r = client.get(path_of(link_from(mail.outbox[0])))
    assert r.status_code == 200
    html = r.content.decode()
    assert "now verified" in html and 'href="/login/"' in html
    assert User.objects.get().is_email_verified is True


@pytest.mark.django_db
def test_second_open_already_verified(client):
    register(client)
    path = path_of(link_from(mail.outbox[0]))
    client.get(path)
    r = client.get(path)
    assert r.status_code == 200
    assert "already verified" in r.content.decode().lower()
    assert User.objects.get().is_email_verified is True


def test_token_uses_timestamp_signer_with_3_days():
    assert verification.MAX_AGE == 3 * 24 * 3600
    token = verification.make_token(mock.Mock(pk=7))
    assert signing.TimestampSigner(salt=verification.SALT).unsign(token) == "7"
    assert verification.read_user_id(token) == 7


@pytest.mark.django_db
def test_expiry_boundary(client, user):
    token = verification.make_token(user)
    now = time.time()
    with mock.patch("time.time", return_value=now + verification.MAX_AGE - 60):
        assert client.get(f"/verify/{token}/").status_code == 200
    User.objects.update(is_email_verified=False)
    with mock.patch("time.time", return_value=now + verification.MAX_AGE + 60):
        r = client.get(f"/verify/{token}/")
    assert r.status_code == 400
    assert "/verify/resend/" in r.content.decode()
    assert User.objects.get().is_email_verified is False


@pytest.mark.django_db
@pytest.mark.parametrize("bad", ["garbage", "a:b:c", "x" * 500, "%20", "..."])
def test_malformed_token_400(client, bad):
    r = client.get(f"/verify/{bad}/")
    assert r.status_code == 400
    assert "/verify/resend/" in r.content.decode()


@pytest.mark.django_db
def test_tampered_token_400(client, user):
    token = verification.make_token(user)
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    r = client.get(f"/verify/{tampered}/")
    assert r.status_code == 400
    user.refresh_from_db()
    assert not user.is_email_verified


@pytest.mark.django_db
def test_token_with_wrong_salt_or_payload_400(client, user):
    other = signing.TimestampSigner(salt="other")
    mine = signing.TimestampSigner(salt=verification.SALT)
    for token in (other.sign(str(user.pk)), mine.sign("not-a-number"), mine.sign("-1")):
        assert client.get(f"/verify/{token}/").status_code == 400
    user.refresh_from_db()
    assert not user.is_email_verified


@pytest.mark.django_db
def test_token_for_a_cannot_verify_b(client):
    a = User.objects.create_user("a@x.com", "A", "pw")
    b = User.objects.create_user("b@x.com", "B", "pw")
    assert client.get(f"/verify/{verification.make_token(a)}/").status_code == 200
    a.refresh_from_db(), b.refresh_from_db()
    assert a.is_email_verified and not b.is_email_verified
    # editing the uid inside A's token breaks the signature
    _ts, sig = verification.make_token(a).split(":", 1)
    assert client.get(f"/verify/{b.pk}:{sig}/").status_code == 400
    assert not User.objects.get(pk=b.pk).is_email_verified


@pytest.mark.django_db
def test_deleted_user_same_error_page(client, user):
    token = verification.make_token(user)
    garbage = client.get("/verify/garbage/")
    user.delete()
    r = client.get(f"/verify/{token}/")
    assert r.status_code == 400
    assert r.content == garbage.content


def resend(client, email):
    return client.post("/verify/resend/", {"email": email})


def test_resend_form_shown(client):
    r = client.get("/verify/resend/")
    assert r.status_code == 200 and 'name="email"' in r.content.decode()


@pytest.mark.django_db
def test_resend_sends_working_new_link(client, user):
    r = resend(client, "u@x.com")
    assert r.status_code == 200
    assert len(mail.outbox) == 1 and mail.outbox[0].to == ["u@x.com"]
    client.get(path_of(link_from(mail.outbox[0])))
    user.refresh_from_db()
    assert user.is_email_verified


@pytest.mark.django_db
def test_resend_email_case_insensitive(client, user):
    resend(client, " U@X.com ")
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_resend_verified_user_no_email(client, user):
    User.objects.update(is_email_verified=True)
    r = resend(client, "u@x.com")
    assert r.status_code == 200
    assert "already verified" in r.content.decode()
    assert mail.outbox == []


@pytest.mark.django_db
def test_resend_rate_limited_per_60s(client, user):
    resend(client, "u@x.com")
    r = resend(client, "u@x.com")
    assert "wait" in r.content.decode().lower()
    assert len(mail.outbox) == 1
    resend(client, "U@x.com")
    assert len(mail.outbox) == 1
    with mock.patch("time.time", return_value=time.time() + 61):
        resend(client, "u@x.com")
    assert len(mail.outbox) == 2


@pytest.mark.django_db
def test_rate_limit_is_per_user(client, user):
    User.objects.create_user("o@x.com", "O", "pw")
    resend(client, "u@x.com")
    resend(client, "o@x.com")
    assert len(mail.outbox) == 2


@pytest.mark.django_db
def test_unknown_email_indistinguishable(client, user):
    cache.clear()
    known = resend(client, "u@x.com")
    unknown = resend(client, "nobody@x.com")
    assert unknown.status_code == known.status_code == 200
    strip = lambda r: re.sub(
        r"csrfmiddlewaretoken\" value=\"[^\"]+|value=\"[^\"]*\"", "", r.content.decode()
    )
    assert strip(unknown) == strip(known)
    assert len(mail.outbox) == 1
    # the wait message is also identical for unknown addresses
    again_known = resend(client, "u@x.com")
    again_unknown = resend(client, "nobody@x.com")
    assert strip(again_known) == strip(again_unknown)


@pytest.mark.django_db
def test_resend_invalid_email_form_error(client):
    r = resend(client, "nope")
    assert r.status_code == 200 and "email" in r.context["form"].errors
    assert mail.outbox == []


def test_check_email_page_links_to_resend(client):
    assert "/verify/resend/" in client.get("/register/check-email/").content.decode()
