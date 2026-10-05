from __future__ import annotations

from inspect import Parameter, signature

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.answers import (
    create_response,
    render_academic_answer,
    render_deadline_answer,
    render_policy_answer,
)
from app.api.schemas import ChatRequest, Error
from app.corpus.retrieval import retrieve_evidence
from app.rules.context import missing_context_fields
from app.rules.deadlines import classify_deadline_question, evaluate_deadline
from app.rules.privacy import contains_student_data
from app.rules.academics import (
    evaluate_academic_question,
    is_general_academic_question,
    is_individual_academic_question,
)
from app.rules.policies import summarize_policy

router = APIRouter()

_POLICY_TERMS = (
    "policy",
    "procedure",
    "parking",
    "citation",
    "ticket",
    "grade appeal",
    "appeal process",
    "academic standing",
    "registration process",
    "register for",
)


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

    if classify_deadline_question(question) == "deadline":
        term = (
            request.context.term.strip()
            if request.context and request.context.term
            else ""
        )
        if not term:
            return render_deadline_answer(
                evaluate_deadline(question, term=None)
            )

        context = {"term": term}
        evidence_results = retrieve_evidence(question, context=context)
        categorized_results = [
            evidence
            for evidence in evidence_results
            if isinstance(getattr(evidence, "metadata", None), dict)
            and evidence.metadata.get("category") is not None
        ]
        schedule_evidence = next(
            (
                evidence
                for evidence in categorized_results
                if evidence.metadata.get("category") == "schedule"
            ),
            None,
        )
        if not categorized_results:
            schedule_evidence = next(iter(evidence_results), None)

        decision = evaluate_deadline(
            question,
            term=term,
            evidence=schedule_evidence,
        )
        return render_deadline_answer(decision)

    if _is_policy_question(question):
        context = (
            request.context.model_dump(by_alias=True, exclude_none=True)
            if request.context
            else None
        )
        evidence_results = _retrieve_policy_evidence(question, context=context)
        decision = summarize_policy(question, evidence=evidence_results)
        return render_policy_answer(decision)

    if _is_academic_question(question):
        context = (
            request.context.model_dump(by_alias=True, exclude_none=True)
            if request.context
            else None
        )
        evidence_results = retrieve_evidence(
            question,
            context=context,
            category="catalog",
        )
        decision = evaluate_academic_question(
            question,
            evidence=evidence_results,
            context=context,
        )
        return render_academic_answer(decision)

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


def _is_policy_question(question: str) -> bool:
    normalized = question.lower()
    return any(term in normalized for term in _POLICY_TERMS)


def _is_academic_question(question: str) -> bool:
    return is_individual_academic_question(question) or is_general_academic_question(
        question
    )


def _is_individual_graduation_question(question: str) -> bool:
    normalized = question.casefold()
    return (
        is_individual_academic_question(question)
        and any(term in normalized for term in ("graduate", "graduation", "graduating"))
    )


def _is_general_public_requirement_question(question: str) -> bool:
    normalized = question.casefold()
    return (
        any(term in normalized for term in ("requirement", "requirements"))
        and is_general_academic_question(question)
    )


def _retrieve_policy_evidence(question: str, *, context: dict | None):
    """Keep compatibility with retriever adapters predating category selection."""
    parameters = signature(retrieve_evidence).parameters.values()
    accepts_category = any(
        parameter.name == "category"
        or parameter.kind is Parameter.VAR_KEYWORD
        for parameter in parameters
    )
    if accepts_category:
        return retrieve_evidence(question, context=context, category="policy")
    return retrieve_evidence(question, context=context)
