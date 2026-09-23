from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Context(BaseModel):
    """Optional public context for a question."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    campus: Literal["Hammond", "Westville"] | None = None
    term: str | None = None
    program: str | None = None
    course_code: str | None = Field(default=None, alias="courseCode")
    academic_level: Literal["undergraduate", "graduate"] | None = Field(
        default=None, alias="academicLevel"
    )


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    url: str
    locator: str


class Escalation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    office: str
    reason: str
    contact_url: str | None = Field(default=None, alias="contactUrl")


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1, max_length=2000)
    context: Context | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["answered", "needs_context", "cannot_verify", "escalation_required"]
    message: str
    required_context: list[Literal["campus", "term", "program", "courseCode", "academicLevel"]] = Field(
        default_factory=list, alias="requiredContext"
    )
    citations: list[Citation] = Field(default_factory=list)
    escalation: Escalation | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Error(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Literal["invalid_request", "student_data_not_allowed"]
    message: str
