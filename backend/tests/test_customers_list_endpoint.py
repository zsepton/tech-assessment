from collections.abc import Iterator

import pytest
from app.main import app
from app.models.outreach import OutreachStatus
from app.routes.customers import DEFAULT_LIMIT, MAX_LIMIT
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_returns_default_page(client: TestClient) -> None:
    response = client.get("/customers")

    assert response.status_code == 200
    body = response.json()
    assert body["offset"] == 0
    assert body["limit"] == DEFAULT_LIMIT
    assert body["total"] > DEFAULT_LIMIT  # the real dataset has ~7k rows
    assert len(body["items"]) == DEFAULT_LIMIT


def test_results_are_sorted_by_risk_score_descending(client: TestClient) -> None:
    response = client.get("/customers", params={"limit": 50})

    scores = [item["risk_score"] for item in response.json()["items"]]

    assert scores == sorted(scores, reverse=True)


def test_pagination_offset_and_limit_produce_disjoint_pages(client: TestClient) -> None:
    page1 = client.get("/customers", params={"offset": 0, "limit": 10}).json()
    page2 = client.get("/customers", params={"offset": 10, "limit": 10}).json()

    ids_page1 = {item["customer_id"] for item in page1["items"]}
    ids_page2 = {item["customer_id"] for item in page2["items"]}

    assert ids_page1.isdisjoint(ids_page2)
    assert len(page1["items"]) == 10
    assert len(page2["items"]) == 10


def test_pagination_is_stable_across_repeated_requests(client: TestClient) -> None:
    first = client.get("/customers", params={"offset": 5, "limit": 5}).json()
    second = client.get("/customers", params={"offset": 5, "limit": 5}).json()

    assert first["items"] == second["items"]


def test_limit_is_capped_at_max(client: TestClient) -> None:
    response = client.get("/customers", params={"limit": MAX_LIMIT + 50})

    assert response.status_code == 422


def test_limit_below_one_is_rejected(client: TestClient) -> None:
    response = client.get("/customers", params={"limit": 0})

    assert response.status_code == 422


def test_negative_offset_is_rejected(client: TestClient) -> None:
    response = client.get("/customers", params={"offset": -1})

    assert response.status_code == 422


def test_filter_by_risk_tier(client: TestClient) -> None:
    response = client.get("/customers", params={"risk_tier": "High", "limit": 50})

    body = response.json()
    assert len(body["items"]) > 0
    assert all(item["risk_tier"] == "High" for item in body["items"])


def test_invalid_risk_tier_filter_returns_400(client: TestClient) -> None:
    response = client.get("/customers", params={"risk_tier": "Extreme"})

    assert response.status_code == 400
    assert "risk_tier" in response.json()["detail"]


def test_filter_by_contract(client: TestClient) -> None:
    response = client.get("/customers", params={"contract": "Two year", "limit": 50})

    body = response.json()
    assert len(body["items"]) > 0
    assert all(item["contract"] == "Two year" for item in body["items"])


def test_invalid_contract_filter_returns_400(client: TestClient) -> None:
    response = client.get("/customers", params={"contract": "Month-to-Month"})  # wrong casing

    assert response.status_code == 400
    assert "contract" in response.json()["detail"]


def test_filter_by_outreach_status(client: TestClient) -> None:
    # Every customer defaults to NOT_CONTACTED at this point in the app (no
    # PATCH endpoint exists yet to change it), so this should match everyone.
    response = client.get(
        "/customers", params={"outreach_status": OutreachStatus.NOT_CONTACTED.value, "limit": 5}
    )

    body = response.json()
    assert len(body["items"]) == 5
    assert all(item["outreach_status"] == "NOT_CONTACTED" for item in body["items"])


def test_invalid_outreach_status_filter_returns_400(client: TestClient) -> None:
    response = client.get("/customers", params={"outreach_status": "GHOSTED"})

    assert response.status_code == 400
    assert "outreach_status" in response.json()["detail"]


def test_combining_filters_narrows_results(client: TestClient) -> None:
    response = client.get(
        "/customers",
        params={"risk_tier": "High", "contract": "Month-to-month", "limit": 50},
    )

    body = response.json()
    assert len(body["items"]) > 0
    assert all(
        item["risk_tier"] == "High" and item["contract"] == "Month-to-month"
        for item in body["items"]
    )


def test_filters_that_match_nothing_return_empty_page(client: TestClient) -> None:
    # No customer can be both RESOLVED (a status only reachable via a PATCH
    # this app has no endpoint for yet, so nothing has it) and High risk.
    response = client.get(
        "/customers",
        params={"risk_tier": "High", "outreach_status": "RESOLVED"},
    )

    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
