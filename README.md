# Chem Guide — Backend

FastAPI + PostgreSQL + LangChain. AI-powered mastery-based chemistry tutor.

---

## Dev Setup

### Prerequisites
- Docker + Docker Compose
- Python 3.12 (for local seed scripts)
- `.env` with `DATABASE_URL` (Neon) + at least one AI provider key

### Start the backend
```bash
docker compose build   # required after any code change in app/
docker compose up -d
docker compose exec app alembic upgrade head   # apply DB migrations (after pulling new revisions)
# API → http://localhost:8000   Docs → http://localhost:8000/docs
```

`docker-compose.yml` bind-mounts `./alembic` so migration files match the repo; run `alembic upgrade head` whenever you add migrations.

> `develop.watch` in docker-compose is NOT a volume mount — always rebuild after editing `app/`.

### Seed the database
```bash
python -m scripts.seed          # idempotent upsert (safe to re-run)
python -m scripts.seed --clean  # truncate all tables then reseed
```

### Full schema reset (dev only)
```bash
py - <<'EOF'
import asyncio, sys; sys.path.insert(0, ".")
async def r():
    from app.infrastructure.database.connection import engine, Base
    import app.infrastructure.database.models
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
        await c.run_sync(Base.metadata.create_all)
asyncio.run(r())
EOF
python -m scripts.seed
```

### Logs & restart
The API runs **without** `uvicorn --reload` (avoids breaking long AI requests and SSE during file sync). After editing code, restart:

```bash
docker logs chem-backend -f          # live logs
docker compose restart app           # pick up code/env (compose service name)
docker compose build && docker compose up -d   # rebuild image
```

To use **hot reload** again locally, override the command, e.g. add `--reload` to the `uvicorn` line in `docker-compose.yml` (not recommended while testing exit-ticket generate or live streams).

---

## Architecture

```
Request → Router → Service → Repository → PostgreSQL (Neon)
                ↘ AI Services → LangChain → OpenAI / Anthropic / Gemini
```

```
app/
  api/v1/routers/       thin routers, no business logic
  core/                 config, structured logging (structlog)
  domain/schemas/       Pydantic models (API + LLM output schemas)
  infrastructure/
    database/
      models/           SQLAlchemy ORM (one file per concern)
      repositories/     typed async repos
  services/
    ai/
      problem_generation/   ProblemGenerationService + prompts v10
      thinking_analysis/    ThinkingAnalysisService (error classification)
      reference_card/       ReferenceCardService
    mastery_service.py      deterministic mastery + band logic
    problem_delivery_service.py   cache-aware delivery, blueprint lookup
scripts/
  seed.py               idempotent seeder (units, lessons, few-shots)
  seed_data/
    lessons.py          96 lessons, each with blueprint + required_tools
    few_shots.py        3 curated examples (detective/lawyer/solver)
```

---

## AI Provider Config

`DEFAULT_AI_PROVIDER` in `.env` → `openai` | `anthropic` | `gemini`

---

## Mastery Logic

- **Bands**: L2 fills 0→60%, L3 fills 60→85%. Complete at ≥ 85%.
- **L3 unlock**: one-way latch — set when mastery ≥ 75% at hard difficulty.
- **Difficulty adaptation**: position within band drives easy/medium/hard.
- **At-risk**: mastery < 40% after ≥ 3 attempts.

---

## Roadmap

### ✅ Milestone 1 — AI Tutor Core (done)

| Status | Item |
|--------|------|
| ✅ | Core DB schema — `problem_attempts`, `skill_mastery`, `exit_tickets`, user linkage |
| ✅ | Problem generation — L1 worked example → L2 faded → L3 full practice |
| ✅ | Blueprint system v10 — 5 blueprints (solver/recipe/architect/detective/lawyer) per lesson |
| ✅ | Widget types — `given`, `interactive`, `drag_drop`, `variable_id`, `comparison` |
| ✅ | Step validation — numeric tolerance, string match, drag-drop, comparison (`<`/`>`/`=`) |
| ✅ | Hint generation — 3-level scaffolded, no answer leaking |
| ✅ | Error classification — conceptual/procedural/computational |
| ✅ | Structured output + retry logic (LangChain + Tenacity) |
| ✅ | Persist attempts in DB — `MasteryRepository.record_attempt()` |
| ✅ | Playlist navigation — prev/next within user/unit/lesson/level/difficulty |
| ✅ | Reference card (fiche de cours) — generated once, cached in DB |
| ✅ | Mastery computation — rolling score, band-fill, L3 unlock latch |
| ✅ | Thinking tracker — per-step logs in `thinking_tracker_logs` |
| ✅ | Adaptive difficulty — `getDifficultyForMastery()` + backend `focus_areas` |
| ✅ | 96 lessons seeded across Standard + AP Chemistry with blueprints |
| ✅ | 3 curated few-shot examples (new widget types) |
| ⚠️ | Step timing — `step_log` JSONB exists but time-per-step not sent from frontend |
| ⚠️ | `comparison` step validation — needs explicit branch in `StepValidationService` |

---

### 🔧 Milestone 2 — Simulations + Problem Quality (next)

| Status | Item |
|--------|------|
| ❌ | **Simulation integration** — embed PhET / custom canvas sims per lesson; pass sim output as problem context |
| ❌ | **Curated problem bank** — hand-authored worked examples per lesson stored in `problem_cache` for L1 |
| ❌ | **Few-shot library expansion** — 3–5 curated examples per blueprint type (currently 3 total) |
| ❌ | **Prompt QA pass** — test generation across all 96 lessons, fix blueprint mismatches |
| ❌ | **Problem deduplication** — `exclude_ids` already wired but no frontend tracking across sessions |
| ❌ | **Problem style variety** — context tags (sports/food/etc.) tested across all blueprints |

---

### 🔧 Milestone 3 — Teacher Dashboard + Analytics (next)

| Status | Item |
|--------|------|
| ✅ | Class mastery aggregation endpoint (`POST /analytics/classes`) |
| ✅ | Per-student skill breakdown (`GET /mastery/users/{id}/...`) |
| ✅ | Exit ticket generation (`POST /problems/exit-ticket`) |
| ✅ | Error pattern data in `misconception_logs` |
| ❌ | **Exit ticket readiness trigger** — rule for when to prompt student (e.g. after N correct L3 attempts) |
| ❌ | **Exit ticket response save endpoint** — `exit_ticket_responses` table exists, no write API |
| ❌ | **Exit ticket performance report** — aggregation by class/topic |
| ❌ | **At-risk detection alerts** — threshold logic (mastery < 40% after 3 attempts) wired to teacher view |
| ❌ | **Curriculum customization** — teacher uploads curriculum doc → scoped to classroom |
| ❌ | **Custom lesson mapping** — teacher maps their syllabus order to canonical lessons |
| ❌ | **Teacher dashboard frontend** — all backend APIs exist; no UI pages built yet |
| ❌ | **Classroom join flow** — `POST /classrooms/join` exists; no frontend page |

---

### 🔧 Milestone 4 — Admin Dashboard

| Status | Item |
|--------|------|
| ❌ | **Admin auth** — role-based access (admin vs teacher vs student) |
| ❌ | **Lesson content editor** — view/edit lesson `key_rules`, `key_equations`, `blueprint` from UI |
| ❌ | **Few-shot manager** — view/add/delete few-shot examples per blueprint via UI |
| ❌ | **Generation log viewer** — browse `generation_logs` to QA prompt output |
| ❌ | **Prompt version audit** — compare prompt versions, A/B output |
| ❌ | **Platform-wide mastery heatmap** — which lessons are hardest across all users |
| ❌ | **User management** — list students, view profiles, manual mastery overrides |
| ❌ | **DB health + seed runner** — trigger reseed or schema reset from UI |
