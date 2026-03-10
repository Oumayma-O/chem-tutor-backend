"""Problem generation schemas."""

import uuid
from typing import Literal
from pydantic import AliasChoices, BaseModel, Field, model_validator


class LabeledValue(BaseModel):
    """
    A labeled sub-part of a multi-value step answer.
    Used by type="variable_id" steps whenever a step's answer has multiple
    distinct labeled pieces (not limited to identifying 'known' variables).
    """
    variable: str
    value: str
    unit: str

    model_config = {"populate_by_name": True}


class ProblemStep(BaseModel):
    """
    One step in a chemistry problem.

    Widget types (chosen based on what the student is doing, not just the level):
      "given"       — read-only teaching step (always shown)
      "interactive" — single micro-input text box
      "drag_drop"   — assemble an equation/formula by arranging parts
      "variable_id" — student identifies/inputs multiple labeled sub-values
      "comparison"  — student compares two things with <, >, or =
    """
    id: str = ""  # LLM often omits; service fills with problem_id + step_number if empty
    step_number: int = Field(validation_alias="stepNumber")
    type: Literal["given", "interactive", "drag_drop", "variable_id", "comparison"]
    label: str
    instruction: str
    explanation: str | None = Field(
        default=None,
        description=(
            "Max 20 words. One-sentence show-your-work trace explaining how correctAnswer was found. "
            "Displayed in Level 1 (worked example) and on wrong answers in L2/L3."
        ),
    )
    skill_used: str | None = Field(default=None, validation_alias="skillUsed")
    correct_answer: str | None = Field(default=None, validation_alias="correctAnswer")
    equation_parts: list[str] | None = Field(default=None, validation_alias="equationParts")
    labeled_values: list[LabeledValue] | None = Field(default=None, validation_alias="labeledValues")
    comparison_parts: list[str] | None = Field(default=None, validation_alias="comparisonParts")

    # No "hint" field: hints are generated on demand via POST /problems/hint.
    model_config = {"populate_by_name": True, "extra": "ignore"}

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "ProblemStep":
        """Enforce type-specific payload shape for step interaction widgets."""
        if self.type == "drag_drop":
            if not self.equation_parts:
                raise ValueError('type="drag_drop" requires non-empty "equationParts".')
            if self.labeled_values or self.comparison_parts:
                raise ValueError('type="drag_drop" must not include "labeledValues" or "comparisonParts".')
        elif self.type == "variable_id":
            if not self.labeled_values:
                raise ValueError('type="variable_id" requires non-empty "labeledValues".')
            if self.equation_parts or self.comparison_parts:
                raise ValueError('type="variable_id" must not include "equationParts" or "comparisonParts".')
        elif self.type == "comparison":
            if not self.comparison_parts or len(self.comparison_parts) != 2:
                raise ValueError('type="comparison" requires exactly 2 items in "comparisonParts".')
            if self.correct_answer not in ("<", ">", "="):
                raise ValueError('type="comparison" requires "correctAnswer" to be "<", ">", or "=".')
            if self.equation_parts or self.labeled_values:
                raise ValueError('type="comparison" must not include "equationParts" or "labeledValues".')
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
    hint: str = "Apply this general approach to the current problem!"
