from pydantic import BaseModel

from app.models.outreach import OutreachStatus
from app.models.risk import RiskTier


class CustomerListItem(BaseModel):
    """One row in the paginated customer list — summary fields plus computed risk.

    Deliberately lighter than the full `Customer` + `RiskScore` models: the
    list view needs enough to scan/sort/filter, not the full profile or
    factor breakdown (that's GET /customers/{id}'s job).
    """

    customer_id: str
    contract: str
    tenure: int
    monthly_charges: float
    outreach_status: OutreachStatus
    risk_score: int
    risk_tier: RiskTier


class PaginatedCustomers(BaseModel):
    """A page of customers plus enough metadata to render pagination controls."""

    items: list[CustomerListItem]
    total: int
    offset: int
    limit: int
