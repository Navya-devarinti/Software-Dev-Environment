from __future__ import annotations

FALLBACK_ROUTE = {
    "office": "Dean of Students Office",
    "reason": "No approved office mapping was identified for this request, so the documented fallback route is the Dean of Students Office.",
    "contactUrl": "https://www.pnw.edu/student-affairs/",
}


ROUTE_MAP = {
    "registration": {
        "office": "Registrar's Office",
        "reason": "Registration and course schedule questions need registrar guidance.",
        "contactUrl": "https://www.pnw.edu/registrar/",
    },
    "graduation": {
        "office": "Academic Advising",
        "reason": "Graduation and program requirements require advisor review for individualized determination.",
        "contactUrl": "https://www.pnw.edu/advising/",
    },
    "parking": {
        "office": "Parking Services",
        "reason": "Parking-policy and ticket questions should be routed to the office that oversees parking guidance.",
        "contactUrl": "https://www.pnw.edu/parking/",
    },
    "financial_aid": {
        "office": "Financial Aid Office",
        "reason": "Financial-aid questions require the official office responsible for aid policies and eligibility.",
        "contactUrl": "https://www.pnw.edu/financial-aid/",
    },
}


def resolve_office_route(category: str | None) -> dict:
    category_key = (category or "").strip().lower().replace(" ", "_")
    if category_key in ROUTE_MAP:
        return ROUTE_MAP[category_key]
    return FALLBACK_ROUTE
