"""Request bodies for student exit ticket APIs."""

from pydantic import BaseModel, Field, field_validator


class ExitTicketSubmitBody(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)
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

