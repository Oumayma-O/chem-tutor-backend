"""Problem generation schemas."""

import uuid
from typing import Literal
from pydantic import BaseModel, Field


class KnownVariable(BaseModel):
    """For Level 3 Step 2 — student identifies variables with values and units."""
    variable: str
    value: str
    unit: str

    model_config = {"populate_by_name": True}


class ProblemStep(BaseModel):
    """
    One step in a chemistry problem.

    Step types by level:
      Level 1 (Worked Example):  all steps are "given"
      Level 2 (Faded):           steps 1-2 "given", steps 3-5 "interactive"
      Level 3 (Unresolved):     step 1 "drag_drop", step 2 "variable_id",
                                 steps 3-5 "interactive"
    """
    id: str
    step_number: int = Field(alias="stepNumber")
    type: Literal["given", "interactive", "drag_drop", "variable_id"]
    label: Literal["Equation", "Knowns", "Substitute", "Calculate", "Answer"]
    instruction: str

    content: str | None = None
    placeholder: str | None = None
    equation_parts: list[str] | None = Field(default=None, alias="equationParts")
    known_variables: list[KnownVariable] | None = Field(default=None, alias="knownVariables")
    correct_answer: str | None = Field(default=None, alias="correctAnswer")
    hint: str | None = None

    model_config = {"populate_by_name": True}


class ProblemOutput(BaseModel):
    """LLM output for generate_problem. Also used as the API response."""
    id: str
    title: str
    statement: str
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
    level: int = Field(default=2, ge=1, le=3)

    context_tag: str | None = Field(default=None, alias="contextTag")
    steps: list[ProblemStep] = Field(min_length=5, max_length=5)

    model_config = {"populate_by_name": True}


class GenerateProblemRequest(BaseModel):
    user_id: uuid.UUID | None = None   # enables playlist tracking when provided
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
