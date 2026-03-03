"""
Tutor schemas — API contract and LLM structured output.

Re-exports for backward compatibility: from app.domain.schemas.tutor import ProblemOutput
"""

from app.domain.schemas.tutor.errors import (
    ClassifyErrorsRequest,
    ErrorClassificationOutput,
    StepError,
    ThinkingEntry,
)
from app.domain.schemas.tutor.exit_ticket import (
    ExitTicketOutput,
    ExitTicketQuestion,
    GenerateExitTicketRequest,
    QCMOption,
)
from app.domain.schemas.tutor.hints import GenerateHintRequest, HintOutput
from app.domain.schemas.tutor.insights import ClassInsightsOutput, GenerateInsightsRequest
from app.domain.schemas.tutor.problems import (
    GenerateProblemRequest,
    KnownVariable,
    ProblemDeliveryResponse,
    ProblemOutput,
    ProblemStep,
)
from app.domain.schemas.tutor.validation import ValidateAnswerRequest, ValidationOutput

__all__ = [
    "ClassifyErrorsRequest",
    "ClassInsightsOutput",
    "ErrorClassificationOutput",
    "ExitTicketOutput",
    "ExitTicketQuestion",
    "GenerateExitTicketRequest",
    "GenerateHintRequest",
    "GenerateInsightsRequest",
    "GenerateProblemRequest",
    "HintOutput",
    "KnownVariable",
    "ProblemDeliveryResponse",
    "ProblemOutput",
    "ProblemStep",
    "QCMOption",
    "StepError",
    "ThinkingEntry",
    "ValidateAnswerRequest",
    "ValidationOutput",
]
