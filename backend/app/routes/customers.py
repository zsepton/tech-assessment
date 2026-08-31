from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.data_access import customers as customer_store
from app.data_access.customers import CustomerNotFoundError, CustomerStore
from app.models.customer import Customer
from app.models.customer_detail import CustomerDetail
from app.models.customer_list import CustomerListItem, PaginatedCustomers
from app.models.outreach import OutreachStatus, OutreachUpdateRequest
from app.models.risk import RiskTier
from app.services.customer_listing import CustomerListFilters, list_matching_customers
from app.services.outreach import InvalidOutreachTransitionError, validate_transition
from app.services.scoring import compute_risk_score

router = APIRouter()

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# The dataset's fixed set of contract values. Not an enum on the Customer
# model itself (it's sourced as a plain CSV string), but filtering still
# needs a known-good set to validate an unrecognized value against.
VALID_CONTRACTS = frozenset({"Month-to-month", "One year", "Two year"})


def _parse_risk_tier_filter(value: str | None) -> RiskTier | None:
    if value is None:
        return None
    try:
        return RiskTier(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid risk_tier filter value: {value!r}"
        ) from exc


def _parse_outreach_status_filter(value: str | None) -> OutreachStatus | None:
    if value is None:
        return None
    try:
        return OutreachStatus(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid outreach_status filter value: {value!r}"
        ) from exc


def _validate_contract_filter(value: str | None) -> None:
    if value is not None and value not in VALID_CONTRACTS:
        raise HTTPException(status_code=400, detail=f"Invalid contract filter value: {value!r}")


def _get_raw_customer_or_404(store: CustomerStore, customer_id: str) -> dict[str, Any]:
    try:
        return customer_store.get_customer(store, customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.") from exc


def _get_customer_or_404(store: CustomerStore, customer_id: str) -> Customer:
    raw = _get_raw_customer_or_404(store, customer_id)
    return Customer(**raw)


@router.get("/customers", response_model=PaginatedCustomers)
def list_customers(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    risk_tier: str | None = Query(None),
    contract: str | None = Query(None),
    outreach_status: str | None = Query(None),
) -> PaginatedCustomers:
    parsed_risk_tier = _parse_risk_tier_filter(risk_tier)
    parsed_outreach_status = _parse_outreach_status_filter(outreach_status)
    _validate_contract_filter(contract)

    store: CustomerStore = request.app.state.customers
    filters = CustomerListFilters(
        risk_tier=parsed_risk_tier, contract=contract, outreach_status=parsed_outreach_status
    )
    page = list_matching_customers(
        customer_store.get_all_customers(store), filters, offset=offset, limit=limit
    )

    items = [
        CustomerListItem(
            customer_id=customer.customer_id,
            contract=customer.contract,
            tenure=customer.tenure,
            monthly_charges=customer.monthly_charges,
            outreach_status=customer.outreach_status,
            risk_score=risk.score,
            risk_tier=risk.tier,
        )
        for customer, risk in page.items
    ]

    return PaginatedCustomers(items=items, total=page.total, offset=offset, limit=limit)


@router.get("/customers/{customer_id}", response_model=CustomerDetail)
def get_customer(customer_id: str, request: Request) -> CustomerDetail:
    store: CustomerStore = request.app.state.customers
    customer = _get_customer_or_404(store, customer_id)
    risk = compute_risk_score(customer)
    return CustomerDetail(customer=customer, risk=risk)


@router.patch("/customers/{customer_id}/outreach", response_model=CustomerDetail)
def update_outreach_status(
    customer_id: str, body: OutreachUpdateRequest, request: Request
) -> CustomerDetail:
    store: CustomerStore = request.app.state.customers
    raw = _get_raw_customer_or_404(store, customer_id)

    current_status = Customer(**raw).outreach_status
    try:
        validate_transition(current_status, body.status)
    except InvalidOutreachTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Synchronous, no `await` between the transition check above and this
    # write — safe under FastAPI's single-process model without a lock.
    raw = customer_store.update_outreach_status(store, customer_id, body.status)

    customer = Customer(**raw)
    risk = compute_risk_score(customer)
    return CustomerDetail(customer=customer, risk=risk)
