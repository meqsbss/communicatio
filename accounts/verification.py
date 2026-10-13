import hashlib

from django.core import signing
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

SALT = "accounts.email-verification"
MAX_AGE = 3 * 24 * 60 * 60  # 3 days
RESEND_COOLDOWN = 60  # seconds


def _signer():
    return signing.TimestampSigner(salt=SALT)


def make_token(user):
    # Compact on purpose: long lines get quoted-printable-wrapped in the console backend.
    return _signer().sign(str(user.pk))


def read_user_id(token):
    """Return the user id, or None if the token is expired/tampered/malformed."""
    try:
        value = _signer().unsign(token, max_age=MAX_AGE)
    except signing.BadSignature:  # includes SignatureExpired
        return None
    return int(value) if value.isdigit() else None


def send_verification_email(request, user):
    link = request.build_absolute_uri(
        reverse("verify_email", kwargs={"token": make_token(user)})
    )
    body = render_to_string(
        "accounts/email/verify.txt",
        {"user": user, "link": link, "days": MAX_AGE // 86400},
    )
    send_mail("Verify your email for .communicatio", body, None, [user.email])


def _cooldown_key(email):
    return "verify-resend:" + hashlib.sha256(email.encode()).hexdigest()


def claim_resend_slot(email):
    """True if a resend is allowed now (and starts the cooldown). Keyed by the
    address, registered or not, so the response never reveals registration."""
    return cache.add(_cooldown_key(email), 1, RESEND_COOLDOWN)
