from __future__ import annotations

from typing import Sequence

from app.api.schemas import ChatResponse, Citation, Escalation


def create_response(
    *,
    outcome: str,
    message: str,
    required_context: Sequence[str] | None = None,
    citations: Sequence[dict | Citation] | None = None,
    escalation: dict | Escalation | None = None,
) -> ChatResponse:
    return ChatResponse(
        outcome=outcome,
        message=message,
        requiredContext=list(required_context or []),
        citations=[
            Citation(**c) if isinstance(c, dict) else c for c in (citations or [])
        ],
        escalation=(Escalation(**escalation) if isinstance(escalation, dict) else escalation),
    )
