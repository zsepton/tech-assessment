from fastapi import APIRouter

from app.models.model_info import ModelInfo
from app.services import scoring

router = APIRouter()


@router.get("/model/info", response_model=ModelInfo)
def get_model_info() -> ModelInfo:
    return ModelInfo(
        contract_weights={
            "Month-to-month": scoring.CONTRACT_MONTH_TO_MONTH_WEIGHT,
            "One year": scoring.CONTRACT_ONE_YEAR_WEIGHT,
            "Two year": scoring.CONTRACT_TWO_YEAR_WEIGHT,
        },
        tenure_weight_buckets=scoring.TENURE_WEIGHT_BUCKETS,
        electronic_check_weight=scoring.ELECTRONIC_CHECK_WEIGHT,
        no_tech_support_weight=scoring.NO_TECH_SUPPORT_WEIGHT,
        no_online_security_weight=scoring.NO_ONLINE_SECURITY_WEIGHT,
        paperless_billing_weight=scoring.PAPERLESS_BILLING_WEIGHT,
        senior_citizen_weight=scoring.SENIOR_CITIZEN_WEIGHT,
        charges_increase_weight=scoring.CHARGES_INCREASE_WEIGHT,
        charges_increase_shortfall_ratio=scoring.CHARGES_INCREASE_SHORTFALL_RATIO,
        high_risk_threshold=scoring.HIGH_RISK_THRESHOLD,
        medium_risk_threshold=scoring.MEDIUM_RISK_THRESHOLD,
        min_score=scoring.MIN_SCORE,
        max_score=scoring.MAX_SCORE,
    )
