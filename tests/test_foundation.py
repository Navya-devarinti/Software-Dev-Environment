from fastapi.testclient import TestClient

from app.main import app
from app.rules.context import missing_context_fields
from app.rules.privacy import contains_student_data

client = TestClient(app)


def test_public_context_missing_triggers_need_context() -> None:
    response = client.post(
        "/v1/chat",
        json={"question": "When is the add/drop deadline for this semester?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "needs_context"
    assert "term" in payload["requiredContext"]


def test_student_specific_request_is_rejected() -> None:
    response = client.post(
        "/v1/chat",
        json={"question": "What is my registration status and PIN?"},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "student_data_not_allowed"


def test_context_rules_detect_missing_fields() -> None:
    fields = missing_context_fields("What are the course prerequisites for CS 101?", {})
    assert "courseCode" in fields


def test_student_data_detection() -> None:
    assert contains_student_data("What is my graduation eligibility?") is True
