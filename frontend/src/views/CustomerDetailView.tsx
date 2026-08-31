import { Link, useParams } from "react-router-dom";
import { getCustomer, getModelInfo } from "../api";
import type { Customer, CustomerDetail, ModelInfo } from "../api";
import { DetailSkeleton } from "../components/DetailSkeleton";
import { ErrorBanner } from "../components/ErrorBanner";
import { OutreachControl } from "../components/OutreachControl";
import { RiskBadge } from "../components/RiskBadge";
import { useAsync } from "../hooks/useAsync";
import "./CustomerDetailView.css";

const PROFILE_FIELDS: Array<[string, (c: Customer) => string]> = [
  ["Gender", (c) => c.gender],
  ["Senior citizen", (c) => (c.senior_citizen ? "Yes" : "No")],
  ["Partner", (c) => (c.partner ? "Yes" : "No")],
  ["Dependents", (c) => (c.dependents ? "Yes" : "No")],
  ["Phone service", (c) => (c.phone_service ? "Yes" : "No")],
  ["Multiple lines", (c) => c.multiple_lines],
  ["Internet service", (c) => c.internet_service],
  ["Online security", (c) => c.online_security],
  ["Online backup", (c) => c.online_backup],
  ["Device protection", (c) => c.device_protection],
  ["Tech support", (c) => c.tech_support],
  ["Streaming TV", (c) => c.streaming_tv],
  ["Streaming movies", (c) => c.streaming_movies],
  ["Paperless billing", (c) => (c.paperless_billing ? "Yes" : "No")],
  ["Payment method", (c) => c.payment_method],
  ["Total charges", (c) => `$${c.total_charges.toFixed(2)}`],
];

export function CustomerDetailView() {
  const { customerId } = useParams<{ customerId: string }>();

  const {
    data: detail,
    setData: setDetail,
    loading,
    error,
  } = useAsync<CustomerDetail | null>(
    () => (customerId ? getCustomer(customerId) : Promise.resolve(null)),
    null,
    [customerId],
  );

  // Model info is supplementary context (the tier thresholds footnote
  // below); a failure here shouldn't block the main customer detail, so
  // this hook's own loading/error state is intentionally left unused.
  const { data: modelInfo } = useAsync<ModelInfo | null>(
    () => (customerId ? getModelInfo() : Promise.resolve(null)),
    null,
    [customerId],
  );

  const maxContribution =
    detail && detail.risk.factors.length > 0
      ? Math.max(...detail.risk.factors.map((f) => f.contribution))
      : 1;

  if (!customerId) {
    return (
      <div className="detail">
        <Link to="/" className="detail__back">
          ‹ Back to dashboard
        </Link>
        <ErrorBanner message="No customer id was provided." />
      </div>
    );
  }

  return (
    <div className="detail">
      <Link to="/" className="detail__back">
        ‹ Back to dashboard
      </Link>

      {loading && <DetailSkeleton />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && detail && (
        <>
          <div className="detail__header">
            <div>
              <div className="detail__customer-id">{detail.customer.customer_id}</div>
              <div className="detail__summary">
                {detail.customer.contract} · {detail.customer.tenure} mo tenure · $
                {detail.customer.monthly_charges.toFixed(2)}/mo
              </div>
            </div>
            <div className="detail__header-right">
              <RiskBadge tier={detail.risk.tier} score={detail.risk.score} />
            </div>
          </div>

          <div className="detail__card detail__outreach-row">
            <OutreachControl
              customerId={detail.customer.customer_id}
              status={detail.customer.outreach_status}
              onUpdated={setDetail}
            />
          </div>

          <div className="detail__body">
            <div className="detail__card">
              <h2>Why this score</h2>
              {detail.risk.factors.length === 0 ? (
                <p className="detail__no-factors">
                  No risk factors were triggered for this customer.
                </p>
              ) : (
                <ul className="detail__factors">
                  {detail.risk.factors.map((factor) => (
                    <li key={factor.name} className="detail__factor">
                      <span className="detail__factor-name">{factor.name}</span>
                      <span className="detail__factor-bar-track">
                        <span
                          className={`detail__factor-bar-fill detail__factor-bar-fill--${factor.direction}`}
                          style={{ width: `${(factor.contribution / maxContribution) * 100}%` }}
                        />
                      </span>
                      <span
                        className={`detail__factor-contribution detail__factor-contribution--${factor.direction}`}
                      >
                        {factor.direction === "increases_risk" ? "+" : "−"}
                        {factor.contribution}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              {modelInfo && (
                <p className="detail__model-note">
                  Weights sourced from the current model rules — high risk starts at{" "}
                  {modelInfo.high_risk_threshold}, medium at {modelInfo.medium_risk_threshold}.
                </p>
              )}
            </div>

            <div className="detail__card">
              <h2>Customer profile</h2>
              <dl className="detail__profile">
                {PROFILE_FIELDS.map(([label, getValue]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{getValue(detail.customer)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
