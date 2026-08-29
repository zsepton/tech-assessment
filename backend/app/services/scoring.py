"""Weighted heuristic churn risk scoring.

This is a deliberate stand-in for a trained ML model (per the assessment's
"Explicitly Out of Scope" section) — a rule-based function producing a 0-100
score, a tier, and a factor-by-factor breakdown explaining *why*. Every
weight and threshold below is a named module-level constant, specifically so
`GET /model/info` can import and return this module's rules directly for
introspection, rather than the scoring logic being opaque.

Design notes on the weights (informed by well-known churn drivers in the
Telco Customer Churn dataset this heuristic runs against):
- Contract type is the single strongest signal: month-to-month customers can
  leave with no penalty, so they carry the highest weight.
- Tenure is bucketed rather than linear: the risk drop-off from a brand-new
  customer to a 6+ month one is much steeper than from 12 to 24 months.
- Electronic check payment, lacking tech support / online security, being on
  paperless billing, and being a senior citizen are all established weaker
  secondary signals in this dataset.
- The "MonthlyCharges/TotalCharges ratio" factor asks: does this customer's
  current monthly rate imply they've been charged less, historically, than
  their tenure would predict? A shortfall suggests a recent price increase —
  a common churn trigger — rather than treating the raw ratio (which mostly
  just re-encodes tenure) as its own factor.
All factors here are risk-increasing by construction; none of the fields
named in the assessment's rubric naturally *reduce* risk, so no protective
factors are modeled. `RiskFactor.direction` remains available for future use.
"""

from app.models.customer import Customer
from app.models.risk import RiskFactor, RiskScore, RiskTier

CONTRACT_MONTH_TO_MONTH_WEIGHT = 30.0
CONTRACT_ONE_YEAR_WEIGHT = 10.0
CONTRACT_TWO_YEAR_WEIGHT = 0.0

# (tenure upper bound in months, inclusive) -> weight. First matching bucket wins.
TENURE_WEIGHT_BUCKETS: list[tuple[int, float]] = [
    (5, 25.0),  # 0-5 months: brand new
    (11, 15.0),  # 6-11 months
    (23, 5.0),  # 12-23 months
    (10**9, 0.0),  # 24+ months: effectively no tenure risk
]

ELECTRONIC_CHECK_WEIGHT = 15.0
NO_TECH_SUPPORT_WEIGHT = 10.0
NO_ONLINE_SECURITY_WEIGHT = 8.0
PAPERLESS_BILLING_WEIGHT = 4.0
SENIOR_CITIZEN_WEIGHT = 5.0

CHARGES_INCREASE_WEIGHT = 8.0
# Flag a "recent charge increase" signal when total_charges paid so far is
# more than this fraction below what the current monthly rate would predict
# over the customer's tenure.
CHARGES_INCREASE_SHORTFALL_RATIO = 0.1

HIGH_RISK_THRESHOLD = 70
MEDIUM_RISK_THRESHOLD = 40

MAX_SCORE = 100
MIN_SCORE = 0


def _contract_factor(customer: Customer) -> RiskFactor | None:
    if customer.contract == "Month-to-month":
        weight = CONTRACT_MONTH_TO_MONTH_WEIGHT
    elif customer.contract == "One year":
        weight = CONTRACT_ONE_YEAR_WEIGHT
    else:
        weight = CONTRACT_TWO_YEAR_WEIGHT

    if weight <= 0:
        return None
    return RiskFactor(
        name=f"Contract: {customer.contract}", contribution=weight, direction="increases_risk"
    )


def _tenure_factor(customer: Customer) -> RiskFactor | None:
    for max_tenure, weight in TENURE_WEIGHT_BUCKETS:
        if customer.tenure <= max_tenure:
            if weight <= 0:
                return None
            return RiskFactor(
                name=f"Tenure: {customer.tenure} months",
                contribution=weight,
                direction="increases_risk",
            )
    return None  # pragma: no cover - last bucket's upper bound is unreachable


def _payment_method_factor(customer: Customer) -> RiskFactor | None:
    if customer.payment_method == "Electronic check":
        return RiskFactor(
            name="Payment method: electronic check",
            contribution=ELECTRONIC_CHECK_WEIGHT,
            direction="increases_risk",
        )
    return None


def _tech_support_factor(customer: Customer) -> RiskFactor | None:
    if customer.tech_support == "No":
        return RiskFactor(
            name="Tech support: none",
            contribution=NO_TECH_SUPPORT_WEIGHT,
            direction="increases_risk",
        )
    return None


def _online_security_factor(customer: Customer) -> RiskFactor | None:
    if customer.online_security == "No":
        return RiskFactor(
            name="Online security: none",
            contribution=NO_ONLINE_SECURITY_WEIGHT,
            direction="increases_risk",
        )
    return None


def _paperless_billing_factor(customer: Customer) -> RiskFactor | None:
    if customer.paperless_billing:
        return RiskFactor(
            name="Paperless billing: yes",
            contribution=PAPERLESS_BILLING_WEIGHT,
            direction="increases_risk",
        )
    return None


def _senior_citizen_factor(customer: Customer) -> RiskFactor | None:
    if customer.senior_citizen:
        return RiskFactor(
            name="Senior citizen", contribution=SENIOR_CITIZEN_WEIGHT, direction="increases_risk"
        )
    return None


def _charges_trend_factor(customer: Customer) -> RiskFactor | None:
    if customer.tenure <= 0:
        return None
    expected_total = customer.monthly_charges * customer.tenure
    if expected_total <= 0:
        return None

    shortfall_ratio = (expected_total - customer.total_charges) / expected_total
    if shortfall_ratio > CHARGES_INCREASE_SHORTFALL_RATIO:
        return RiskFactor(
            name="Monthly charges elevated vs. billing history",
            contribution=CHARGES_INCREASE_WEIGHT,
            direction="increases_risk",
        )
    return None


_FACTOR_FUNCTIONS = (
    _contract_factor,
    _tenure_factor,
    _payment_method_factor,
    _tech_support_factor,
    _online_security_factor,
    _paperless_billing_factor,
    _senior_citizen_factor,
    _charges_trend_factor,
)


def _tier_for_score(score: int) -> RiskTier:
    if score >= HIGH_RISK_THRESHOLD:
        return RiskTier.HIGH
    if score >= MEDIUM_RISK_THRESHOLD:
        return RiskTier.MEDIUM
    return RiskTier.LOW


def compute_risk_score(customer: Customer) -> RiskScore:
    """Compute a customer's churn risk score, tier, and factor breakdown."""
    factors = [factor for f in _FACTOR_FUNCTIONS if (factor := f(customer)) is not None]
    raw_score = sum(factor.contribution for factor in factors)
    score = int(round(min(max(raw_score, MIN_SCORE), MAX_SCORE)))
    return RiskScore(score=score, tier=_tier_for_score(score), factors=factors)
