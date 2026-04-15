"""Request bodies for student exit ticket APIs."""

from pydantic import BaseModel, Field, field_validator


class ExitTicketSubmitBody(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)
    # Per-question correctness as determined by the frontend grader (apiValidateStep / MCQ match).
    # Keyed by question id, same as `answers`. When provided these are stored on each answer row and
    # the score is derived from them rather than re-calculated with naive string comparison.
    results: dict[str, bool] = Field(default_factory=dict)
    # Overall score 0–100 pre-computed by the frontend.  Stored directly when present so the value
    # shown to the teacher matches exactly what the student saw.
    score_percent: float | None = Field(default=None, ge=0, le=100)
    # Seconds spent on the exit ticket from first question shown to submission.
    time_spent_s: int = Field(default=0, ge=0)

    @field_validator("answers", mode="before")
    @classmethod
    def coerce_answers_to_str_map(cls, v: object) -> dict[str, str]:
        """Accept numeric or other JSON values from clients; DB expects string answers."""
        if not isinstance(v, dict):
            return {}
        out: dict[str, str] = {}
        for k, val in v.items():
            key = str(k)
            if val is None:
                out[key] = ""
            elif isinstance(val, str):
                out[key] = val
            else:
                out[key] = str(val)
        return out

    @field_validator("results", mode="before")
    @classmethod
    def coerce_results(cls, v: object) -> dict[str, bool]:
        if not isinstance(v, dict):
            return {}
        return {str(k): bool(val) for k, val in v.items()}
