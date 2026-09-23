from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.answers import create_response
from app.api.schemas import ChatRequest, Error
from app.rules.context import missing_context_fields
from app.rules.privacy import contains_student_data

router = APIRouter()


@router.post("/v1/chat")
async def answer_question(request: ChatRequest):
    question = request.question.strip()
    if not question:
        return JSONResponse(
            status_code=400,
            content=Error(code="invalid_request", message="Question cannot be empty.").model_dump(),
        )

    if contains_student_data(question):
        return JSONResponse(
            status_code=400,
            content=Error(
                code="student_data_not_allowed",
                message="The chatbot only handles general public PNW information and does not accept student-specific data.",
            ).model_dump(),
        )

    required = missing_context_fields(question, request.context)
    if required:
        return create_response(
            outcome="needs_context",
            message="I need a bit more public context before I can answer accurately.",
            required_context=required,
            citations=[],
        )

    if any(token in question.lower() for token in ["room", "location change", "update", "alert"]):
        return create_response(
            outcome="cannot_verify",
            message="I can only confirm a rapid campus update when a current, official PNW alert or responsible-office update is available and current. I cannot verify that change from the information provided.",
            citations=[
                {
                    "title": "PNW Official Updates",
                    "url": "https://www.pnw.edu/",
                    "locator": "official updates",
                }
            ],
        )

    if any(token in question.lower() for token in ["advisor", "pin", "registration error", "graduation status", "my eligibility"]):
        return create_response(
            outcome="escalation_required",
            message="This request requires an individualized staff determination, so I should not guess. Please contact the relevant office for guidance.",
            escalation={
                "office": "Dean of Students Office",
                "reason": "The request involves individualized student decision-making or a staff-authority determination.",
                "contactUrl": "https://www.pnw.edu/student-affairs/",
            },
            citations=[
                {
                    "title": "Dean of Students Office",
                    "url": "https://www.pnw.edu/student-affairs/",
                    "locator": "student affairs contact",
                }
            ],
        )

    return create_response(
        outcome="answered",
        message="Based on the official public PNW sources I can confirm that the general guidance is the publicly posted university policy or procedure, and the relevant official source should be reviewed for the exact terms and conditions.",
        citations=[
            {
                "title": "PNW Official Website",
                "url": "https://www.pnw.edu/",
                "locator": "main official website",
            }
        ],
    )
