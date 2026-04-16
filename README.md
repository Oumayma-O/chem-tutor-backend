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

### Without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
python -m scripts.seed
python -m scripts.bootstrap_superadmin
```

---

## Environment Variables

Copy `.env.example` to `.env`. Critical variables:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL (asyncpg). Works with Neon, Supabase, local. |
| `DEFAULT_AI_PROVIDER` | Yes | `openai` / `anthropic` / `gemini` / `mistral` |
| `OPENAI_API_KEY` | If using OpenAI | Problem generation, reference cards |
| `FAST_AI_PROVIDER` | Yes | Lightweight model for validation, hints, exit tickets |
| `JWT_SECRET_KEY` | Yes | Change in production |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Optional | Bootstrap superadmin on startup |
| `ALLOWED_ORIGINS` | Production | JSON array of frontend URLs for CORS |

See `.env.example` for mastery thresholds, playlist caps, and all defaults.

---

## Architecture Overview

```
app/
├── api/v1/routers/          # Thin HTTP handlers — delegate to services
├── core/                    # Config, structured logging, SSE helpers
├── domain/schemas/          # Pydantic request/response contracts
├── infrastructure/
│   ├── database/models/     # SQLAlchemy ORM (PostgreSQL + JSONB)
│   └── database/repositories/  # Data access layer
├── services/                # Business logic
│   ├── ai/                  # LLM pipelines (generation, validation, hints)
│   ├── problem_delivery/    # Playlist, cache, difficulty, dedup
│   ├── classroom/           # Join, live session, settings
│   ├── exit_ticket/         # Scoring, mastery bridge, misconceptions
│   └── mastery_service.py   # 3-band mastery model
├── utils/                   # Markdown sanitizer, math evaluation
scripts/
├── seed.py                  # Curriculum: units, lessons, phases, standards
├── bootstrap_superadmin.py  # Platform superadmin creation
└── seed_data/               # Master lesson library, few-shots, standards
```

---

## Engineering Complexity & Optimizations

### 1. Hybrid Step Validation Pipeline

The most complex subsystem. Every student answer goes through a multi-phase waterfall that balances accuracy against latency:

```
Student answer
    │
    ▼
Phase 1: Local (< 1ms)
    ├── Normalized string match (case, whitespace, LaTeX normalization)
    ├── Canonical equivalence (chemical formula rewriting)
    ├── Symbolic equivalence (SymPy algebraic comparison)
    ├── Numeric comparison (configurable tolerance: 1% final, 2% intermediate)
    │   ├── Unit extraction + dimensional analysis (Pint library)
    │   ├── SI prefix scaling (55.4×10³ ms ≈ 55.4 s)
    │   └── Naked-number guard (value correct but unit missing → defer to Phase 2)
    └── Multi-input JSON field-by-field comparison
    │
    ▼ (only if Phase 1 is inconclusive)
Phase 2: LLM Equivalence (200-800ms)
    ├── Fast model (gpt-4o-mini / claude-haiku) with structured output
    ├── Semantic equivalence judgment + short feedback
    └── Fallback: string match on LLM error (never 502 to student)
    │
    ▼
Post-processing
    ├── Semicolon-separated completeness check
    ├── Unit presence enforcement (value OK but unit missing)
    ├── Multi-segment partial feedback ("you answered 2 of 3 parts")
    └── Generic feedback guarantee (never empty feedback on incorrect)
```

Phase 1 resolves ~70% of answers locally with zero LLM cost. The tolerance is tighter for final answers (1%) than intermediate steps (2%) to match sig-fig expectations.

### 2. LLM Output Structuring

All LLM calls use LangChain's `with_structured_output()` which enforces a Pydantic schema on the response. The `generate_structured()` wrapper in `app/services/ai/shared/llm.py` handles:

- Two-tier model selection (powerful vs fast) from config
- Provider abstraction (OpenAI, Anthropic, Gemini, Mistral)
- OpenAI-specific `method="function_calling"` to avoid `ParsedChatCompletion` serialization warnings
- Async invocation with configurable timeout (`LLM_TIMEOUT_SECONDS`)

Problem generation retries up to 3 times if the structured output fails LaTeX validation.

### 3. Markdown/LaTeX Sanitizer Pipeline

LLM-generated chemistry content contains LaTeX that must render in KaTeX on the frontend. The sanitizer (`app/utils/markdown_sanitizer.py`, ~600 lines) is a deterministic regex pipeline that runs on every generated string:

```
LLM JSON output
    │
    ▼
Tab/FormFeed recovery     ← JSON parser ate \t from \text, \f from \frac
    │
    ▼
ANSI/control char strip   ← LLM occasionally emits escape codes
    │
    ▼
Dollar-split exponents    ← $X$^{2} → $X^{2}$ (exponent leaked outside math)
    │
    ▼
\cdot unit garbage        ← \backslash\text{cdotK} → \cdot \text{K}
    │                        \cdot inside \text{} → unicode middle dot
    ▼
Unbracketed exponents     ← 10^23 → 10^{23}
    │
    ▼
Orphaned commands         ← \textamu → \text{amu}, \mathrmMg → \mathrm{Mg}
    │
    ▼
Math wrapper normalize    ← \( \) → $, $...$ → $...$
    │
    ▼
Globally wrapped fix      ← Entire statement in one $...$ → split prose/math
    │
    ▼
Calculator upgrade        ← Ea = 8.314 * ln(8.10e-3) → $E_a = 8.314 \times \ln(...)$
    │
    ▼
Slash → \frac             ← (a)/(b) → \frac{a}{b}, Ea/R → \frac{E_a}{R}
    │                        Sci-not blocks: 1.15×10^{-2} / 2.40×10^{-3}
    ▼
Bare words in math        ← "formula units to g" → \text{formula units to} g
    │
    ▼
Long float truncation     ← 18.11723679840585 → 18.1172
    │
    ▼
KaTeX dry-run             ← Balanced braces check, forbidden command detection
```

Each fix is idempotent. The pipeline runs on every string field in the problem JSON recursively. Hints use a `for_hint=True` mode that skips auto-wrapping (hints are prose, not math).

### 4. Problem Delivery & Dedup Pipeline

```
POST /problems/generate
    │
    ▼
Playlist resume check     ← Return current problem if student has one in-progress
    │
    ▼ (no resume)
Cache hit (L1 only)       ← Random pick from problem_cache, excluding seen IDs
    │
    ▼ (cache miss or L2/L3)
Fetch previous summaries  ← Titles + first sentences from playlist (max 5)
    │                        Injected into prompt as "DO NOT REPEAT" block
    ▼
LLM generation            ← Full system prompt with blueprint, level, few-shots
    │
    ▼
Structured output parse   ← ProblemOutput Pydantic model (3 retry attempts)
    │
    ▼
Markdown sanitizer        ← Full pipeline above
    │
    ▼
Step type enforcement     ← is_given flags, category assignment from labels
    │
    ▼
Persist to playlist       ← UPSERT to user_lesson_playlists (JSONB array)
    │
    ▼
Start attempt             ← Insert problem_attempts row
    │
    ▼
Background tasks          ← Cache storage, telemetry logging, next-level prefetch
```

The playlist coordinator caches the last DB fetch to avoid duplicate queries when `get_previous_problem_summaries` runs after `try_resume`.

### 5. SSE (Server-Sent Events) Architecture

Real-time updates use a polling-backed SSE pattern (`app/core/sse_stream.py`):

```python
async def sse_json_poll_events(poll_json, interval_seconds=2.0):
    """Poll DB, push only when JSON hash changes. Heartbeat every ~24s."""
```

Active streams:
- `/teacher/classes/{id}/live/stream` — student presence (2s poll)
- `/teacher/classes/{id}/roster/stream` — roster mastery (5s poll)
- `/teacher/exit-tickets/{id}/stream` — exit ticket submissions (2s poll)
- `/classrooms/me/live-session/stream` — student live session state (2s poll)
- `/teacher/classes/{id}/sessions/{id}/practice-analytics/stream` — timed practice (2s poll)

Each stream does a lightweight auth pre-check before opening, then polls in a loop. The `sse_json_poll_events` helper compares JSON hashes and only pushes `data:` frames when content changes. Comment heartbeats (`": heartbeat\n\n"`) keep connections alive through proxies.

Frontend uses `useEventSourceConnection` hook that reconnects with backoff on error.

### 6. Three-Band Mastery Model

```
0%                    60%                   85%                 100%
├─── L2 Practice ─────┤─── L3 Practice ─────┤── Exit Ticket ────┤
     (faded)                (independent)         (assessment)
```

- L2 band: filled by qualifying Level 2 attempts (`l2_attempts_to_fill=3`)
- L3 band: filled by qualifying Level 3 attempts (`l3_attempts_to_fill=3`)
- ET band: filled by exit ticket score (additive, never overwrites practice)
- Level 3 unlock: one-way latch — requires perfect score on a single L2 attempt
- Difficulty adapts from mastery: < 40% → easy, 40-70% → medium, > 70% → hard

The mastery bridge (`app/services/exit_ticket/mastery_bridge.py`) feeds exit ticket scores into `SkillMastery` so the standards heatmap reflects both practice and assessment.

---

## B2B Multi-Tenant Role Hierarchy

| Role | Created by | Scope |
|---|---|---|
| `superadmin` | Bootstrap env vars | Platform-wide. Creates school admins. |
| `admin` | Superadmin | School-scoped. Creates teachers (inherits district/school). |
| `teacher` | School admin | Owns classrooms. Generates problems/exit tickets. |
| `student` | Self-register (public) | Joins classroom by code. Inherits district/school from teacher. |

Student management: teachers can block (`PATCH`) or remove (`DELETE`) students. Blocked students can't rejoin, submit work, or see live sessions. Removed students lose district/school.

---

## Scripts

```bash
python -m scripts.seed              # Idempotent curriculum upsert
python -m scripts.seed --clean      # Wipe all data + reseed
python -m scripts.bootstrap_superadmin  # Create/verify superadmin
```

## Testing

```bash
pytest                    # All tests
pytest tests/ -v          # Verbose
pytest --cov=app          # Coverage
```

---

## Gotchas for New Developers

1. **No `--reload` with uvicorn** — interrupts LLM calls and SSE streams, leaks DB pool connections.

2. **JWT expiry is 7 days**. After `seed --clean`, all tokens are invalid (user IDs change). Log in again.

3. **Bootstrap is idempotent** — skips if email exists. To recreate: delete the user row first.

4. **Exit ticket scoring** prefers frontend-computed `score_percent` + `results`. Server-side is fallback only.

5. **Problem dedup is best-effort** — 5 previous summaries in the prompt. LLM may still generate similar scenarios.

6. **Standards heatmap** includes both teacher sessions AND independent student practice (union query).

7. **Blocked vs removed**: blocked keeps the row (`is_blocked=true`, can unblock later). Removed deletes the row and clears district/school.

8. **`days` filter** on exit ticket endpoints filters by `published_at`, not `created_at`.

9. **The markdown sanitizer** is the most fragile code — each regex fix targets a specific LLM failure mode observed in production. Test changes against the existing test suite before modifying.

10. **`create_user()` factory** in `app/services/auth/user_factory.py` is the single source of truth for user creation. All 4 creation paths (register, create-teacher, create-school-admin, bootstrap) use it.

---

## API Documentation

Development mode: `http://localhost:8000/docs` (Swagger) / `http://localhost:8000/redoc`

Disabled in production (`ENVIRONMENT=production`).
