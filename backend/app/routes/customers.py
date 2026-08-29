from fastapi import APIRouter, HTTPException, Query, Request

from app.models.customer import Customer
from app.models.customer_detail import CustomerDetail
from app.models.customer_list import CustomerListItem, PaginatedCustomers
from app.models.outreach import OutreachStatus, OutreachUpdateRequest
from app.models.risk import RiskTier
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


def _get_raw_customer_or_404(
    raw_customers: dict[str, dict[str, object]], customer_id: str
) -> dict[str, object]:
    raw = raw_customers.get(customer_id)
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return raw


def _get_customer_or_404(raw_customers: dict[str, dict[str, object]], customer_id: str) -> Customer:
    raw = _get_raw_customer_or_404(raw_customers, customer_id)
    return Customer(**raw)  # type: ignore[arg-type]


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

    raw_customers: dict[str, dict[str, object]] = request.app.state.customers

    scored = []
    for raw in raw_customers.values():
        customer = Customer(**raw)  # type: ignore[arg-type]
        risk = compute_risk_score(customer)

        if parsed_risk_tier is not None and risk.tier != parsed_risk_tier:
            continue
        if contract is not None and customer.contract != contract:
            continue
        if (
            parsed_outreach_status is not None
            and customer.outreach_status != parsed_outreach_status
        ):
            continue

        scored.append((customer, risk))

    # Sort before slicing, descending by score, so pages are stable across
    # requests; customer_id as a secondary key makes the ordering fully
    # deterministic rather than relying on dict-insertion-order as a tiebreaker.
    scored.sort(key=lambda pair: (-pair[1].score, pair[0].customer_id))

    total = len(scored)
    page = scored[offset : offset + limit]

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
        for customer, risk in page
    ]

    return PaginatedCustomers(items=items, total=total, offset=offset, limit=limit)


@router.get("/customers/{customer_id}", response_model=CustomerDetail)
def get_customer(customer_id: str, request: Request) -> CustomerDetail:
    raw_customers: dict[str, dict[str, object]] = request.app.state.customers
    customer = _get_customer_or_404(raw_customers, customer_id)
    risk = compute_risk_score(customer)
    return CustomerDetail(customer=customer, risk=risk)


@router.patch("/customers/{customer_id}/outreach", response_model=CustomerDetail)
def update_outreach_status(
    customer_id: str, body: OutreachUpdateRequest, request: Request
) -> CustomerDetail:
    raw_customers: dict[str, dict[str, object]] = request.app.state.customers
    raw = _get_raw_customer_or_404(raw_customers, customer_id)

    current_status = Customer(**raw).outreach_status  # type: ignore[arg-type]
    try:
        validate_transition(current_status, body.status)
    except InvalidOutreachTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Synchronous, no `await` between the transition check above and this
    # write — safe under FastAPI's single-process model without a lock.
    raw["outreach_status"] = body.status.value

    customer = Customer(**raw)  # type: ignore[arg-type]
    risk = compute_risk_score(customer)
    return CustomerDetail(customer=customer, risk=risk)
