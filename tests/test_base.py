import re
import types
from pathlib import Path

import pytest
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.template import engines
from django.test import RequestFactory
from django.urls import NoReverseMatch, path, reverse

from core import urls as core_urls

ROOT = Path(__file__).resolve().parent.parent


def render_base(template_string="", messages_list=()):
    request = RequestFactory().get("/")
    request.session = {}
    request._messages = FallbackStorage(request)
    for level, text in messages_list:
        messages.add_message(request, level, text)
    tpl = engines["django"].from_string('{% extends "base.html" %}' + template_string)
    return tpl.render({}, request)


def test_home_extends_base(client):
    html = client.get("/").content.decode()
    assert 'class="site-header"' in html
    assert "<h1>.communicatio</h1>" in html


def test_viewport_meta(client):
    html = client.get("/").content.decode()
    assert (
        '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    )


def test_htmx_pinned_local_file_and_element(client):
    html = client.get("/").content.decode()
    assert "/static/js/htmx.min.js" in html
    js = (ROOT / "static/js/htmx.min.js").read_text()
    assert 'version:"2.0.4"' in js
    assert 'hx-get="/htmx-ping/"' in html
    response = client.get("/htmx-ping/")
    assert response.status_code == 200
    assert response.content == b"HTMX works"


def test_nav_only_home_when_no_login_url(client):
    html = client.get("/").content.decode()
    nav = re.search(r"<nav.*?</nav>", html, re.DOTALL).group(0)
    assert ">Home</a>" in nav
    assert "Register" not in nav and "Log in" not in nav
    with pytest.raises(NoReverseMatch):
        reverse("login")


def test_css_single_file_responsive_no_framework():
    css_files = list((ROOT / "static/css").glob("*"))
    assert [f.name for f in css_files] == ["site.css"]
    css = css_files[0].read_text()
    assert "flex-direction: column" in css
    assert "@media (min-width: 768px)" in css
    assert "flex-direction: row" in css


def test_messages_rendered_with_distinct_styles():
    html = render_base(
        messages_list=[
            (messages.SUCCESS, "ok"),
            (messages.ERROR, "bad"),
            (messages.INFO, "fyi"),
        ]
    )
    assert 'class="message message-success"' in html
    assert 'class="message message-error"' in html
    assert 'class="message message-info"' in html
    assert html.index('class="messages"') < html.index("<main") + 200
    css = (ROOT / "static/css/site.css").read_text()
    for tag in ("success", "error", "info"):
        assert f".message-{tag}" in css


def test_messages_above_content():
    html = render_base(
        "{% block content %}CONTENT{% endblock %}", [(messages.INFO, "hello")]
    )
    assert html.index("hello") < html.index("CONTENT")


def test_messages_disappear_on_next_request(client, settings):
    settings.MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

    def add(request):
        messages.success(request, "flash once")
        return HttpResponse("added")

    urlconf = types.ModuleType("tmp_urlconf")
    urlconf.urlpatterns = [path("add/", add), *core_urls.urlpatterns]
    settings.ROOT_URLCONF = urlconf
    client.get("/add/")
    assert "flash once" in client.get("/").content.decode()
    assert "flash once" not in client.get("/").content.decode()


def test_message_html_is_escaped():
    html = render_base(messages_list=[(messages.INFO, "<b>x</b>")])
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert "<b>x</b>" not in html


def test_page_without_content_block_renders():
    html = render_base()
    assert "<main" in html
