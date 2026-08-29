import csv
from pathlib import Path
from typing import Any

DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
)


def _yes_no(value: str) -> bool:
    return value.strip() == "Yes"


def _parse_charges(raw: str) -> float:
    stripped = raw.strip()
    if not stripped:
        return 0.0
    try:
        return float(stripped)
    except ValueError:
        return 0.0


def parse_customer_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "customer_id": row["customerID"].strip(),
        "gender": row["gender"].strip(),
        "senior_citizen": row["SeniorCitizen"].strip() == "1",
        "partner": _yes_no(row["Partner"]),
        "dependents": _yes_no(row["Dependents"]),
        "tenure": int(row["tenure"]),
        "phone_service": _yes_no(row["PhoneService"]),
        "multiple_lines": row["MultipleLines"].strip(),
        "internet_service": row["InternetService"].strip(),
        "online_security": row["OnlineSecurity"].strip(),
        "online_backup": row["OnlineBackup"].strip(),
        "device_protection": row["DeviceProtection"].strip(),
        "tech_support": row["TechSupport"].strip(),
        "streaming_tv": row["StreamingTV"].strip(),
        "streaming_movies": row["StreamingMovies"].strip(),
        "contract": row["Contract"].strip(),
        "paperless_billing": _yes_no(row["PaperlessBilling"]),
        "payment_method": row["PaymentMethod"].strip(),
        "monthly_charges": _parse_charges(row["MonthlyCharges"]),
        "total_charges": _parse_charges(row["TotalCharges"]),
        # Historical outcome label from the source dataset — not a scoring input.
        "churn": _yes_no(row["Churn"]),
    }


def load_customers(csv_path: Path = DEFAULT_CSV_PATH) -> dict[str, dict[str, Any]]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        customers = [parse_customer_row(row) for row in reader]
    return {customer["customer_id"]: customer for customer in customers}
