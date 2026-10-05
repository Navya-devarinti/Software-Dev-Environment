from datetime import date

import pytest

from app.main import app
from app.corpus.models import Evidence, Source, SourceVersion, SourceVersionStatus
from app.rules.freshness import is_eligible_source_version

TODAY = date(2026, 10, 4)


@pytest.fixture
def schedule_evidence_factory():
    def create(
        *,
        status: SourceVersionStatus = SourceVersionStatus.CURRENT,
        last_reviewed_on: date = date(2026, 10, 1),
        effective_to: date | None = date(2026, 12, 31),
    ) -> Evidence:
        source = Source(
            title="Fall 2026 Academic Schedule",
            url="https://www.pnw.edu/academic-calendar/",
            category="schedule",
            owner_office="Registrar",
            review_frequency="term",
            last_reviewed_on=last_reviewed_on,
        )
        version = SourceVersion(
            source=source,
            status=status,
            effective_from=date(2026, 8, 1),
            effective_to=effective_to,
        )
        return Evidence(
            source_version=version,
            text="Add/drop deadline: September 8, 2026.",
            locator="Fall 2026 schedule, add/drop row",
            context={
                "term": "Fall 2026",
                "deadline_type": "add/drop",
                "date": "2026-09-08",
                "conditions": ["Refund eligibility depends on the date of withdrawal."],
            },
        )

    return create


def test_current_in_period_recently_reviewed_schedule_is_eligible(
    schedule_evidence_factory,
) -> None:
    evidence = schedule_evidence_factory()

    assert is_eligible_source_version(
        evidence.source_version, today=TODAY
    ) is True


@pytest.mark.parametrize(
    ("scenario", "version_kwargs"),
    [
        (
            "stale schedule review",
            {"last_reviewed_on": date(2026, 5, 1)},
        ),
        (
            "incomplete schedule",
            {"status": SourceVersionStatus.INCOMPLETE},
        ),
        (
            "unreviewed schedule",
            {"status": SourceVersionStatus.UNREVIEWED},
        ),
        (
            "superseded schedule",
            {"status": SourceVersionStatus.SUPERSEDED},
        ),
        (
            "expired schedule",
            {"effective_to": date(2026, 10, 3)},
        ),
    ],
)
def test_unsafe_schedule_evidence_is_not_eligible(
    schedule_evidence_factory, scenario: str, version_kwargs: dict
) -> None:
    evidence = schedule_evidence_factory(**version_kwargs)

    assert evidence.context["term"] == "Fall 2026", scenario
    assert (
        is_eligible_source_version(evidence.source_version, today=TODAY) is False
    ), scenario
