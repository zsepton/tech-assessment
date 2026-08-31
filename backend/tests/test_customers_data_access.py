import csv
from pathlib import Path

import pytest
from app.data_access.customers import (
    CustomerNotFoundError,
    CustomerStore,
    get_all_customers,
    get_raw_customer,
    load_customers,
    parse_customer_row,
    to_customer,
    update_outreach_status,
)
from app.models.customer import Customer
from app.models.outreach import OutreachStatus

RAW_ROW = {
    "customerID": "7590-VHVEG",
    "gender": "Female",
    "SeniorCitizen": "0",
    "Partner": "Yes",
    "Dependents": "No",
    "tenure": "1",
    "PhoneService": "No",
    "MultipleLines": "No phone service",
    "InternetService": "DSL",
    "OnlineSecurity": "No",
    "OnlineBackup": "Yes",
    "DeviceProtection": "No",
    "TechSupport": "No",
    "StreamingTV": "No",
    "StreamingMovies": "No",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": "29.85",
    "TotalCharges": "29.85",
    "Churn": "No",
}


def test_parse_customer_row_coerces_types() -> None:
    parsed = parse_customer_row(RAW_ROW)

    assert parsed["customer_id"] == "7590-VHVEG"
    assert parsed["senior_citizen"] is False
    assert parsed["partner"] is True
    assert parsed["dependents"] is False
    assert parsed["tenure"] == 1
    assert parsed["monthly_charges"] == 29.85
    assert parsed["total_charges"] == 29.85
    assert parsed["churn"] is False


def test_parse_customer_row_handles_blank_total_charges(
    caplog: pytest.LogCaptureFixture,
) -> None:
    row = {**RAW_ROW, "tenure": "0", "TotalCharges": " "}

    with caplog.at_level("WARNING", logger="app.data_access.customers"):
        parsed = parse_customer_row(row)

    assert parsed["tenure"] == 0
    assert parsed["total_charges"] == 0.0
    # A blank value is an expected artifact of this dataset (a brand-new,
    # not-yet-billed customer), not a data-quality problem, so it should not
    # be logged as a warning the way a genuinely malformed value is below.
    assert caplog.records == []


def test_parse_customer_row_handles_malformed_charges(caplog: pytest.LogCaptureFixture) -> None:
    row = {**RAW_ROW, "MonthlyCharges": "not-a-number"}

    with caplog.at_level("WARNING", logger="app.data_access.customers"):
        parsed = parse_customer_row(row)

    assert parsed["monthly_charges"] == 0.0
    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert caplog.records[0].levelname == "WARNING"
    assert "MonthlyCharges" in message
    assert "not-a-number" in message
    assert row["customerID"] in message


def test_load_customers_keys_by_customer_id(tmp_path: Path) -> None:
    csv_path = tmp_path / "customers.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(RAW_ROW.keys()))
        writer.writeheader()
        writer.writerow(RAW_ROW)
        writer.writerow({**RAW_ROW, "customerID": "5575-GNVDE", "TotalCharges": " ", "tenure": "0"})

    customers = load_customers(csv_path)

    assert set(customers.keys()) == {"7590-VHVEG", "5575-GNVDE"}
    assert customers["5575-GNVDE"]["total_charges"] == 0.0


def _store() -> CustomerStore:
    return {
        "7590-VHVEG": parse_customer_row(RAW_ROW),
        "5575-GNVDE": parse_customer_row({**RAW_ROW, "customerID": "5575-GNVDE"}),
    }


def test_get_all_customers_returns_every_record_as_a_domain_object() -> None:
    store = _store()

    all_customers = get_all_customers(store)

    assert {c.customer_id for c in all_customers} == {"7590-VHVEG", "5575-GNVDE"}
    assert all(isinstance(c, Customer) for c in all_customers)


def test_get_raw_customer_returns_matching_record() -> None:
    store = _store()

    customer = get_raw_customer(store, "7590-VHVEG")

    assert customer["customer_id"] == "7590-VHVEG"


def test_get_raw_customer_raises_for_unknown_id() -> None:
    store = _store()

    with pytest.raises(CustomerNotFoundError):
        get_raw_customer(store, "does-not-exist")


def test_update_outreach_status_mutates_and_returns_the_given_record() -> None:
    store = _store()
    raw = get_raw_customer(store, "7590-VHVEG")

    updated = update_outreach_status(raw, OutreachStatus.IN_PROGRESS)

    assert updated["outreach_status"] == "IN_PROGRESS"
    assert updated is raw
    # The store isn't passed in at all; the caller is expected to have
    # already fetched `raw` from it (e.g. via get_raw_customer), so no
    # separate lookup happens here.
    assert store["7590-VHVEG"]["outreach_status"] == "IN_PROGRESS"


def test_to_customer_converts_a_raw_record() -> None:
    raw = get_raw_customer(_store(), "7590-VHVEG")

    customer = to_customer(raw)

    assert isinstance(customer, Customer)
    assert customer.customer_id == "7590-VHVEG"
