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

- `POST /store-weather-data`
- `GET /list-weather-files`
- `GET /weather-file-content/{file}`
- `GET /health`
- Interactive documentation: `/docs`

Date ranges contain at most 31 calendar dates, inclusive. Daily values use the location's timezone via Open-Meteo's `timezone=auto` and Celsius units. Missing values are preserved as JSON `null`.

## Supabase setup

1. Create a project and a private bucket named `weather-data`.
2. Copy `.env.example` to `.env`.
3. Set `STORAGE_BACKEND=supabase`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY`.
4. Never expose the service-role key to the frontend or commit `.env`.

The storage layer is isolated behind a small interface so an approved S3/GCS adapter can replace Supabase without changing the routes.

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
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_BUCKET=weather-data`
- `CORS_ORIGINS=https://your-frontend.vercel.app`

Provider note: the case-study document specifies GCS/S3 and GCP/AWS backend deployment. Supabase/Vercel should be used only after the evaluator accepts the substitutions.
