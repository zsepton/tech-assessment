from pydantic import BaseModel, Field

from app.models.outreach import OutreachStatus


class Customer(BaseModel):
    """A customer record, matching the fields in the source Telco churn CSV."""

    customer_id: str
    gender: str
    senior_citizen: bool
    partner: bool
    dependents: bool
    tenure: int = Field(ge=0, description="Months as a customer")
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
    monthly_charges: float = Field(ge=0)
    total_charges: float = Field(ge=0)
    churn: bool = Field(description="Historical churn label from the source dataset")
    outreach_status: OutreachStatus = OutreachStatus.NOT_CONTACTED
