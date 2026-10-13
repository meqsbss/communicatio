# AGENTS.md

## Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file
- `uv run ruff check .` - lint
- `uv run python manage.py runserver` - local server; it defaults `DJANGO_DEBUG=1` so `/static/` is served (set `DJANGO_DEBUG=0` to override; wsgi/asgi never default it)

## Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking
- Server-rendered Django templates with HTMX. No JavaScript framework
- Profile fields are hidden by default. Never expose a profile field that the user has not made public
- Only groups with status `APPROVED` may appear in matching or search results

## Documents

- `_docs/plan.md` - what we are building and what is out of scope
- `_docs/process.md` - how work is organized
- `_docs/task-template.md` - the format of a groomed GitHub issue
- `_docs/team/` - role descriptions (pm.md, software-engineer.md, qa-engineer.md)
- Before writing tests, read `_docs/testing-guidelines.md` if it exists
- For anything touching the UI, read `_docs/design-system.md` if it exists
