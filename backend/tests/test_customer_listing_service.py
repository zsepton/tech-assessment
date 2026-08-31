from typing import Any

from app.models.outreach import OutreachStatus
from app.models.risk import RiskTier
from app.services.customer_listing import CustomerListFilters, list_matching_customers

BASE: dict[str, Any] = {
    "gender": "Female",
    "senior_citizen": False,
    "partner": False,
    "dependents": False,
    "tenure": 1,
    "phone_service": True,
    "multiple_lines": "No",
    "internet_service": "Fiber optic",
    "online_security": "No",
    "online_backup": "No",
    "device_protection": "No",
    "tech_support": "No",
    "streaming_tv": "No",
    "streaming_movies": "No",
    "contract": "Month-to-month",
    "paperless_billing": True,
    "payment_method": "Electronic check",
    "monthly_charges": 90.0,
    "total_charges": 90.0,
    "churn": False,
}


def _customer(customer_id: str, **overrides: Any) -> dict[str, Any]:
    """A High-risk customer by default (score 92); override fields to vary it."""
    return {**BASE, "customer_id": customer_id, **overrides}


HIGH_RISK = _customer("high-1")
LOW_RISK = _customer(
    "low-1",
    contract="Two year",
    tenure=60,
    payment_method="Mailed check",
    tech_support="Yes",
    online_security="Yes",
    paperless_billing=False,
    monthly_charges=20.0,
    total_charges=1200.0,
)


def test_no_filters_returns_everyone_sorted_by_score_descending() -> None:
    page = list_matching_customers([LOW_RISK, HIGH_RISK], CustomerListFilters(), offset=0, limit=10)

    assert [c.customer_id for c, _ in page.items] == ["high-1", "low-1"]
    assert page.total == 2


def test_filters_by_risk_tier() -> None:
    page = list_matching_customers(
        [HIGH_RISK, LOW_RISK], CustomerListFilters(risk_tier=RiskTier.HIGH), offset=0, limit=10
    )

    assert [c.customer_id for c, _ in page.items] == ["high-1"]
    assert page.total == 1


def test_filters_by_contract() -> None:
    page = list_matching_customers(
        [HIGH_RISK, LOW_RISK], CustomerListFilters(contract="Two year"), offset=0, limit=10
    )

    assert [c.customer_id for c, _ in page.items] == ["low-1"]


def test_filters_by_outreach_status() -> None:
    in_progress = _customer("in-progress-1", outreach_status="IN_PROGRESS")

    page = list_matching_customers(
        [HIGH_RISK, in_progress],
        CustomerListFilters(outreach_status=OutreachStatus.IN_PROGRESS),
        offset=0,
        limit=10,
    )

    assert [c.customer_id for c, _ in page.items] == ["in-progress-1"]


def test_combined_filters_narrow_results() -> None:
    page = list_matching_customers(
        [HIGH_RISK, LOW_RISK],
        CustomerListFilters(risk_tier=RiskTier.HIGH, contract="Month-to-month"),
        offset=0,
        limit=10,
    )

    assert [c.customer_id for c, _ in page.items] == ["high-1"]


def test_filters_matching_nothing_return_empty_page() -> None:
    page = list_matching_customers(
        [HIGH_RISK, LOW_RISK],
        CustomerListFilters(risk_tier=RiskTier.LOW, contract="Month-to-month"),
        offset=0,
        limit=10,
    )

    assert page.items == []
    assert page.total == 0


def test_total_reflects_filtered_count_not_page_size() -> None:
    customers = [_customer(f"high-{i}") for i in range(5)]

    page = list_matching_customers(customers, CustomerListFilters(), offset=0, limit=2)

    assert page.total == 5
    assert len(page.items) == 2


def test_pagination_offset_and_limit_slice_the_sorted_results() -> None:
    customers = [_customer(f"high-{i}") for i in range(5)]

    page = list_matching_customers(customers, CustomerListFilters(), offset=2, limit=2)

    assert [c.customer_id for c, _ in page.items] == ["high-2", "high-3"]


def test_customer_id_is_the_tiebreaker_for_equal_scores() -> None:
    customers = [_customer("b-customer"), _customer("a-customer")]

    page = list_matching_customers(customers, CustomerListFilters(), offset=0, limit=10)

    assert [c.customer_id for c, _ in page.items] == ["a-customer", "b-customer"]
