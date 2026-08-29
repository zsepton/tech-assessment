from enum import Enum

from pydantic import BaseModel


class OutreachStatus(str, Enum):
    """The outreach lifecycle for a customer, tracked by the retention team."""

    NOT_CONTACTED = "NOT_CONTACTED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class OutreachUpdateRequest(BaseModel):
    """Request body for updating a customer's outreach status."""

    status: OutreachStatus
