from pydantic import BaseModel


class ModelInfo(BaseModel):
    """The scoring engine's current weights, rules, and tier thresholds.

    Lets a client (or a human) explain *why* a customer got a given score
    without duplicating the scoring logic — see app/services/scoring.py,
    which this is built directly from.
    """

    contract_weights: dict[str, float]
    tenure_weight_buckets: list[tuple[int, float]]
    electronic_check_weight: float
    no_tech_support_weight: float
    no_online_security_weight: float
    paperless_billing_weight: float
    senior_citizen_weight: float
    charges_increase_weight: float
    charges_increase_shortfall_ratio: float
    high_risk_threshold: int
    medium_risk_threshold: int
    min_score: int
    max_score: int
