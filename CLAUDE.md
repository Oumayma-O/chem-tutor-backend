# CLAUDE.md — ChemTutor Backend

Behavioral guidelines for this project. These rules apply to every task unless explicitly overridden.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

---

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

---

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

---

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

---

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## 5. Project-Specific Rules

### Architecture

- **Thin routers.** Routers live in `app/api/v1/routers/`. No business logic there — call a service, return the result. If a router is doing work, move that work to a service.
- **SRP services.** Each service in `app/services/` owns one concern. Don't add unrelated logic to an existing service; create a new one or ask.
- **Typed repositories.** DB access goes through `app/infrastructure/database/repositories/`. Never write raw queries in routers or services.
- **Schemas are contracts.** `app/domain/schemas/` defines API contracts and LLM output shapes. Changes here can break the frontend and AI pipelines — be deliberate.

### Database & Migrations

- **Always create an Alembic migration** when changing ORM models in `app/infrastructure/database/models/`. Don't skip this step.
- Migration files go in `alembic/versions/` with the naming convention `YYYYMMDD_<slug>.py`.
- After writing a migration, verify it with `alembic upgrade head` in the dev container before considering the task done.
- **`level3_unlocked` is a one-way latch.** Never set it to `False` in code. `MasteryRepository.upsert()` only writes it when `True`. Don't change this behavior.

### AI / LLM

- **LLM calls belong in `app/services/ai/`.** Don't add LLM calls in routers, repositories, or general services.
- **Structured output via LangChain.** Use `with_structured_output()` and Pydantic v2 schemas for all LLM responses. Don't parse raw text.
- **Math validation uses `app/utils/math_eval.py`** — AST-based, no `eval()`. If a step answer could be numeric, run it through `math_eval` first before falling back to LLM validation. Don't bypass this.
- **Prompts live in `app/services/ai/*/prompts.py`** for their respective service. Don't embed long prompt strings inline in service methods.
- Use Tenacity for LLM retry logic. Don't write manual retry loops.

### Auth

- **Auth is Supabase's job.** There is no auth logic in this backend. JWT validation is done via the `authz.py` dependency. Don't add custom auth logic.
- User identity comes from `get_current_user()` in `app/api/v1/authz.py`. Use it consistently — don't read user IDs from request bodies.

### Logging

- Use `structlog` for all logging. Don't use `print()` or the stdlib `logging` module directly.
- Log at the service layer, not the router layer.

### Style

- Python 3.12. Use `async/await` throughout — no sync DB calls.
- Pydantic v2 syntax (`model_config`, `field_validator`, etc.). Don't use v1 patterns.
- SQLAlchemy 2.0 style (`select()`, `session.execute()`, `await session.scalar()`). No legacy `session.query()`.

---

**These guidelines are working if:** diffs are small and focused, migrations are never forgotten, LLM logic stays in `services/ai/`, and routers stay thin.
