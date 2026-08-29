from pydantic import BaseModel

from app.models.customer import Customer
from app.models.risk import RiskScore


class CustomerDetail(BaseModel):
    """Everything a customer detail view needs in one response.

    Kept as two nested objects (rather than one flat model) so the customer
    profile and the computed risk breakdown stay clearly separated, matching
    how the frontend detail view renders them as two distinct sections.
    """

    customer: Customer
    risk: RiskScore
