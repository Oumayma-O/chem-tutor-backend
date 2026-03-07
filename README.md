# Chem Guide — Backend

FastAPI backend for the AI-powered mastery-based chemistry tutor.

## Architecture

Single FastAPI application with internal module separation:

```
Request → Router → Service → Repository → PostgreSQL
                ↘ TutorService → AIProvider (OpenAI | Anthropic | Gemini)
```

**Module boundaries:**
- `api/` — routers only (zero business logic)
- `services/` — all business and AI logic
- `infrastructure/` — database models, repositories, external I/O
- `domain/schemas/` — shared Pydantic models (request/response + LLM output schemas)
- `core/` — config, logging

## Local Development

**Prerequisites:** Docker, Docker Compose

```bash
cd backend
cp .env.example .env
# Fill in at least one AI provider key in .env

docker compose up
```

The API will be available at http://localhost:8000
Interactive docs: http://localhost:8000/docs

## Running Without Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

# Start local Postgres (or point DATABASE_URL at an existing one)
uvicorn app.main:app --reload
```

## Database Migrations

```bash
# Create a new migration after changing models.py
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

## AI Provider Configuration

Set `DEFAULT_AI_PROVIDER` in `.env` to `openai`, `anthropic`, or `gemini`.
Each provider requires its corresponding API key.

To benchmark providers:

```bash
pip install -e '.[notebooks]'
jupyter notebook notebooks/benchmark_providers.ipynb
```

## Adding a New AI Provider

1. Create `app/services/ai/providers/my_provider.py`
2. Implement `AIProvider` and decorate with `@ProviderFactory.register("my_name")`
3. Add the model name + API key to `app/core/config.py`
4. Import the module in `app/services/ai/providers/__init__.py`

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/tutor/generate-problem` | Generate a structured 5-step problem |
| POST | `/api/v1/tutor/validate-answer` | Validate a student answer (local + AI fallback) |
| POST | `/api/v1/tutor/generate-hint` | 3-level scaffolded hint |
| POST | `/api/v1/tutor/classify-errors` | Classify error type + misconception tag |
| POST | `/api/v1/tutor/generate-exit-ticket` | Generate exit ticket questions |
| POST | `/api/v1/tutor/generate-class-insights` | AI teaching insights from class data |
| POST | `/api/v1/mastery/attempts/start` | Begin a problem attempt |
| POST | `/api/v1/mastery/attempts/complete` | Complete attempt + recompute mastery |
| GET  | `/api/v1/mastery/users/{id}/chapters/{id}/topics/{n}` | Get mastery state |
| POST | `/api/v1/analytics/classes` | Teacher analytics + at-risk detection |
| GET  | `/health` | Health check |

## Project Structure

```
backend/
├── app/
│   ├── api/v1/routers/     # FastAPI routers (thin layer)
│   ├── core/               # Config + structured logging
│   ├── domain/schemas/     # Pydantic request/response models
│   ├── services/
│   │   ├── ai/             # Provider abstraction + TutorService
│   │   └── mastery_service.py
│   └── infrastructure/
│       └── database/       # SQLAlchemy models + repositories
├── alembic/                # Migration scripts
├── notebooks/              # Provider benchmark notebook
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Mastery Logic

- **Band-filling**: L2 band (0 → 60%), L3 band (60% → 85%). Lesson complete when mastery ≥ `l3_mastery_ceiling` (default 0.85).
- **Level 3 unlock**: one perfect L2 attempt unlocks L3; further attempts fill the L3 band.
- **should_advance / has_mastered**: true when `mastery_score >= l3_mastery_ceiling` (no separate threshold).
- **Difficulty adaptation**: from position within the L2 band (`MASTERY_WINDOW` for rolling context).
- **At-risk detection**: mastery < 40% after at least 3 attempts.
