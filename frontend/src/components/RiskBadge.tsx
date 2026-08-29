import type { RiskTier } from "../api";
import "./RiskBadge.css";

interface RiskBadgeProps {
  tier: RiskTier;
  score: number;
}

const TIER_CLASS: Record<RiskTier, string> = {
  Low: "risk-badge--low",
  Medium: "risk-badge--medium",
  High: "risk-badge--high",
};

export function RiskBadge({ tier, score }: RiskBadgeProps) {
  return (
    <span className={`risk-badge ${TIER_CLASS[tier]}`}>
      <span className="risk-badge__dot" />
      {score} · {tier}
    </span>
  );
}
