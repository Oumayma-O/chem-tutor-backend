"""Problem generation schemas."""

import uuid
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field, model_validator


def _coerce_step_dict_wire_input_fields(step: Any) -> Any:
    """Normalize legacy step keys so only ``input_fields`` remains (API wire format)."""
    if not isinstance(step, dict):
        return step
    out = dict(step)
    current = out.get("input_fields")
    alt = out.pop("inputFields", None)
    legacy = out.pop("labeledValues", None)
    if current is None:
        if alt is not None:
            out["input_fields"] = alt
        elif legacy is not None:
            out["input_fields"] = legacy
    return out


def _coerce_problem_output_dict_before(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    steps = data.get("steps")
    if not isinstance(steps, list):
        return data
    out = dict(data)
    out["steps"] = [_coerce_step_dict_wire_input_fields(s) for s in steps]
    return out


class InputField(BaseModel):
    """
    One input field within a multi_input step.
    `label` is displayed next to the input box; `value` is the correct answer;
    `unit` is an optional unit suffix.
    Accepts legacy `variable` key for backward-compat with cached DB data.
    """
    label: str = Field(validation_alias=AliasChoices("label", "variable"))
    value: str
    unit: str

    model_config = {"populate_by_name": True}


class ProblemStep(BaseModel):
    """
    One step in a chemistry problem.

    Naming: ``type`` is the step *widget kind* (how the UI behaves). ``inputFields`` / ``input_fields``
    is the *payload* for that widget when ``type`` is ``multi_input`` — same idea as ``equationParts``
    for ``drag_drop`` and ``comparisonParts`` for ``comparison``.

    Widget types (chosen based on what the student is doing, not just the level):
      "interactive" — single micro-input text box (default for calculation/answer steps)
      "drag_drop"   — assemble an equation/formula by arranging parts
      "multi_input" — student inputs multiple distinct labeled values
      "comparison"  — student compares two things with <, >, or =

    ``is_given`` MUST be set by the LLM based on the current level:
      Level 1 → all steps True (full worked example)
      Level 2 → first 2 steps True, rest False (faded scaffolding)
      Level 3 → all steps False (independent practice)
    Server enforces L1 (all True) and L3 (all False) as a guardrail; LLM controls L2.
    When True the step renders as a read-only teaching/scaffolding step.
    """
    id: str = ""  # LLM often omits; service fills with problem_id + step_number if empty
    step_number: int = Field(validation_alias="stepNumber")
    type: Literal["interactive", "drag_drop", "multi_input", "comparison"]
    is_given: bool = False  # set by LLM; server guardrail enforces L1/L3 rules
    label: str
    instruction: str
    explanation: str | None = Field(
        default=None,
        description=(
            "Max 20 words. One-sentence show-your-work trace explaining how correctAnswer was found. "
            "Generated for ALL steps. Displayed automatically when is_given=True; used for hint "
            "generation context on interactive steps."
        ),
    )
    key_rule: str | None = Field(
        default=None,
        validation_alias="keyRule",
        description=(
            "The single most relevant rule, formula, or principle for this step. "
            "Used by hint generation — keeps hints focused without requiring full lesson context."
        ),
    )
    skill_used: str | None = Field(default=None, validation_alias="skillUsed")
    correct_answer: str | None = Field(default=None, validation_alias="correctAnswer")
    equation_parts: list[str] | None = Field(default=None, validation_alias="equationParts")
    input_fields: list[InputField] | None = Field(
        default=None,
        validation_alias=AliasChoices("inputFields", "labeledValues"),
    )
    comparison_parts: list[str] | None = Field(default=None, validation_alias="comparisonParts")

    # No "hint" field: hints are generated on demand via POST /problems/hint.
    model_config = {"populate_by_name": True, "extra": "ignore"}

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "ProblemStep":
        """Enforce type-specific payload shape for step interaction widgets."""
        if self.type == "drag_drop":
            if not self.equation_parts:
                raise ValueError('type="drag_drop" requires non-empty "equationParts".')
            if self.input_fields or self.comparison_parts:
                raise ValueError('type="drag_drop" must not include "inputFields" or "comparisonParts".')
        elif self.type == "multi_input":
            if not self.input_fields:
                raise ValueError('type="multi_input" requires non-empty "inputFields".')
            if self.equation_parts or self.comparison_parts:
                raise ValueError('type="multi_input" must not include "equationParts" or "comparisonParts".')
        elif self.type == "comparison":
            if not self.comparison_parts or len(self.comparison_parts) != 2:
                raise ValueError('type="comparison" requires exactly 2 items in "comparisonParts".')
            if not self.comparison_parts[0].strip() or not self.comparison_parts[1].strip():
                raise ValueError('type="comparison": both "comparisonParts" strings must be non-empty.')
            if self.correct_answer not in ("<", ">", "="):
                raise ValueError('type="comparison" requires "correctAnswer" to be "<", ">", or "=".')
            if self.equation_parts or self.input_fields:
                raise ValueError('type="comparison" must not include "equationParts" or "inputFields".')
        return self


class ProblemOutput(BaseModel):
    """LLM output for generate_problem. Also used as the API response."""
    id: str
    title: str
    statement: str
    lesson: str = Field(validation_alias="topic")  # lesson name; alias for LLM/cache backward compat
    difficulty: Literal["easy", "medium", "hard"]
    level: int = Field(default=2, ge=1, le=3)
    # Set server-side after generation; not expected from the LLM.
    blueprint: Literal["solver", "recipe", "architect", "detective", "lawyer"] | None = None

    context_tag: str | None = Field(default=None, validation_alias="contextTag")
    steps: list[ProblemStep] = Field(min_length=3, max_length=6)

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def _wire_normalize_step_input_fields(cls, data: Any) -> Any:
        """Accept legacy ``inputFields`` / ``labeledValues``; strip them before model fields run."""
        return _coerce_problem_output_dict_before(data)


# Backward-compatible schema alias for legacy imports.
LabeledValue = InputField


class GenerateProblemRequest(BaseModel):
    class LessonContext(BaseModel):
        """Optional lesson metadata used to guide problem generation."""
        equations: list[str] = Field(default_factory=list)
        objectives: list[str] = Field(default_factory=list)
        key_rules: list[str] = Field(default_factory=list)
        misconceptions: list[str] = Field(default_factory=list)

    user_id: uuid.UUID | None = None   # enables playlist tracking when provided
    unit_id: str
    lesson_index: int
    lesson_name: str  # human-readable lesson name
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    level: int = Field(default=2, ge=1, le=3)
    interests: list[str] = Field(default_factory=list)
    grade_level: str | None = None
    focus_areas: list[str] = Field(default_factory=list)
    problem_style: str | None = None
    lesson_context: LessonContext | None = None
    exclude_ids: list[str] = Field(default_factory=list)  # e.g. current problem id so "See Another" returns a different one
    # When True: skip playlist resume check and force a fresh LLM generation.
    # Also bypasses the per-slot cap so the student always gets a brand-new problem.
    # Use for explicit "Try Another Problem" actions, not routine prefetches.
    force_regenerate: bool = False


class ProblemDeliveryResponse(BaseModel):
    """
    Wrapper returned by /problems/generate and /problems/navigate.

    Navigation fields are populated only when user_id is provided.
    When no user_id: current_index=0, total=1, has_prev/has_next=False.
    """
    problem: ProblemOutput
    current_index: int = 0         # 0-based position in user's playlist
    total: int = 1                 # problems in playlist so far
    max_problems: int = 5          # cap for this level
    has_prev: bool = False         # can navigate back
    has_next: bool = False         # can navigate forward (through seen problems)
    at_limit: bool = False         # reached max; generate will return current


# ── Reference Card ────────────────────────────────────────────


class ReferenceStepCard(BaseModel):
    """
    One step in the conceptual fiche de cours.
    Contains ONLY symbolic/conceptual text — no numerical examples.
    """
    label: str  # e.g. "Equation", "Identify Ions", "State Principle" — strategy-dependent
    content: str


class ReferenceCardOutput(BaseModel):
    """
    Lesson-level study reference card generated once by an LLM chain and
    persisted in the DB.  Returned as-is on subsequent requests.

    Design rule: no numbers, no worked examples — just the general method.
    """
    lesson: str = Field(validation_alias=AliasChoices("lesson", "topic"))  # lesson name; "topic" for DB/LLM compat
    unit_id: str
    lesson_index: int
    steps: list[ReferenceStepCard] = Field(min_length=3, max_length=5)
