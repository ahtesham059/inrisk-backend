# InRisk Weather API

FastAPI service that validates a historical weather request, fetches daily data from Open-Meteo, stores the full response as JSON, and exposes saved files for the dashboard.

Companion dashboard: https://github.com/ahtesham059/inrisk-frontend

## Run locally

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

Local development defaults to `.data/weather`. Production refuses to start with local storage.

## API

- `POST /auth/login`
- `GET /auth/me`
- `POST /store-weather-data`
- `GET /list-weather-files`
- `GET /weather-file-content/{file}`
- `DELETE /weather-file-content/{file}`
- `GET /health`
- Interactive documentation: `/docs`

Date ranges contain at most 31 calendar dates, inclusive. Daily values use the location's timezone via Open-Meteo's `timezone=auto` and Celsius units. Missing values are preserved as JSON `null`.

## Supabase setup

1. Create a project and a private bucket named `weather-data`.
2. Copy `.env.example` to `.env`.
3. Set `STORAGE_BACKEND=supabase`, `SUPABASE_URL`, and `SUPABASE_SECRET_KEY`.
4. Never expose the service-role key to the frontend or commit `.env`.

The storage layer is isolated behind a small interface so an approved S3/GCS adapter can replace Supabase without changing the routes.

## Demo authentication

All weather endpoints require a short-lived bearer token. Generate a password hash and signing secret locally:

```bash
python -m scripts.generate_auth_config
```

Copy the five generated lines into `.env` locally and into the backend host's environment settings. The script reads the password without echoing it; only its PBKDF2-SHA256 hash is stored. Give the reviewer the username and original password privately. Do not put either the token secret or reviewer password in GitHub.

The default token lifetime is two hours. `MAX_STORED_FILES` rejects new fetches after the configured object count is reached, while existing objects remain readable. `/health` and `/docs` stay public; the three case-study routes require authentication.

## Design and libraries

- **FastAPI and Pydantic** define the API contract, validation, CORS, and error mapping.
- **HTTPX** calls Open-Meteo and the Supabase Storage REST API asynchronously.
- A storage protocol separates routes and weather orchestration from local/Supabase persistence.
- Authentication uses standard-library PBKDF2-SHA256 password hashing and HMAC-SHA256 signed tokens, avoiding a database for this single-reviewer demo.
- **pytest** exercises validation, authentication, orchestration, and error behavior; **Ruff** enforces Python quality checks.

The backend validates Open-Meteo's aligned daily arrays before storage. It lists storage through the provider's paginated listing API and never downloads objects to obtain metadata. A server-only Supabase secret keeps the bucket private.

## Checks

```bash
pytest
ruff check .
```

## Deploy on Vercel

Import this repository as a Vercel project and add:

- `APP_ENVIRONMENT=production`
- `STORAGE_BACKEND=supabase`
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `SUPABASE_BUCKET=weather-data`
- `CORS_ORIGINS=https://your-frontend.vercel.app`
- `AUTH_USERNAME`
- `AUTH_PASSWORD_HASH`
- `AUTH_TOKEN_SECRET`
- `AUTH_TOKEN_TTL_MINUTES=120`
- `MAX_STORED_FILES=100`

Provider note: the case-study document specifies GCS/S3 and GCP/AWS backend deployment. Supabase/Vercel should be used only after the evaluator accepts the substitutions.
