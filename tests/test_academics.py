from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.corpus import retrieval


CATALOG_URL = "https://www.pnw.edu/academic-catalog/"


def catalog_evidence(
    *,
    title: str,
    text: str,
    locator: str,
    context: dict[str, str],
    url: str = CATALOG_URL,
) -> SimpleNamespace:
    source = SimpleNamespace(
        title=title,
        url=url,
        category="catalog",
        related_source=None,
        related_sources=[],
    )
    version = SimpleNamespace(status="current", source=source)
    return SimpleNamespace(
        text=text,
        locator=locator,
        context=context,
        source_version=version,
    )


def install_catalog_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    evidence_items: list[SimpleNamespace],
    requested_context: dict[str, str],
) -> None:
    rows = [
        (item, item.source_version.source.title, "catalog", index / 10)
        for index, item in enumerate(evidence_items)
    ]

    class Session:
        def __enter__(self) -> Session:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def execute(self, statement: Any) -> SimpleNamespace:
            compiled = statement.compile()
            params = compiled.params
            matching_rows = list(rows)
            for field, requested_value in requested_context.items():
                if field in params.values() and requested_value in params.values():
                    matching_rows = [
                        row
                        for row in matching_rows
                        if row[0].context.get(field) in (None, requested_value)
                    ]
            return SimpleNamespace(all=lambda: matching_rows)

    monkeypatch.setattr(retrieval, "SessionLocal", Session)
    monkeypatch.setattr(retrieval, "embed_texts", lambda _texts: [[0.0] * 768])


def test_prerequisite_retrieval_preserves_catalog_source_and_locator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prerequisite = catalog_evidence(
        title="Computer Science Course Descriptions",
        text="CS 202 requires CS 101 with a grade of C or better.",
        locator="2026-2027 Catalog, Computer Science, CS 202",
        context={"courseCode": "CS 202"},
        url=f"{CATALOG_URL}computer-science/",
    )
    install_catalog_retrieval(
        monkeypatch, [prerequisite], {"courseCode": "CS 202"}
    )

    results = retrieval.retrieve_evidence(
        "What is the prerequisite for CS 202?",
        context={"courseCode": "CS 202"},
        category="catalog",
    )

    assert len(results) == 1
    result = results[0]
    assert result.text == "CS 202 requires CS 101 with a grade of C or better."
    assert result.metadata["courseCode"] == "CS 202"
    assert result.source_title == "Computer Science Course Descriptions"
    assert result.source_url == f"{CATALOG_URL}computer-science/"
    assert result.locator == "2026-2027 Catalog, Computer Science, CS 202"
    assert result.source_version.source.url == result.source_url


def test_prerequisite_retrieval_does_not_use_an_unrelated_course(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_course = catalog_evidence(
        title="Computer Science Course Descriptions",
        text="CS 202 requires CS 101.",
        locator="Catalog, CS 202",
        context={"courseCode": "CS 202"},
    )
    unrelated_course = catalog_evidence(
        title="Mathematics Course Descriptions",
        text="MA 202 requires MA 101.",
        locator="Catalog, MA 202",
        context={"courseCode": "MA 202"},
        url=f"{CATALOG_URL}mathematics/",
    )
    install_catalog_retrieval(
        monkeypatch,
        [requested_course, unrelated_course],
        {"courseCode": "CS 202"},
    )

    results = retrieval.retrieve_evidence(
        "What is the prerequisite for CS 202?",
        context={"courseCode": "CS 202"},
        category="catalog",
    )

    assert [result.metadata["courseCode"] for result in results] == ["CS 202"]
    assert [result.text for result in results] == ["CS 202 requires CS 101."]


def test_offering_retrieval_keeps_course_details_and_excludes_other_courses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_offering = catalog_evidence(
        title="CS 101 Course Offerings",
        text="CS 101 is offered at Hammond in Fall 2026, section 01 at 10:30 a.m.",
        locator="Fall 2026, CS 101, section 01",
        context={
            "courseCode": "CS 101",
            "campus": "Hammond",
            "term": "Fall 2026",
        },
    )
    unrelated_offering = catalog_evidence(
        title="CS 201 Course Offerings",
        text="CS 201 is offered at Westville in Fall 2026, section 02.",
        locator="Fall 2026, CS 201, section 02",
        context={
            "courseCode": "CS 201",
            "campus": "Westville",
            "term": "Fall 2026",
        },
        url=f"{CATALOG_URL}course-schedule/",
    )
    install_catalog_retrieval(
        monkeypatch,
        [requested_offering, unrelated_offering],
        {"courseCode": "CS 101", "campus": "Hammond"},
    )

    results = retrieval.retrieve_evidence(
        "Where and when is CS 101 offered?",
        context={"courseCode": "CS 101", "campus": "Hammond"},
        category="catalog",
    )

    assert len(results) == 1
    result = results[0]
    assert result.text == (
        "CS 101 is offered at Hammond in Fall 2026, section 01 at 10:30 a.m."
    )
    assert result.metadata["courseCode"] == "CS 101"
    assert result.metadata["campus"] == "Hammond"
    assert result.metadata["term"] == "Fall 2026"
    assert result.source_title == "CS 101 Course Offerings"
    assert result.source_url == CATALOG_URL
    assert result.locator == "Fall 2026, CS 101, section 01"


def test_campus_context_excludes_catalog_evidence_for_another_campus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hammond = catalog_evidence(
        title="Hammond Course Offerings",
        text="CS 101 is available at Hammond.",
        locator="Hammond, CS 101",
        context={"courseCode": "CS 101", "campus": "Hammond"},
    )
    westville = catalog_evidence(
        title="Westville Course Offerings",
        text="CS 101 is available at Westville.",
        locator="Westville, CS 101",
        context={"courseCode": "CS 101", "campus": "Westville"},
        url=f"{CATALOG_URL}westville/",
    )
    install_catalog_retrieval(
        monkeypatch,
        [hammond, westville],
        {"courseCode": "CS 101", "campus": "Hammond"},
    )

    results = retrieval.retrieve_evidence(
        "Is CS 101 available at Hammond?",
        context={"courseCode": "CS 101", "campus": "Hammond"},
        category="catalog",
    )

    assert [(result.metadata["campus"], result.text) for result in results] == [
        ("Hammond", "CS 101 is available at Hammond.")
    ]


def test_academic_level_context_excludes_other_level_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    undergraduate = catalog_evidence(
        title="Undergraduate Catalog",
        text="The undergraduate CS program requires CS 202.",
        locator="Undergraduate catalog, Computer Science requirements",
        context={"academicLevel": "undergraduate"},
    )
    graduate = catalog_evidence(
        title="Graduate Catalog",
        text="The graduate CS program requires CS 501.",
        locator="Graduate catalog, Computer Science requirements",
        context={"academicLevel": "graduate"},
        url=f"{CATALOG_URL}graduate/",
    )
    install_catalog_retrieval(
        monkeypatch,
        [undergraduate, graduate],
        {"academicLevel": "undergraduate"},
    )

    results = retrieval.retrieve_evidence(
        "What are the computer science requirements?",
        context={"academicLevel": "undergraduate"},
        category="catalog",
    )

    assert [
        (result.metadata["academicLevel"], result.text) for result in results
    ] == [
        (
            "undergraduate",
            "The undergraduate CS program requires CS 202.",
        )
    ]


def test_program_context_excludes_other_program_but_keeps_general_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_program = catalog_evidence(
        title="Computer Science Catalog",
        text="Computer Science requires CS 202.",
        locator="Computer Science requirements",
        context={"program": "Computer Science"},
    )
    unrelated_program = catalog_evidence(
        title="Mathematics Catalog",
        text="Mathematics requires MA 202.",
        locator="Mathematics requirements",
        context={"program": "Mathematics"},
        url=f"{CATALOG_URL}mathematics/",
    )
    general_catalog = catalog_evidence(
        title="General Academic Catalog",
        text="All programs must satisfy the university-wide requirements.",
        locator="University-wide requirements",
        context={},
        url=f"{CATALOG_URL}general/",
    )
    install_catalog_retrieval(
        monkeypatch,
        [requested_program, unrelated_program, general_catalog],
        {"program": "Computer Science"},
    )

    results = retrieval.retrieve_evidence(
        "What are the Computer Science requirements?",
        context={"program": "Computer Science"},
        category="catalog",
    )

    assert [result.text for result in results] == [
        "Computer Science requires CS 202.",
        "All programs must satisfy the university-wide requirements.",
    ]
