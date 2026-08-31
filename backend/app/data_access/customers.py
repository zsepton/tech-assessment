import csv
import logging
from pathlib import Path
from typing import NotRequired, TypedDict

from app.models.outreach import OutreachStatus

logger = logging.getLogger("app.data_access.customers")

DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
)


class RawCustomerRecord(TypedDict):
    """The shape of a raw customer record, matching `Customer`'s fields.

    Using a TypedDict (rather than `dict[str, Any]`) means `Customer(**raw)`
    is checked field-by-field by mypy — e.g. a `tenure` accidentally parsed
    as a str instead of an int is a type error here, not just a runtime
    `pydantic.ValidationError` on the first request.
    """

    customer_id: str
    gender: str
    senior_citizen: bool
    partner: bool
    dependents: bool
    tenure: int
    phone_service: bool
    multiple_lines: str
    internet_service: str
    online_security: str
    online_backup: str
    device_protection: str
    tech_support: str
    streaming_tv: str
    streaming_movies: str
    contract: str
    paperless_billing: bool
    payment_method: str
    monthly_charges: float
    total_charges: float
    churn: bool
    # Absent until the first PATCH /customers/{id}/outreach; Customer's
    # matching field has a default, so omitting it is fine.
    outreach_status: NotRequired[OutreachStatus]


CustomerStore = dict[str, RawCustomerRecord]
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


def _parse_charges(raw: str, *, customer_id: str, field_name: str) -> float:
    """Parse a charges field, treating a blank value as 0.0.

    A blank value is an expected artifact of this dataset (brand-new
    customers with tenure=0 haven't been billed yet). A non-blank value that
    still fails to parse as a float is not expected, and is logged as a
    warning (distinct from the blank case) so malformed source data doesn't
    silently masquerade as a legitimate $0 customer.
    """
    stripped = raw.strip()
    if not stripped:
        return 0.0
    try:
        return float(stripped)
    except ValueError:
        logger.warning(
            "malformed %s value %r for customer %s; treating as 0.0",
            field_name,
            raw,
            customer_id,
        )
        return 0.0


def parse_customer_row(row: dict[str, str]) -> RawCustomerRecord:
    customer_id = row["customerID"].strip()
    return {
        "customer_id": customer_id,
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
        "monthly_charges": _parse_charges(
            row["MonthlyCharges"], customer_id=customer_id, field_name="MonthlyCharges"
        ),
        "total_charges": _parse_charges(
            row["TotalCharges"], customer_id=customer_id, field_name="TotalCharges"
        ),
        # Historical outcome label from the source dataset — not a scoring input.
        "churn": _yes_no(row["Churn"]),
    }


def load_customers(csv_path: Path = DEFAULT_CSV_PATH) -> CustomerStore:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        customers = [parse_customer_row(row) for row in reader]
    return {customer["customer_id"]: customer for customer in customers}


def get_all_customers(store: CustomerStore) -> list[RawCustomerRecord]:
    """Return every raw customer record in the store."""
    return list(store.values())


def get_customer(store: CustomerStore, customer_id: str) -> RawCustomerRecord:
    """Look up a raw customer record by id.

    Raises CustomerNotFoundError if no record matches.
    """
    try:
        return store[customer_id]
    except KeyError:
        raise CustomerNotFoundError(customer_id) from None


def update_outreach_status(
    store: CustomerStore, customer_id: str, status: OutreachStatus
) -> RawCustomerRecord:
    """Persist a new outreach status for customer_id, returning the updated record.

    Raises CustomerNotFoundError if no record matches. Does not validate that
    the transition is legal — callers are expected to check that via
    `services.outreach.validate_transition` before calling this.
    """
    raw = get_customer(store, customer_id)
    raw["outreach_status"] = status
    return raw
