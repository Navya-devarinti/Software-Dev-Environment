from __future__ import annotations


STUDENT_DATA_PATTERNS = [
    "my pin",
    "my schedule",
    "my transcript",
    "my student id",
    "student id",
    "my record",
    "my graduation eligibility",
    "my registration",
    "my advisor",
    "my balance",
    "my financial aid",
    "my account",
    "my student profile",
    "my plan of study",
    "my grades",
]


def contains_student_data(question: str) -> bool:
    q = (question or "").lower()
    return any(pattern in q for pattern in STUDENT_DATA_PATTERNS)
