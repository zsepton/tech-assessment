export type RiskTier = "Low" | "Medium" | "High";

export type OutreachStatus = "NOT_CONTACTED" | "IN_PROGRESS" | "RESOLVED";

export interface RiskFactor {
  name: string;
  contribution: number;
  direction: "increases_risk" | "decreases_risk";
}

export interface RiskScore {
  score: number;
  tier: RiskTier;
  factors: RiskFactor[];
}

/** One row in the paginated customer list — summary fields plus computed risk. */
export interface CustomerListItem {
  customer_id: string;
  contract: string;
  tenure: number;
  monthly_charges: number;
  outreach_status: OutreachStatus;
  risk_score: number;
  risk_tier: RiskTier;
}

export interface PaginatedCustomers {
  items: CustomerListItem[];
  total: number;
  offset: number;
  limit: number;
}

/**
 * A customer record, as returned by the API. Excludes the historical `churn`
 * outcome label present in the source CSV: the backend never serializes it,
 * since it's the ground-truth answer the risk score predicts, not a
 * prospective signal.
 */
export interface Customer {
  customer_id: string;
  gender: string;
  senior_citizen: boolean;
  partner: boolean;
  dependents: boolean;
  tenure: number;
  phone_service: boolean;
  multiple_lines: string;
  internet_service: string;
  online_security: string;
  online_backup: string;
  device_protection: string;
  tech_support: string;
  streaming_tv: string;
  streaming_movies: string;
  contract: string;
  paperless_billing: boolean;
  payment_method: string;
  monthly_charges: number;
  total_charges: number;
  outreach_status: OutreachStatus;
}

export interface CustomerDetail {
  customer: Customer;
  risk: RiskScore;
}

export interface OutreachUpdateRequest {
  status: OutreachStatus;
}

/** The scoring engine's current weights, rules, and tier thresholds. */
export interface ModelInfo {
  contract_weights: Record<string, number>;
  tenure_weight_buckets: [number, number][];
  electronic_check_weight: number;
  no_tech_support_weight: number;
  no_online_security_weight: number;
  paperless_billing_weight: number;
  senior_citizen_weight: number;
  charges_increase_weight: number;
  charges_increase_shortfall_ratio: number;
  high_risk_threshold: number;
  medium_risk_threshold: number;
  min_score: number;
  max_score: number;
}

export interface CustomerListParams {
  offset?: number;
  limit?: number;
  risk_tier?: RiskTier;
  contract?: string;
  outreach_status?: OutreachStatus;
}
