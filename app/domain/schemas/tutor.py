"""
Pydantic schemas for all AI tutor domain objects.

These serve two purposes:
  1. FastAPI request/response validation (the API contract)
  2. LangChain structured output parsing (LLM response schema)
"""

from typing import Literal
from pydantic import BaseModel, Field


# ── Problem Step ───────────────────────────────────────────────

class KnownVariable(BaseModel):
    """For Level 3 Step 2 — student identifies variables with values and units."""
    variable: str          # "[A]0", "k", "t"
    value: str             # "0.75" (student must fill this)
    unit: str              # "M", "M/s", "s"

    model_config = {"populate_by_name": True}


class ProblemStep(BaseModel):
    """
    One step in a chemistry problem.

    Step types by level:
      Level 1 (Worked Example):  all steps are "given"
      Level 2 (Faded):           steps 1-2 "given", steps 3-5 "interactive"
      Level 3 (Unresolved):      step 1 "drag_drop", step 2 "variable_id",
                                  steps 3-5 "interactive"
    """
    id: str
    step_number: int = Field(alias="stepNumber")
    type: Literal["given", "interactive", "drag_drop", "variable_id"]
    label: Literal["Equation", "Knowns", "Substitute", "Calculate", "Answer"]
    instruction: str

    # Populated for "given" steps and as reference in LLM output
    content: str | None = None

    # For "interactive" steps
    placeholder: str | None = None

    # For "drag_drop" steps (Level 3 Step 1)
    # Tokens the student arranges, e.g. ["[A]t", "=", "[A]0", "−", "k", "·", "t"]
    equation_parts: list[str] | None = Field(default=None, alias="equationParts")

    # For "variable_id" steps (Level 3 Step 2)
    # List of variables the student must identify with values+units
    known_variables: list[KnownVariable] | None = Field(default=None, alias="knownVariables")

    correct_answer: str | None = Field(default=None, alias="correctAnswer")
    hint: str | None = None

    model_config = {"populate_by_name": True}


class ProblemOutput(BaseModel):
    """LLM output for generate_problem. Also used as the API response."""
    id: str
    title: str
    # Full narrative scenario: "A sports drink manufacturer... [A]₀ = 0.80 M, k = 0.20 M/s..."
    # All given values must appear here so Step 2 can extract them.
    statement: str
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    level: int = Field(default=2, ge=1, le=3)  # 1=worked, 2=faded, 3=unresolved

    # Interest-based context tag used to personalise the scenario
    # e.g. "sports", "music", "food", "technology", "nature", "gaming",
    #       "art", "health", "dance", "movies"
    context_tag: str | None = Field(default=None, alias="contextTag")

    steps: list[ProblemStep] = Field(min_length=5, max_length=5)

    model_config = {"populate_by_name": True}


class GenerateProblemRequest(BaseModel):
    chapter_id: str
    topic_index: int
    topic_name: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    level: int = Field(default=2, ge=1, le=3)
    interests: list[str] = Field(default_factory=list)
    grade_level: str | None = None
    focus_areas: list[str] = Field(default_factory=list)
    problem_style: str | None = None
    rag_context: dict | None = None


# ── Answer Validation ─────────────────────────────────────────

class ValidationOutput(BaseModel):
    is_correct: bool
    feedback: str | None = None
    # Numeric details (populated for numeric steps)
    student_value: float | None = None
    correct_value: float | None = None
    unit_correct: bool | None = None
    validation_method: str | None = None  # "local_numeric" | "local_string" | "llm"


class ValidateAnswerRequest(BaseModel):
    student_answer: str
    correct_answer: str
    step_label: str
    step_type: str = "interactive"   # interactive | drag_drop | variable_id
    problem_context: str = ""


# ── Hints ─────────────────────────────────────────────────────

class HintOutput(BaseModel):
    hint: str
    hint_level: int = Field(ge=1, le=3, alias="hintLevel")

    model_config = {"populate_by_name": True}


class GenerateHintRequest(BaseModel):
    step_id: str
    step_label: str
    step_instruction: str
    student_input: str = ""
    correct_answer: str
    attempt_count: int = 1
    problem_context: str = ""
    interests: list[str] = Field(default_factory=list)
    grade_level: str | None = None
    rag_context: dict | None = None
    error_category: str | None = None
    misconception_tag: str | None = None


# ── Error Classification ──────────────────────────────────────

class StepError(BaseModel):
    step_id: str = Field(alias="stepId")
    category: Literal["conceptual", "procedural", "computational", "representation"]
    subcategory: Literal[
        "rate_law_understanding",
        "formula_setup",
        "variable_substitution",
        "arithmetic",
        "dimensional_awareness",
        "unit_mismatch",
        "graph_reading",
        "symbolic_notation",
    ]
    misconception_tag: str
    severity: Literal["blocking", "slowing", "minor"]
    description: str
    concept_missing: str | None = Field(default=None, alias="conceptMissing")
    suggested_intervention: Literal[
        "worked_example",
        "faded_example",
        "full_problem",
        "micro_hint",
        "concept_refresher",
        "arithmetic_drill",
        "unit_drill",
    ] = Field(alias="suggestedIntervention")

    model_config = {"populate_by_name": True}


class ThinkingEntry(BaseModel):
    """One entry in the Thinking Tracker panel."""
    step_label: str = Field(alias="stepLabel")
    reasoning_pattern: str = Field(alias="reasoningPattern")
    # Procedural | Conceptual | Units | Arithmetic | …
    student_input: str = Field(alias="studentInput")
    time_spent_seconds: int = Field(alias="timeSpentSeconds")
    is_correct: bool = Field(alias="isCorrect")

    model_config = {"populate_by_name": True}


class ErrorClassificationOutput(BaseModel):
    errors: list[StepError]
    thinking_entries: list[ThinkingEntry] = Field(
        default_factory=list, alias="thinkingEntries"
    )
    insight: str

    model_config = {"populate_by_name": True}


class ClassifyErrorsRequest(BaseModel):
    steps: list[dict]      # incorrect steps with studentInput, expectedValue, timeSpent
    all_steps: list[dict]  # all steps with isCorrect, timeSpent
    problem_context: str


# ── Exit Ticket ───────────────────────────────────────────────

class QCMOption(BaseModel):
    label: str
    value: str
    misconception_tag: str | None = None


class ExitTicketQuestion(BaseModel):
    question_order: int
    format: Literal["qcm", "structured"]
    question_text: str
    correct_answer: str
    unit: str | None = None
    equation_parts: list[str] | None = None
    qcm_options: list[QCMOption] | None = None


class ExitTicketOutput(BaseModel):
    questions: list[ExitTicketQuestion]


class GenerateExitTicketRequest(BaseModel):
    chapter_id: str
    topic_name: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    question_count: int = Field(default=3, ge=1, le=10)
    format: Literal["qcm", "structured", "mixed"] = "mixed"


# ── Class Insights ────────────────────────────────────────────

class ClassInsightsOutput(BaseModel):
    insights: list[str] = Field(min_length=1, max_length=5)


class GenerateInsightsRequest(BaseModel):
    student_count: int
    class_mastery: float = Field(ge=0.0, le=1.0)
    error_frequencies: dict[str, int]
    misconception_data: list[dict]
