# ChemTutor Backend

AI-powered chemistry tutoring platform with adaptive scaffolding, mastery tracking, and B2B multi-tenant classroom management.

## Quick Start

```bash
# 1. Clone and copy env
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL and one AI provider key

# 2. Run with Docker (recommended)
docker compose up --build

# 3. Seed the curriculum
docker compose exec app python -m scripts.seed

# 4. Create the superadmin
docker compose exec app python -m scripts.bootstrap_superadmin
```

The API is at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

## Without Docker

```bash
# Python 3.12+ required
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Run migrations + start
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Seed + bootstrap
python -m scripts.seed
python -m scripts.bootstrap_superadmin
```

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string (asyncpg driver). Works with Neon, Supabase, or local Postgres. |
| `DEFAULT_AI_PROVIDER` | Yes | `openai`, `anthropic`, `gemini`, or `mistral` — used for problem generation |
| `OPENAI_API_KEY` | If using OpenAI | API key for the default provider |
| `FAST_AI_PROVIDER` | Yes | Lightweight model for validation, hints, exit ticket scoring |
| `JWT_SECRET_KEY` | Yes | Change in production. Used for all JWT tokens. |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Optional | Bootstrap creates a superadmin on startup if set |
| `ALLOWED_ORIGINS` | Production | JSON array of frontend URLs for CORS |

See `.env.example` for the full list with defaults.

## Architecture

```
app/
├── api/v1/routers/       # FastAPI route handlers (thin — delegate to services)
│   ├── auth.py           # Register, login, /me, password change, heartbeat
│   ├── problems/         # Generate, navigate, validate-step, hints, playlist
│   ├── teacher.py        # Teacher dashboard: classes, roster, live, sessions
│   ├── admin.py          # School admin: create teachers, stats, curriculum
│   ├── superadmin.py     # Platform admin: create school admins, global stats
│   ├── classrooms.py     # Join by code, student management, live session
│   ├── exit_tickets.py   # Teacher exit ticket generation + analytics
│   └── student_exit_tickets.py  # Student submit + scoring
├── core/                 # Config, logging, SSE stream helpers
├── domain/schemas/       # Pydantic models (request/response contracts)
├── infrastructure/
│   ├── database/models/  # SQLAlchemy ORM models
│   └── database/repositories/  # Data access layer (queries)
├── services/             # Business logic
│   ├── ai/               # LLM integration (generation, validation, hints)
│   ├── problem_delivery/ # Playlist, cache, difficulty policy, dedup
│   ├── classroom/        # Join, live session, class settings
│   ├── exit_ticket/      # Scoring, mastery bridge, misconceptions
│   └── mastery_service.py  # Band-filling mastery model
scripts/
├── seed.py               # Curriculum seed (units, lessons, phases, standards)
├── bootstrap_superadmin.py  # Create the platform superadmin
└── seed_data/            # Master lesson library, few-shot examples, standards
```

## Role Hierarchy (B2B Multi-Tenant)

| Role | Created by | Can do |
|---|---|---|
| `superadmin` | Bootstrap / env vars | Create school admins, see all data, platform stats |
| `admin` | Superadmin | Create teachers (inherits district/school), school-scoped stats |
| `teacher` | School admin | Create classrooms, generate problems/exit tickets, manage students |
| `student` | Self-register (public) | Join classroom by code, practice, submit exit tickets |

Students inherit `district` and `school` from the teacher when they join a classroom. Teachers inherit from the admin who created them.

## Key Concepts

### Mastery Model (3-Band)
- **L2 band** (0% → 60%): Filled by Level 2 (faded scaffolding) practice
- **L3 band** (60% → 85%): Filled by Level 3 (independent) practice
- **Exit ticket band** (85% → 100%): Filled by exit ticket scores
- A student needs both practice AND assessment to reach 100%

### Problem Delivery Pipeline
1. **Playlist resume** — check if student has an in-progress problem
2. **Cache hit** — pick a random cached problem (Level 1 only)
3. **LLM generation** — generate fresh with dedup (previous problem summaries in prompt)
4. **Persist** — append to `user_lesson_playlists`, start attempt

### Problem Levels
- **Level 1**: Worked examples (all steps shown, `is_given=true`)
- **Level 2**: Faded scaffolding (first 2 steps shown, rest interactive)
- **Level 3**: Independent practice (all steps interactive)

### Step Validation (Hybrid)
- **Phase 1** (local): String match, canonical equivalence, symbolic (SymPy), numeric tolerance
- **Phase 2** (LLM): Semantic equivalence for ambiguous answers
- MCQ: always Phase 1 only (no LLM needed)

### SSE Streams
Real-time updates via Server-Sent Events (polling-backed, push-on-diff):
- `/teacher/classes/{id}/live/stream` — student presence
- `/teacher/classes/{id}/roster/stream` — roster mastery updates
- `/teacher/exit-tickets/{id}/stream` — exit ticket submissions
- `/classrooms/me/live-session/stream` — student live session state

## Scripts

```bash
# Full seed (idempotent upsert)
python -m scripts.seed

# Wipe everything and reseed
python -m scripts.seed --clean

# Create/upgrade superadmin
python -m scripts.bootstrap_superadmin
```

## Testing

```bash
pytest                    # Run all tests
pytest tests/ -v          # Verbose
pytest --cov=app          # With coverage
```

## Things to Watch Out For

1. **Don't use `--reload` with uvicorn** in production or when testing SSE/LLM. Hot reload interrupts long LLM calls and leaks DB pool connections.

2. **JWT expiry is 7 days** by default. After `seed --clean`, all existing tokens become invalid (user IDs change). Students/teachers must log in again.

3. **`ADMIN_EMAIL`/`ADMIN_PASSWORD`** bootstrap is idempotent — it skips if the email exists. To recreate: delete the user row first, then restart.

4. **Exit ticket scoring** prefers frontend-computed `score_percent` + `results` (from the same `validateStep` API the student used). Server-side scoring is a fallback only.

5. **`days` filter** on exit ticket endpoints filters by `published_at`, not `created_at`.

6. **Blocked students** keep their `classroom_students` row (with `is_blocked=true`) so they can be unblocked later. Removed students have the row deleted and lose `district`/`school`.

7. **Problem dedup** sends up to 5 previous problem summaries (title + first sentence) to the LLM prompt. Not a hard guarantee — the LLM may still generate similar scenarios.

8. **Standards heatmap** shows standards from both teacher sessions (exit tickets, timed practice) AND independent student practice.

## API Documentation

With the server running in development mode, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Disabled in production (`ENVIRONMENT=production`).
