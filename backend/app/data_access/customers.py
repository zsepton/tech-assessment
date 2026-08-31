import csv
from pathlib import Path
from typing import Any

from app.models.outreach import OutreachStatus

DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
)

CustomerStore = dict[str, dict[str, Any]]
"""In-memory customer storage, keyed by customer_id. Populated once at
startup by `load_customers` and held on `app.state.customers`; reads and
writes should go through this module's accessors below rather than
indexing/mutating the dict directly."""


class CustomerNotFoundError(Exception):
    """Raised when no customer record matches the given customer_id."""

    def __init__(self, customer_id: str) -> None:
        self.customer_id = customer_id
        super().__init__(f"No customer found with id {customer_id!r}")


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


def load_customers(csv_path: Path = DEFAULT_CSV_PATH) -> CustomerStore:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        customers = [parse_customer_row(row) for row in reader]
    return {customer["customer_id"]: customer for customer in customers}


def get_all_customers(store: CustomerStore) -> list[dict[str, Any]]:
    """Return every raw customer record in the store."""
    return list(store.values())


def get_customer(store: CustomerStore, customer_id: str) -> dict[str, Any]:
    """Look up a raw customer record by id.

    Raises CustomerNotFoundError if no record matches.
    """
    try:
        return store[customer_id]
    except KeyError:
        raise CustomerNotFoundError(customer_id) from None


def update_outreach_status(
    store: CustomerStore, customer_id: str, status: OutreachStatus
) -> dict[str, Any]:
    """Persist a new outreach status for customer_id, returning the updated record.

    Raises CustomerNotFoundError if no record matches. Does not validate that
    the transition is legal — callers are expected to check that via
    `services.outreach.validate_transition` before calling this.
    """
    raw = get_customer(store, customer_id)
    raw["outreach_status"] = status.value
    return raw
