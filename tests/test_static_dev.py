import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def static_urls():
    base = (ROOT / "templates" / "base.html").read_text()
    paths = re.findall(r"\{%\s*static\s+'([^']+)'\s*%\}", base)
    assert paths
    return ["/static/" + p for p in paths]


def fetch(port, url):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{url}") as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def run_server(env_overrides):
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_DEBUG"}
    env.update(env_overrides)
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return proc, port
        except OSError:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("server did not start")


def test_default_runserver_serves_static_files():
    proc, port = run_server({})
    try:
        for url in static_urls():
            assert fetch(port, url) == 200, url
    finally:
        proc.terminate()
        proc.wait()


def test_explicit_debug_off_does_not_serve_static():
    proc, port = run_server({"DJANGO_DEBUG": "0"})
    try:
        assert fetch(port, static_urls()[0]) == 404
    finally:
        proc.terminate()
        proc.wait()


def test_production_default_debug_is_off():
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_DEBUG"}
    code = (
        "import os;os.environ['DJANGO_SETTINGS_MODULE']='config.settings';"
        "from django.conf import settings;print(settings.DEBUG)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        check=False, cwd=ROOT, env=env, capture_output=True, text=True,
    )
    assert out.stdout.strip() == "False"
