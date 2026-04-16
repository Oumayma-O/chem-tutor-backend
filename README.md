# ChemTutor Backend

AI-powered chemistry tutoring platform with adaptive scaffolding, mastery tracking, and B2B multi-tenant classroom management.

~15,000 lines of application code across 80+ modules, 16 test files, 12 Alembic migrations, ~6,800 lines of curated seed data.

---

## Quick Start

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL, AI provider key, ADMIN_EMAIL, ADMIN_PASSWORD

docker compose up --build
docker compose exec app python -m scripts.seed
docker compose exec app python -m scripts.bootstrap_superadmin
```

API: `http://localhost:8000` — Swagger: `http://localhost:8000/docs`

---

## Superadmin Bootstrap & Credential Flow

### Where to Put Credentials

In `.env` (never committed to git):

```env
ADMIN_EMAIL=admin@yourplatform.com
ADMIN_PASSWORD=use-a-strong-secret-here
```

On app startup, `ensure_admin_user()` in `app/services/auth/bootstrap.py` checks the `users` table:
- Email missing → creates user with `role=superadmin` using `create_user()` factory
- Email exists with `role=superadmin` → no-op
- Email exists with different role → logs warning, skips

Manual run: `python -m scripts.bootstrap_superadmin`

### The Full Credential Chain

```
.env (ADMIN_EMAIL + ADMIN_PASSWORD)
    │
    ▼
Superadmin logs in → POST /auth/login → JWT with role=superadmin
    │
    ├── POST /superadmin/create-school-admin
    │   Payload: { email, password, full_name, district, school }
    │   → Creates user with role=admin, district="Springfield", school="Lincoln High"
    │   → Superadmin shares these credentials with the school principal/IT
    │
    ▼
School Admin logs in → can change own email/password via PUT /auth/me
    │
    ├── POST /admin/create-teacher
    │   Payload: { email, password, full_name }
    │   → Creates user with role=teacher
    │   → district + school FORCEFULLY copied from the admin (not in payload)
    │   → Admin shares credentials with the teacher
    │
    ▼
Teacher logs in → can change own email/password via PUT /auth/me
    │
    ├── Creates classrooms (6-digit join codes auto-generated)
    │   → Cannot have two classrooms with the same name
    │   → Shares the code with students (one-time join)
    │
    ▼
Student self-registers → POST /auth/register (role=student only, public)
    │
    ├── POST /classrooms/join { code: "3617DA" }
    │   → district + school inherited from the teacher who owns the classroom
    │   → Student can enter code during sign-up or later
    │
    ▼
Teacher manages students:
    ├── PATCH /classrooms/{id}/students/{sid} { is_blocked: true }
    │   → Student can't rejoin, submit work, or see live sessions
    │   → Teacher can unblock later
    └── DELETE /classrooms/{id}/students/{sid}
        → Row deleted, district/school cleared on student User record
```

Two admins cannot administrate the same school — the `(district, school)` pair on the admin's User row determines their scope. `GET /admin/teachers` returns only teachers matching the admin's school.

### Admin/Superadmin Dashboard Access

Admins and superadmins have read-only access to the teacher dashboard per class:
- `GET /teacher/classes/{id}/roster` — see students + mastery
- `GET /teacher/exit-tickets/{id}` — see exit ticket results
- `GET /teacher/classes/{id}/live` — see live presence

Exit ticket creation (`POST /teacher/exit-tickets/generate`) is teacher-only. Admins observe, teachers act.

---

## Seed Data Architecture

The curriculum is modeled as structured Python data in `scripts/seed_data/` (~6,800 lines total), seeded into PostgreSQL via `python -m scripts.seed`.

### Data Files

| File | Lines | What it contains |
|---|---|---|
| `lessons.py` | 1,997 | **Master Lesson Library** — 96 lessons, each with title, blueprint, key_equations, key_rules, misconceptions, objectives |
| `problem_few_shots.py` | 2,602 | **Curated few-shot examples** — 35 hand-crafted problems with full step-by-step solutions, used as LLM prompt context |
| `reference_cards.py` | 958 | **Study reference cards** — 82 lesson-level "fiche de cours" with symbolic method steps (no numbers) |
| `standards.py` | 559 | **52 NGSS + AP standards** — code, framework, title, description, category, is_core flag |
| `lesson_standards.py` | 477 | **122 lesson↔standard links** — maps each lesson to the standards it covers |
| `units.py` | 163 | **24 units** — 15 Standard Chemistry + 9 AP Chemistry, each with ordered lesson_ids |
| `phases.py` | 65 | **10 phases** — 5 Standard + 5 AP, grouping units into curriculum progression |
| `lookup.py` | 16 | Grades (Middle School → College), interests (Sports, Music, etc.) |

### How Curriculum Data Flows Through the Platform

```
seed_data/lessons.py (MASTER_LESSONS)
    │
    ├── Lesson.key_equations     → injected into LLM system prompt as "lesson guidance"
    ├── Lesson.key_rules         → injected into hint generation as "Key Rule: ..."
    ├── Lesson.misconceptions    → used by hint service for misconception-aware scaffolding
    ├── Lesson.objectives        → used to derive skill list for step category assignment
    ├── Lesson.blueprint         → selects problem structure (solver/recipe/architect/detective/lawyer)
    │
    ├── seed_data/problem_few_shots.py
    │   └── Injected into generation prompt as "FEW-SHOT EXAMPLE" blocks
    │       4-tier fallback: exact match → same lesson → same unit → global
    │       Up to 2 examples per generation for varied structure
    │
    ├── seed_data/reference_cards.py
    │   └── Stored as Lesson.reference_card_json
    │       Returned by GET /problems/reference-card for the lesson sidebar
    │       Symbolic method steps only (no numbers) — the "study guide"
    │
    ├── seed_data/standards.py + lesson_standards.py
    │   └── Standards heatmap in teacher dashboard
    │       Per-student mastery aggregated across lessons that map to each standard
    │       Union query: teacher sessions + independent student practice
    │
    └── seed_data/units.py + phases.py
        └── Curriculum catalog (GET /units, GET /phases)
            Phase-grouped unit ordering for the student sidebar
            Classroom curriculum overrides (teacher can hide/reorder units)
```

### Few-Shot Examples (Curated Problems)

Each few-shot is a complete problem with steps, stored in `few_shot_examples` table:

```python
# Tuple: (unit_id, lesson_index, difficulty, blueprint, problem_dict)
("unit-chemical-reactions", 1, "easy", "architect", {
    "title": "Balancing Al₂O₃",
    "level": 1,
    "statement": "Balance the equation: Al + O₂ → Al₂O₃",
    "steps": [
        {"label": "Goal / Setup", "type": "interactive", "is_given": True, ...},
        {"label": "Draft", "type": "drag_drop", "equationParts": [...], ...},
        ...
    ]
})
```

Each step has: `label`, `type` (interactive/multi_input/drag_drop/comparison), `is_given` (scaffolding flag), `instruction`, `correctAnswer`, `explanation`, `category` (conceptual/procedural/computational), `skillUsed`.

The seed normalizes `inputFields` to `input_fields`, assigns `category` from `LABEL_TO_MASTERY_CATEGORY`, and computes `is_given` from level if not explicitly set.

### Reference Cards

Symbolic study guides — no numbers, just the general method:

```python
{"lesson": "Molar Mass (1-Step)", "unit_id": "ap-unit-1", "lesson_index": 0,
 "steps": [
    {"label": "Goal / Setup",       "content": "Identify starting unit and target unit"},
    {"label": "Conversion Factors", "content": "Find molar mass ($M$) on the periodic table"},
    {"label": "Dimensional Setup",  "content": "Multiply to cancel starting units ($n = m/M$)"},
    {"label": "Calculate",          "content": "Perform the unrounded arithmetic"},
    {"label": "Answer",             "content": "Round to starting sig figs and attach units"},
]}
```

Generated once by LLM, then persisted in `Lesson.reference_card_json`. Subsequent requests return the cached card — no LLM call.

---

## Scoring Logic & Penalties

### Per-Step Scoring

Each interactive step earns 0.0 to 1.0 points based on how the student solved it:

```
Base score: 1.0 (correct answer)

Penalties:
  - Each hint used:           -0.25
  - Each wrong attempt:       -0.10
  - Answer revealed (3-strike): 0.0 (entire step scores zero)

Examples:
  Correct on first try, no hints:     1.0
  Correct on first try, 1 hint:       0.75
  Correct on second try, no hints:    0.90
  Correct on third try, 2 hints:      0.30
  Answer revealed after 3 failures:   0.0
```

Given/scaffold steps (`is_given=true`) are excluded from scoring — the student is observing, not demonstrating.

### Answer Reveal (3-Strike Rule)

After 3 failed attempts on a step, the student can reveal the correct answer. This is controlled per-classroom:

- `allow_answer_reveal` (boolean) — teacher toggle in Settings tab
- `max_answer_reveals_per_lesson` (integer) — cap on reveals per lesson (default 6, teacher-configurable)

When a step is revealed:
- `was_revealed=true` is set in the step_log
- The step earns 0.0 points (full penalty)
- The mastery preview (`preview_step_progress`) skips blending this step into category scores
- The attempt is still persisted for analytics (teacher sees the student needed help)

### Attempt Score

```
attempt_score = mean(earned_points for each interactive step)
```

Only interactive steps count. Given steps are excluded. The score feeds into the mastery band-filling model.

### Category Scores (Conceptual / Procedural / Computational)

Each step is categorized by its label:
- **Conceptual**: Equation, Knowns, Goal/Setup, Data Extraction, Concept ID
- **Procedural**: Substitute, Dimensional Setup, Draft, Refine, Apply Concept
- **Computational**: Calculate, Answer, Final Answer

Per-category score = earned / possible for that category. Tracked in `SkillMastery.category_scores` JSONB. Used by the teacher dashboard for diagnostic breakdown (strengths/weaknesses).

### Three-Band Mastery

```
0%                    60%                   85%                 100%
├─── L2 Practice ─────┤─── L3 Practice ─────┤── Exit Ticket ────┤
```

- L2 band: `min(sum(qualifying_L2_scores) / 3, 1.0) × 0.60`
- L3 band: `min(sum(qualifying_L3_scores) / 3, 1.0) × 0.25`
- ET band: `(exit_ticket_score / 100) × 0.15` — additive, never overwrites practice
- Qualifying score threshold: `MASTERY_PASSING_SCORE=0.6` (below this, attempt is ignored)

---

## Step Types & Widget Architecture

Problems have 3-6 steps. Each step's `type` determines the frontend widget:

| Type | Widget | When to use | Answer field |
|---|---|---|---|
| `interactive` | Single text input | Default: one value, unitless numbers, text answers | `correctAnswer` |
| `multi_input` | Multiple labeled inputs | Multiple values OR any numeric + unit answer | `inputFields: [{label, value, unit}]` |
| `drag_drop` | Drag-and-drop assembly | Symbolic equations, electron configs | `equationParts: [tokens]` |
| `comparison` | Three-button (<, >, =) | Comparing two quantities | `comparisonParts: [left, right]`, `correctAnswer: "<"/">"/"="` |

The `is_given` flag controls scaffolding:
- Level 1 (Worked): all steps `is_given=true` — student reads the solution
- Level 2 (Faded): first 2 steps `is_given=true`, rest interactive
- Level 3 (Independent): all steps `is_given=false` — student solves everything

Server enforces L1 (all true) and L3 (all false) as guardrails. LLM controls L2 fading.

---

## Problem Prefetching & Playlist Persistence

### Prefetching

When a student is on Level 2, the frontend prefetches a Level 3 problem in the background:
- `triggerPrefetch(difficulty, excludeIds, nextLevel)` fires after the current problem loads
- Level 3 prefetch starts immediately (zero delay); Level 2 prefetch uses 400ms delay
- Prefetched problem is cached in `prefetchedProblem.current` and `levelCacheRef`
- When the student advances, `applyPrefetchedProblem()` displays it instantly — no loading spinner

### Playlist Persistence

Every generated problem is appended to `user_lesson_playlists` (JSONB array):
- Key: `(user_id, unit_id, lesson_index, level, difficulty)`
- `current_index` tracks the student's position
- `append_and_advance()` uses PostgreSQL `ON CONFLICT DO UPDATE` (upsert)
- Deduplication: if the problem ID already exists in the array, moves index to it instead of appending

On reload or new device, `GET /problems/playlist` returns the full playlist with `attempts_by_problem` — the frontend hydrates all problems, answers, and step state from the backend.

---

## Exit Ticket System

### Creation (Teacher Only)

`POST /teacher/exit-tickets/generate` — AI generates 1-10 questions per ticket:
- Question types: MCQ, numeric, short_answer (or mixed)
- Difficulty: easy/medium/hard
- Lesson-context-aware: uses the same `key_equations`, `objectives`, `misconceptions` from the seed data
- MCQ options include `misconception_tag` for analytics

### Submission & Scoring

Student submits via `POST /student/exit-tickets/{id}/submit`:
1. Frontend sends `score_percent` + per-question `results` (from `validateStep` API)
2. Backend prefers frontend values (matches what student saw)
3. Fallback: server-side scoring via `StepValidationService` (same hybrid pipeline)
4. Score feeds into mastery bridge (fills 85→100% band)

### Teacher Analytics

- Per-question class score (% correct)
- Per-student submission with score badge
- Misconception analytics: tag frequency across all tickets
- Historical `_effective_score()` derives correct score from `is_correct` flags for pre-fix rows

---

## Database Schema (15+ tables)

| Table | Key columns | Purpose |
|---|---|---|
| `users` | email, role, district, school | All accounts (superadmin/admin/teacher/student) |
| `user_profiles` | grade_id, course_id | Extended profile + interests junction |
| `classrooms` | code, live_session (JSONB), settings | Teacher-owned classes with 6-digit codes |
| `classroom_students` | is_blocked, joined_at | Many-to-many junction with block support |
| `user_lesson_playlists` | problems (JSONB[]), current_index | Per-level problem history |
| `problem_attempts` | step_log (JSONB), score, completed_at | Per-problem attempt with step-by-step data |
| `skill_mastery` | mastery_score, category_scores, level3_unlocked | Rolling mastery per (user, unit, lesson) |
| `problem_cache` | problem_data (JSONB), expires_at | Cached AI-generated problems (L1 never expires) |
| `exit_tickets` | questions (JSONB), published_at | Teacher assessments |
| `exit_ticket_responses` | answers (JSONB), score | Student submissions with per-answer is_correct |
| `classroom_sessions` | session_type, started_at, ended_at | Session history for analytics |
| `presence_heartbeats` | step_id, last_seen_at | Live student tracking (30s interval) |
| `user_session_activity` | session_date, total_minutes_active | Daily login/engagement |
| `lessons` | key_equations, objectives, blueprint, reference_card_json | Curriculum content |
| `units` / `phases` | sort_order, course_id | Curriculum structure |
| `standards` / `lesson_standards` | code, framework, is_core | NGSS/AP alignment |
| `few_shot_examples` | example_json (JSONB), strategy, variant_index | Curated problem examples |

### Caching Strategy

| What | Where | TTL | Invalidation |
|---|---|---|---|
| L1 worked examples | `problem_cache` | Never expires | Background backfill when < 3 per slot |
| L2/L3 problems | `problem_cache` | 7 days | Expired entries ignored on pick |
| Reference cards | `Lesson.reference_card_json` | Permanent | Generated once, never regenerated |
| Few-shot examples | `few_shot_examples` | Permanent | Updated only by `seed` script |
| Playlist state | `user_lesson_playlists` | Permanent | Upserted on every generate/navigate |
| Frontend session | `localStorage` | Until cleared | Hydrated from backend on new device |

---

## SSE (Server-Sent Events)

| Stream | Endpoint | Poll | Purpose |
|---|---|---|---|
| Live presence | `/teacher/classes/{id}/live/stream` | 2s | Who's online, current step |
| Roster mastery | `/teacher/classes/{id}/roster/stream` | 5s | Mastery scores, at-risk flags |
| Exit tickets | `/teacher/exit-tickets/{id}/stream` | 2s | Submission count, scores |
| Live session | `/classrooms/me/live-session/stream` | 2s | Student: exit ticket / timed practice |
| Practice analytics | `/.../practice-analytics/stream` | 2s | Per-student level stats |

Push-on-diff: JSON hash comparison, only sends `data:` frames when content changes. Heartbeat comments every ~24s keep connections alive through proxies.

---

## Scripts

```bash
python -m scripts.seed              # Idempotent curriculum upsert
python -m scripts.seed --clean      # Wipe ALL data + reseed (dev only)
python -m scripts.bootstrap_superadmin  # Create/verify superadmin from .env
```

## Testing

```bash
pytest                    # All tests
pytest tests/ -v          # Verbose
pytest --cov=app          # Coverage
```

---

## Gotchas

1. **No `--reload`** — interrupts LLM calls (30-120s) and SSE streams.
2. **JWT = 7 days**. After `seed --clean`, all tokens invalid. Log in again.
3. **Bootstrap is idempotent** — delete user row to force recreation.
4. **Exit ticket scoring** prefers frontend values. Server-side is fallback.
5. **Problem dedup** is best-effort (5 summaries in prompt).
6. **Standards heatmap** = UNION of teacher sessions + student practice.
7. **Blocked ≠ removed**: blocked keeps row (can unblock). Removed deletes + clears district/school.
8. **Markdown sanitizer** is the most fragile code — each regex targets a specific LLM failure.
9. **`create_user()` factory** is the single source of truth for all user creation.
10. **SSE uses query-param auth** (`?token=...`) — EventSource can't set headers.
11. **Two admins can't share a school** — scope is `(district, school)` on the admin User row.
12. **Classroom names must be unique per teacher** — enforced at DB level.

---

## API Docs

Development: `http://localhost:8000/docs` (Swagger) / `http://localhost:8000/redoc` — disabled in production.
