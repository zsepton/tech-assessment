import csv
from pathlib import Path

from app.data_access.customers import load_customers, parse_customer_row

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


def test_parse_customer_row_handles_blank_total_charges() -> None:
    row = {**RAW_ROW, "tenure": "0", "TotalCharges": " "}

    parsed = parse_customer_row(row)

    assert parsed["tenure"] == 0
    assert parsed["total_charges"] == 0.0


def test_parse_customer_row_handles_malformed_charges() -> None:
    row = {**RAW_ROW, "MonthlyCharges": "not-a-number"}

    parsed = parse_customer_row(row)

    assert parsed["monthly_charges"] == 0.0


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
