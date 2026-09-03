# Repair

Multi-domain broken-artifact learning system. Users are presented with deliberately broken artifacts across five domains and must diagnose and fix them. The system tracks mastery per concept using an exponential moving average.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS |
| Backend | FastAPI · Python 3.12+ |
| Database | Supabase Postgres |
| Auth | Supabase Auth (email + Google OAuth) |
| AI | Grok API (`xAI`) |

---

## Project layout

```
repair/
├── frontend/           Next.js 14 app
├── backend/            FastAPI app
└── supabase/
    └── migrations/     SQL migrations
```

---

## Quickstart

### 1 — Supabase project

1. Create a project at [supabase.com](https://supabase.com).
2. In **SQL Editor**, paste and run `supabase/migrations/001_initial_schema.sql`.
3. In **Authentication → Providers**, enable **Email** and **Google**.
   - For Google: create OAuth credentials at [console.cloud.google.com](https://console.cloud.google.com), then paste the Client ID and Secret into Supabase.
   - Set the redirect URL in Google Console to: `https://your-project-ref.supabase.co/auth/v1/callback`

### 2 — Backend

> **Python 3.14 note:** `pydantic-core` doesn't yet have pre-built Windows wheels for Python 3.14. Install **Python 3.13** from [python.org/downloads](https://python.org/downloads) (binary installer available) before proceeding. Python 3.12 binary installers are no longer published.

```powershell
cd backend

# Create a virtual environment with Python 3.13
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env
# Edit .env — fill in SUPABASE_URL, keys, and GROK_API_KEY

# Run
uvicorn main:app --reload --port 8000
```

- Health check: `GET http://localhost:8000/health`
- API docs (debug mode only): `GET http://localhost:8000/docs`

### 3 — Frontend

```powershell
cd frontend

# Configure environment
Copy-Item .env.local.example .env.local
# Edit .env.local — fill in NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY

# Run
npm run dev
```

App runs at `http://localhost:3000`.

---

## Auth flow

```
User visits /dashboard
    │  no session
    ▼
/login  ──email/password──▶  Supabase Auth  ──▶  /dashboard
        ──Google OAuth ──▶  Google  ──▶  /api/auth/callback  ──▶  /dashboard
```

The Next.js middleware refreshes the Supabase JWT on every request. No session → redirected to `/login`. Already logged in → `/login` and `/signup` redirect to `/dashboard`.

---

## Backend API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/api/auth/me` | Current user info (JWT required) |
| `GET` | `/api/artifacts` | List artifacts |
| `GET` | `/api/artifacts/{id}` | Get artifact |
| `GET` | `/api/artifacts/{id}/hint` | Get domain-specific hint |
| `POST` | `/api/attempts` | Submit a fix attempt |
| `GET` | `/api/attempts/my` | Current user's attempts |
| `GET` | `/api/mastery/me` | All mastery scores |
| `GET` | `/api/mastery/me/{concept_id}` | Mastery for a concept |

---

## Domain architecture

Each domain lives in `backend/domains/<slug>/handler.py` and implements `DomainHandler`:

```python
class DomainHandler(ABC):
    domain_slug: str

    def generate_prompt_context(self, artifact) -> str: ...
    def validate_fix(self, artifact, submitted_fix, explanation) -> FixResult: ...
    def render_hint(self, artifact, attempt) -> str: ...
```

To add a new domain:
1. Create `backend/domains/<new_slug>/handler.py` with `class NewHandler(DomainHandler)`.
2. Add one line to `backend/domains/base.py` in `_build_registry()`.

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Service-role key (never expose to browser) |
| `GROK_API_KEY` | xAI Grok API key |
| `ALLOWED_ORIGINS` | JSON array of allowed CORS origins |
| `DEBUG` | `true` enables `/docs` and `/redoc` |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public anon key |
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |
