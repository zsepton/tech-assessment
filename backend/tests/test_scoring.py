from app.models.customer import Customer
from app.models.risk import RiskTier
from app.services.scoring import compute_risk_score

BASE_CUSTOMER_KWARGS: dict[str, object] = {
    "customer_id": "0000-BASE0",
    "gender": "Female",
    "senior_citizen": False,
    "partner": True,
    "dependents": True,
    "tenure": 60,
    "phone_service": True,
    "multiple_lines": "Yes",
    "internet_service": "DSL",
    "online_security": "Yes",
    "online_backup": "Yes",
    "device_protection": "Yes",
    "tech_support": "Yes",
    "streaming_tv": "Yes",
    "streaming_movies": "Yes",
    "contract": "Two year",
    "paperless_billing": False,
    "payment_method": "Bank transfer (automatic)",
    "monthly_charges": 50.0,
    "total_charges": 3000.0,
    "churn": False,
}


def make_customer(**overrides: object) -> Customer:
    return Customer(**{**BASE_CUSTOMER_KWARGS, **overrides})  # type: ignore[arg-type]


def test_lowest_risk_profile_scores_zero_with_no_factors() -> None:
    customer = make_customer(total_charges=50.0 * 60)  # matches expected exactly, no shortfall

    result = compute_risk_score(customer)

    assert result.score == 0
    assert result.tier == RiskTier.LOW
    assert result.factors == []


def test_known_snapshot_matches_expected_score_and_tier() -> None:
    customer = make_customer(
        contract="Month-to-month",
        tenure=2,
        payment_method="Electronic check",
        tech_support="No",
        online_security="No",
        paperless_billing=True,
        senior_citizen=False,
        monthly_charges=53.85,
        total_charges=107.70,  # exactly 53.85 * 2, no charges-trend signal
    )

    result = compute_risk_score(customer)

    assert result.score == 92  # 30 + 25 + 15 + 10 + 8 + 4
    assert result.tier == RiskTier.HIGH
    assert {f.name for f in result.factors} == {
        "Contract: Month-to-month",
        "Tenure: 2 months",
        "Payment method: electronic check",
        "Tech support: none",
        "Online security: none",
        "Paperless billing: yes",
    }


def test_score_clamps_at_100_when_raw_total_exceeds_it() -> None:
    customer = make_customer(
        contract="Month-to-month",
        tenure=1,
        payment_method="Electronic check",
        tech_support="No",
        online_security="No",
        paperless_billing=True,
        senior_citizen=True,
        monthly_charges=100.0,
        total_charges=50.0,  # well below the 100.0 expected total -> charges-trend factor fires
    )

    result = compute_risk_score(customer)

    assert result.score == 100
    assert result.tier == RiskTier.HIGH


def test_contract_month_to_month_contributes_expected_weight() -> None:
    customer = make_customer(contract="Month-to-month")

    result = compute_risk_score(customer)

    factor = next(f for f in result.factors if f.name.startswith("Contract"))
    assert factor.contribution == 30.0


def test_contract_one_year_contributes_expected_weight() -> None:
    customer = make_customer(contract="One year")

    result = compute_risk_score(customer)

    factor = next(f for f in result.factors if f.name.startswith("Contract"))
    assert factor.contribution == 10.0


def test_contract_two_year_contributes_nothing() -> None:
    customer = make_customer(contract="Two year")

    result = compute_risk_score(customer)

    assert not any(f.name.startswith("Contract") for f in result.factors)


def test_tenure_buckets_at_each_boundary() -> None:
    expected = {0: 25.0, 5: 25.0, 6: 15.0, 11: 15.0, 12: 5.0, 23: 5.0, 24: 0.0, 60: 0.0}

    for tenure, expected_weight in expected.items():
        customer = make_customer(tenure=tenure)
        result = compute_risk_score(customer)
        tenure_factors = [f for f in result.factors if f.name.startswith("Tenure")]

        if expected_weight == 0.0:
            assert tenure_factors == [], f"tenure={tenure}"
        else:
            assert tenure_factors[0].contribution == expected_weight, f"tenure={tenure}"


def test_electronic_check_contributes_expected_weight() -> None:
    customer = make_customer(payment_method="Electronic check")

    result = compute_risk_score(customer)

    factor = next(f for f in result.factors if f.name.startswith("Payment method"))
    assert factor.contribution == 15.0


def test_non_electronic_check_payment_contributes_nothing() -> None:
    customer = make_customer(payment_method="Mailed check")

    result = compute_risk_score(customer)

    assert not any(f.name.startswith("Payment method") for f in result.factors)


def test_no_tech_support_contributes_expected_weight() -> None:
    customer = make_customer(tech_support="No")

    result = compute_risk_score(customer)

    factor = next(f for f in result.factors if f.name.startswith("Tech support"))
    assert factor.contribution == 10.0


def test_tech_support_no_internet_service_is_not_penalized() -> None:
    customer = make_customer(tech_support="No internet service")

    result = compute_risk_score(customer)

    assert not any(f.name.startswith("Tech support") for f in result.factors)


def test_no_online_security_contributes_expected_weight() -> None:
    customer = make_customer(online_security="No")

    result = compute_risk_score(customer)

    factor = next(f for f in result.factors if f.name.startswith("Online security"))
    assert factor.contribution == 8.0


def test_online_security_no_internet_service_is_not_penalized() -> None:
    customer = make_customer(online_security="No internet service")

    result = compute_risk_score(customer)

    assert not any(f.name.startswith("Online security") for f in result.factors)


def test_paperless_billing_contributes_expected_weight() -> None:
    customer = make_customer(paperless_billing=True)

    result = compute_risk_score(customer)

    factor = next(f for f in result.factors if f.name.startswith("Paperless"))
    assert factor.contribution == 4.0


def test_non_paperless_billing_contributes_nothing() -> None:
    customer = make_customer(paperless_billing=False)

    result = compute_risk_score(customer)

    assert not any(f.name.startswith("Paperless") for f in result.factors)


def test_senior_citizen_contributes_expected_weight() -> None:
    customer = make_customer(senior_citizen=True)

    result = compute_risk_score(customer)

    factor = next(f for f in result.factors if f.name == "Senior citizen")
    assert factor.contribution == 5.0


def test_non_senior_citizen_contributes_nothing() -> None:
    customer = make_customer(senior_citizen=False)

    result = compute_risk_score(customer)

    assert not any(f.name == "Senior citizen" for f in result.factors)


def test_charges_trend_factor_fires_on_significant_shortfall() -> None:
    customer = make_customer(tenure=10, monthly_charges=50.0, total_charges=100.0)  # expected 500

    result = compute_risk_score(customer)

    assert any(f.name.startswith("Monthly charges elevated") for f in result.factors)


def test_charges_trend_factor_does_not_fire_within_tolerance() -> None:
    customer = make_customer(tenure=10, monthly_charges=50.0, total_charges=460.0)  # 8% shortfall

    result = compute_risk_score(customer)

    assert not any(f.name.startswith("Monthly charges elevated") for f in result.factors)


def test_charges_trend_factor_not_applicable_for_zero_tenure() -> None:
    customer = make_customer(tenure=0, monthly_charges=50.0, total_charges=0.0)

    result = compute_risk_score(customer)

    assert not any(f.name.startswith("Monthly charges elevated") for f in result.factors)


def test_charges_trend_factor_not_applicable_when_monthly_charges_is_zero() -> None:
    customer = make_customer(tenure=10, monthly_charges=0.0, total_charges=0.0)

    result = compute_risk_score(customer)

    assert not any(f.name.startswith("Monthly charges elevated") for f in result.factors)


def test_tier_boundaries() -> None:
    assert compute_risk_score(make_customer(contract="Two year", tenure=60)).tier == RiskTier.LOW

    # tenure 12 (+5) + one year (+10) + paperless (+4) + senior (+5) = 24 (Low, below 40)
    below_medium = make_customer(
        contract="One year", tenure=12, paperless_billing=True, senior_citizen=True
    )
    assert compute_risk_score(below_medium).tier == RiskTier.LOW

    # tenure 12 (+5) + one year (+10) + electronic check (+15) + paperless (+4) + senior (+5) = 39
    just_below_medium = make_customer(
        contract="One year",
        tenure=12,
        payment_method="Electronic check",
        paperless_billing=True,
        senior_citizen=True,
    )
    assert compute_risk_score(just_below_medium).score == 39
    assert compute_risk_score(just_below_medium).tier == RiskTier.LOW

    # add no_tech_support (+10) to push to 49 -> Medium
    medium = make_customer(
        contract="One year",
        tenure=12,
        payment_method="Electronic check",
        paperless_billing=True,
        senior_citizen=True,
        tech_support="No",
    )
    assert compute_risk_score(medium).score == 49
    assert compute_risk_score(medium).tier == RiskTier.MEDIUM

    just_below_high = make_customer(contract="Month-to-month", tenure=1)
    assert compute_risk_score(just_below_high).score == 55
    assert compute_risk_score(just_below_high).tier == RiskTier.MEDIUM

    definitely_high = make_customer(
        contract="Month-to-month", tenure=1, payment_method="Electronic check"
    )
    assert compute_risk_score(definitely_high).tier == RiskTier.HIGH
