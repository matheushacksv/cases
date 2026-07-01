# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Django 6 API backend (django-ninja) for a sales-consultancy **case library**: users submit cases (`name`, free-text `niche`, `result`) and the app groups them by **semantic niche similarity** so they can be browsed/searched. Python 3.13, managed with **uv**. PostgreSQL 16 + **pgvector** via psycopg 3. Config from `backend/.env` with `python-decouple`. UI language/timezone are `pt-BR` / `America/Sao_Paulo`.

Repo root holds only `docker-compose.yml`; all app code is under `backend/`. Run commands from `backend/`.

## Commands

```bash
# from backend/
uv sync                              # install deps into .venv
uv run manage.py runserver           # dev server (Swagger at /api/docs)
uv run manage.py makemigrations      # create migrations
uv run manage.py migrate             # apply migrations
uv run manage.py createsuperuser     # prompts for email (no username)
uv run manage.py shell               # REPL — used to calibrate THRESHOLD against real niches
uv run manage.py test                # all tests
uv run manage.py test apps.cases     # one app
uv run manage.py test apps.cases.tests.ClassName.test_method  # single test

# Postgres (compose starts the DB only, not the app)
docker compose up -d db
```

Required `.env` keys: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `POSTGRES_DB|USER|PASSWORD|HOST|PORT`, **`OPENAI_API_KEY`**.

## Architecture

Layered, request flows top-down — keep each layer to its job:

- `api/api.py` — single `NinjaAPI`, mounted at `/api/` in `core/urls.py`. Adds routers, nothing else.
- `api/endpoints/<area>.py` — thin `Router`s. Parse/return only; delegate all logic to services. Responses use explicit codes (`response={201: ...}`, `Status(201, ...)`).
- `apps/<app>/services.py` — **all business logic lives here.** Endpoints and admin call into it.
- `apps/<app>/schemas.py` — django-ninja DTOs, suffixed `*DTO` (`CaseInDTO`, `CaseOutDTO`, ...). Plain `Schema`, not `ModelSchema`; for computed/related fields use a `resolve_<field>` staticmethod, not `Field(alias='a.b')` (the dotted alias drops into the ORM factory and raises `ConfigError`).
- `apps/<app>/models.py` — `core/` holds Django project config. Apps are namespaced: reference as `apps.<name>` in `INSTALLED_APPS`/migrations.

### Semantic niche grouping (the core mechanism)

`apps/cases/`:
- `embeddings.py` — `embed(text)` → OpenAI `text-embedding-3-small` (**1536 dims**, already L2-normalized so cosine works directly). `_client` and `embed` are `lru_cache`d, so repeat niches don't re-hit the API.
- `services.assign_segment(niche)` — embeds the niche, finds the nearest `Segment` by `CosineDistance` (pgvector, computed in SQL), and **greedily** assigns it if distance ≤ `THRESHOLD`, else creates a new `Segment` seeded with this vector. Online greedy clustering; `Segment.centroid` is just the first member's vector.
- `services.search_case(q)` — embeds the query, returns cases ordered by `CosineDistance` on `niche_vec`. This is the semantic "consulta facilitada".
- Both `Segment.centroid` and `Case.niche_vec` are `VectorField(dimensions=1536)`.

**`THRESHOLD` (services.py) is a calibration knob, not a constant** — embedding distances are noisy on short human niche text and there is no global threshold that perfectly separates synonyms from cross-domain pairs. Current value `0.45` is tuned to favor *fragmentation* (a concept splits into two segments — recoverable via admin merge) over *false merges* (unrelated cases in one segment — misleading). Re-measure in `shell` if you change the embedding model. Known ceiling: greedy + fixed threshold fragments noisy slang; upgrade path is admin merge, then a seeded taxonomy if it gets messy.

## Gotchas

- **pgvector needs the right image + a migration op.** `docker-compose.yml` must use `pgvector/pgvector:pg16` (stock `postgres` lacks the extension). The first migration (`cases/0001`) runs `VectorExtension()` as its first operation to `CREATE EXTENSION vector` before any `VectorField` table. Changing vector dimensions requires deleting existing rows first (pgvector rejects an `AlterField` to a different dim with data present).
- **The write path depends on OpenAI.** `create_case` wraps `assign_segment` and returns `503` on `OpenAIError` rather than persisting a half-classified case. A case insert fails if the OpenAI API is down.
- `python-decouple`'s `config()` is untyped and returns a union pyright reads as possibly `bool`; cast at the call site (`cast=bool` for `DEBUG`, `str(config('OPENAI_API_KEY'))` for the key). `DEBUG = config('DEBUG')` in `settings.py` still lacks `cast=bool` — any non-empty string (incl. `"False"`) is truthy.
- pyright can't see Django's runtime-injected `.objects` (fixed repo-wide by the `django-types` dev dep) nor `.annotate()` fields like `dist`/`d` (needs `# type: ignore[attr-defined]` at the access site).
