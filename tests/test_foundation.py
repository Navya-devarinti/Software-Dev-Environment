from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.rules.context import missing_context_fields
from app.rules.freshness import (
    is_current_effective_period,
    is_current_status,
    is_eligible_source_version,
    is_reviewed_recently,
)
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


def test_current_status_and_effective_dates_are_evaluated_inclusively() -> None:
    assert is_current_status("CURRENT") is True
    assert is_current_status("current") is True
    assert is_current_effective_period("2025-01-01", "2025-12-31", today=date(2025, 1, 1)) is True
    assert is_current_effective_period("2025-01-01", "2025-12-31", today=date(2025, 12, 31)) is True
    assert is_current_effective_period("2025-01-01", "2025-12-31", today=date(2024, 12, 31)) is False


def test_review_freshness_uses_cadence_rules() -> None:
    assert is_reviewed_recently("2025-01-01", "daily", today=date(2025, 1, 2)) is True
    assert is_reviewed_recently("2025-01-01", "daily", today=date(2025, 1, 3)) is False
    assert is_reviewed_recently("2025-01-01", "term", today=date(2025, 4, 30)) is True
    assert is_reviewed_recently("2025-01-01", "annual", today=date(2025, 12, 31)) is True


def test_source_version_eligibility_requires_current_fresh_status() -> None:
    class Source:
        def __init__(self, last_reviewed_on, review_frequency):
            self.last_reviewed_on = last_reviewed_on
            self.review_frequency = review_frequency

    class Version:
        def __init__(self, status, effective_from, effective_to, source):
            self.status = status
            self.effective_from = effective_from
            self.effective_to = effective_to
            self.source = source

    source = Source("2025-01-02", "daily")
    version = Version("current", "2025-01-01", "2025-12-31", source)
    assert is_eligible_source_version(version, today=date(2025, 1, 2)) is True

    source_old = Source("2025-01-01", "daily")
    version_old = Version("current", "2025-01-01", "2025-12-31", source_old)
    assert is_eligible_source_version(version_old, today=date(2025, 1, 3)) is False

    version_stale = Version("superseded", "2025-01-01", "2025-12-31", source)
    assert is_eligible_source_version(version_stale, today=date(2025, 1, 2)) is False
