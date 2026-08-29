import pytest
from app.models import (
    Customer,
    OutreachStatus,
    OutreachUpdateRequest,
    RiskFactor,
    RiskScore,
    RiskTier,
)
from fastapi import FastAPI
from pydantic import ValidationError

VALID_CUSTOMER_KWARGS = {
    "customer_id": "7590-VHVEG",
    "gender": "Female",
    "senior_citizen": False,
    "partner": True,
    "dependents": False,
    "tenure": 1,
    "phone_service": False,
    "multiple_lines": "No phone service",
    "internet_service": "DSL",
    "online_security": "No",
    "online_backup": "Yes",
    "device_protection": "No",
    "tech_support": "No",
    "streaming_tv": "No",
    "streaming_movies": "No",
    "contract": "Month-to-month",
    "paperless_billing": True,
    "payment_method": "Electronic check",
    "monthly_charges": 29.85,
    "total_charges": 29.85,
    "churn": False,
}


def test_customer_defaults_to_not_contacted() -> None:
    customer = Customer(**VALID_CUSTOMER_KWARGS)

    assert customer.outreach_status == OutreachStatus.NOT_CONTACTED


def test_customer_rejects_negative_tenure() -> None:
    with pytest.raises(ValidationError):
        Customer(**{**VALID_CUSTOMER_KWARGS, "tenure": -1})


def test_outreach_update_request_accepts_valid_status() -> None:
    request = OutreachUpdateRequest(status=OutreachStatus.IN_PROGRESS)

    assert request.status == OutreachStatus.IN_PROGRESS


def test_outreach_update_request_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        OutreachUpdateRequest(status="NOT_A_REAL_STATUS")


def test_risk_score_holds_factor_breakdown() -> None:
    risk_score = RiskScore(
        score=91,
        tier=RiskTier.HIGH,
        factors=[
            RiskFactor(
                name="Contract: month-to-month", contribution=28, direction="increases_risk"
            ),
            RiskFactor(name="Tenure: 2 months", contribution=24, direction="increases_risk"),
        ],
    )

    assert risk_score.tier == RiskTier.HIGH
    assert len(risk_score.factors) == 2
    assert risk_score.factors[0].direction == "increases_risk"


def test_risk_score_rejects_out_of_range_score() -> None:
    with pytest.raises(ValidationError):
        RiskScore(score=101, tier=RiskTier.HIGH, factors=[])


def test_models_appear_in_openapi_schema() -> None:
    schema_app = FastAPI()

    @schema_app.get("/customer", response_model=Customer)
    def _get_customer() -> Customer:  # pragma: no cover - never called, route for schema only
        raise NotImplementedError

    @schema_app.get("/risk", response_model=RiskScore)
    def _get_risk() -> RiskScore:  # pragma: no cover - never called, route for schema only
        raise NotImplementedError

    @schema_app.patch("/outreach")
    def _patch_outreach(
        body: OutreachUpdateRequest,
    ) -> None:  # pragma: no cover - never called, route for schema only
        raise NotImplementedError

    schema = schema_app.openapi()
    component_names = schema["components"]["schemas"].keys()

    assert "Customer" in component_names
    assert "RiskScore" in component_names
    assert "RiskFactor" in component_names
    assert "OutreachUpdateRequest" in component_names
