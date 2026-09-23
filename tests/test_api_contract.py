from openapi_spec_validator import validate_spec

from app.main import app


def test_openapi_contract_matches_generated_schema() -> None:
    validate_spec(app.openapi())
