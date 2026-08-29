from collections.abc import Iterator

import pytest
from app.main import app
from fastapi.testclient import TestClient

KNOWN_CUSTOMER_ID = "7590-VHVEG"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_legal_transition_updates_status(client: TestClient) -> None:
    response = client.patch(
        f"/customers/{KNOWN_CUSTOMER_ID}/outreach", json={"status": "IN_PROGRESS"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["customer"]["outreach_status"] == "IN_PROGRESS"

    # persisted: a subsequent read reflects the mutation
    follow_up = client.get(f"/customers/{KNOWN_CUSTOMER_ID}")
    assert follow_up.json()["customer"]["outreach_status"] == "IN_PROGRESS"


def test_full_legal_sequence(client: TestClient) -> None:
    client.patch(f"/customers/{KNOWN_CUSTOMER_ID}/outreach", json={"status": "IN_PROGRESS"})
    response = client.patch(f"/customers/{KNOWN_CUSTOMER_ID}/outreach", json={"status": "RESOLVED"})

    assert response.status_code == 200
    assert response.json()["customer"]["outreach_status"] == "RESOLVED"


def test_illegal_transition_returns_400_and_does_not_mutate(client: TestClient) -> None:
    response = client.patch(f"/customers/{KNOWN_CUSTOMER_ID}/outreach", json={"status": "RESOLVED"})

    assert response.status_code == 400
    assert "NOT_CONTACTED" in response.json()["detail"]
    assert "RESOLVED" in response.json()["detail"]

    unchanged = client.get(f"/customers/{KNOWN_CUSTOMER_ID}")
    assert unchanged.json()["customer"]["outreach_status"] == "NOT_CONTACTED"


def test_resolved_is_terminal_via_endpoint(client: TestClient) -> None:
    client.patch(f"/customers/{KNOWN_CUSTOMER_ID}/outreach", json={"status": "IN_PROGRESS"})
    client.patch(f"/customers/{KNOWN_CUSTOMER_ID}/outreach", json={"status": "RESOLVED"})

    response = client.patch(
        f"/customers/{KNOWN_CUSTOMER_ID}/outreach", json={"status": "IN_PROGRESS"}
    )

    assert response.status_code == 400


def test_unknown_customer_id_returns_404(client: TestClient) -> None:
    response = client.patch("/customers/does-not-exist/outreach", json={"status": "IN_PROGRESS"})

    assert response.status_code == 404
    assert "does-not-exist" in response.json()["detail"]


def test_missing_status_returns_422(client: TestClient) -> None:
    response = client.patch(f"/customers/{KNOWN_CUSTOMER_ID}/outreach", json={})

    assert response.status_code == 422


def test_invalid_status_value_returns_422(client: TestClient) -> None:
    response = client.patch(f"/customers/{KNOWN_CUSTOMER_ID}/outreach", json={"status": "GHOSTED"})

    assert response.status_code == 422
