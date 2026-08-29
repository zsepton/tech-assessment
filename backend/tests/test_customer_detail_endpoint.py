from collections.abc import Iterator

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_returns_full_record_with_risk_breakdown_for_known_id(client: TestClient) -> None:
    response = client.get("/customers/7590-VHVEG")

    assert response.status_code == 200
    body = response.json()
    assert body["customer"]["customer_id"] == "7590-VHVEG"
    assert body["customer"]["contract"] == "Month-to-month"
    assert "risk" in body
    assert 0 <= body["risk"]["score"] <= 100
    assert body["risk"]["tier"] in {"Low", "Medium", "High"}
    assert isinstance(body["risk"]["factors"], list)


def test_risk_breakdown_matches_the_scoring_engine(client: TestClient) -> None:
    list_response = client.get("/customers", params={"limit": 1})
    top_customer_id = list_response.json()["items"][0]["customer_id"]
    top_score = list_response.json()["items"][0]["risk_score"]

    detail_response = client.get(f"/customers/{top_customer_id}")

    assert detail_response.json()["risk"]["score"] == top_score


def test_unknown_customer_id_returns_404(client: TestClient) -> None:
    response = client.get("/customers/does-not-exist")

    assert response.status_code == 404
    assert "does-not-exist" in response.json()["detail"]
