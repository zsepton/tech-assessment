from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    """Coarse risk bucket a customer's score maps to."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskFactor(BaseModel):
    """A single factor contributing to a customer's risk score."""

    name: str
    contribution: float = Field(ge=0, description="Magnitude of this factor's effect on the score")
    direction: Literal["increases_risk", "decreases_risk"]


class RiskScore(BaseModel):
    """A customer's computed churn risk, with the factors that produced it."""

    score: int = Field(ge=0, le=100, description="Overall churn risk score, 0-100")
    tier: RiskTier
    factors: list[RiskFactor]
