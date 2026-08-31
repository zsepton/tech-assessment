"""Filtering, sorting, and pagination for the customer list endpoint.

Pulled out of the route handler into its own service, matching how
scoring.py and outreach.py encapsulate the rest of this app's business
logic, so it's unit-testable independent of an HTTP request/response cycle.
"""

from dataclasses import dataclass

from app.data_access.customers import RawCustomerRecord
from app.models.customer import Customer
from app.models.outreach import OutreachStatus
from app.models.risk import RiskScore, RiskTier
from app.services.scoring import compute_risk_score


@dataclass(frozen=True)
class CustomerListFilters:
    """Optional filters for the customer list; `None` means "don't filter on this"."""

    risk_tier: RiskTier | None = None
    contract: str | None = None
    outreach_status: OutreachStatus | None = None


@dataclass(frozen=True)
class CustomerListPage:
    """One page of (customer, risk) pairs, plus the total matching count."""

    items: list[tuple[Customer, RiskScore]]
    total: int


def _matches(customer: Customer, risk: RiskScore, filters: CustomerListFilters) -> bool:
    if filters.risk_tier is not None and risk.tier != filters.risk_tier:
        return False
    if filters.contract is not None and customer.contract != filters.contract:
        return False
    return filters.outreach_status is None or customer.outreach_status == filters.outreach_status


def list_matching_customers(
    raw_customers: list[RawCustomerRecord],
    filters: CustomerListFilters,
    offset: int,
    limit: int,
) -> CustomerListPage:
    """Score, filter, sort, and paginate the given raw customer records."""
    scored = []
    for raw in raw_customers:
        customer = Customer(**raw)
        risk = compute_risk_score(customer)
        if _matches(customer, risk, filters):
            scored.append((customer, risk))

    # Sort before slicing, descending by score, so pages are stable across
    # requests; customer_id as a secondary key makes the ordering fully
    # deterministic rather than relying on dict-insertion-order as a tiebreaker.
    scored.sort(key=lambda pair: (-pair[1].score, pair[0].customer_id))

    total = len(scored)
    page = scored[offset : offset + limit]
    return CustomerListPage(items=page, total=total)
