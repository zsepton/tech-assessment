from collections.abc import Iterator

import pytest
from app.main import app
from app.services import scoring
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_reflects_current_scoring_constants(client: TestClient) -> None:
    response = client.get("/model/info")

    assert response.status_code == 200
    body = response.json()

    assert body["contract_weights"] == {
        "Month-to-month": scoring.CONTRACT_MONTH_TO_MONTH_WEIGHT,
        "One year": scoring.CONTRACT_ONE_YEAR_WEIGHT,
        "Two year": scoring.CONTRACT_TWO_YEAR_WEIGHT,
    }
    expected_buckets = [list(bucket) for bucket in scoring.TENURE_WEIGHT_BUCKETS]
    assert body["tenure_weight_buckets"] == expected_buckets
    assert body["electronic_check_weight"] == scoring.ELECTRONIC_CHECK_WEIGHT
    assert body["no_tech_support_weight"] == scoring.NO_TECH_SUPPORT_WEIGHT
    assert body["no_online_security_weight"] == scoring.NO_ONLINE_SECURITY_WEIGHT
    assert body["paperless_billing_weight"] == scoring.PAPERLESS_BILLING_WEIGHT
    assert body["senior_citizen_weight"] == scoring.SENIOR_CITIZEN_WEIGHT
    assert body["charges_increase_weight"] == scoring.CHARGES_INCREASE_WEIGHT
    assert body["charges_increase_shortfall_ratio"] == scoring.CHARGES_INCREASE_SHORTFALL_RATIO
    assert body["high_risk_threshold"] == scoring.HIGH_RISK_THRESHOLD
    assert body["medium_risk_threshold"] == scoring.MEDIUM_RISK_THRESHOLD
    assert body["min_score"] == scoring.MIN_SCORE
    assert body["max_score"] == scoring.MAX_SCORE


def test_updating_a_scoring_constant_is_reflected_without_code_changes(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(scoring, "SENIOR_CITIZEN_WEIGHT", 42.0)

    response = client.get("/model/info")

    assert response.json()["senior_citizen_weight"] == 42.0
