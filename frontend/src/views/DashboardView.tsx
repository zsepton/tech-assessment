import { useState } from "react";
import { Link } from "react-router-dom";
import { getCustomers } from "../api";
import type { PaginatedCustomers } from "../api";
import { DashboardTableSkeleton } from "../components/DashboardTableSkeleton";
import { ErrorBanner } from "../components/ErrorBanner";
import { FilterBar } from "../components/FilterBar";
import type { CustomerFilters } from "../components/FilterBar";
import { OutreachBadge } from "../components/OutreachBadge";
import { Pagination } from "../components/Pagination";
import { RiskBadge } from "../components/RiskBadge";
import { useAsync } from "../hooks/useAsync";
import "./DashboardView.css";

const LIMIT = 20;

const EMPTY_FILTERS: CustomerFilters = { riskTier: "", contract: "", outreachStatus: "" };
const EMPTY_PAGE: PaginatedCustomers = { items: [], total: 0, offset: 0, limit: LIMIT };

export function DashboardView() {
  const [filters, setFilters] = useState<CustomerFilters>(EMPTY_FILTERS);
  const [offset, setOffset] = useState(0);

  const { data, loading, error } = useAsync(
    () =>
      getCustomers({
        offset,
        limit: LIMIT,
        risk_tier: filters.riskTier || undefined,
        contract: filters.contract || undefined,
        outreach_status: filters.outreachStatus || undefined,
      }),
    EMPTY_PAGE,
    [offset, filters],
  );

  function handleFiltersChange(next: CustomerFilters) {
    setFilters(next);
    setOffset(0);
  }

  function goPrev() {
    setOffset((prev) => Math.max(0, prev - LIMIT));
  }

  function goNext() {
    setOffset((prev) => prev + LIMIT);
  }

  return (
    <div className="dashboard">
      <div className="dashboard__header">
        <h1>Customer risk dashboard</h1>
        {!loading && !error && (
          <p className="dashboard__subtitle">
            {data.total.toLocaleString()} customers · sorted by risk score, high to low
          </p>
        )}
      </div>

      <FilterBar filters={filters} onChange={handleFiltersChange} />

      {loading && <DashboardTableSkeleton />}
      {error && <ErrorBanner message={error} />}

      {!loading && !error && (
        <>
          <div className="dashboard__table-card">
            <table>
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Contract</th>
                  <th>Tenure</th>
                  <th>Monthly charges</th>
                  <th>Risk score</th>
                  <th>Outreach</th>
                  <th aria-hidden="true"></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.customer_id}>
                    <td className="dashboard__customer-id">
                      <Link to={`/customers/${item.customer_id}`}>{item.customer_id}</Link>
                    </td>
                    <td>{item.contract}</td>
                    <td>{item.tenure} mo</td>
                    <td>${item.monthly_charges.toFixed(2)}</td>
                    <td>
                      <RiskBadge tier={item.risk_tier} score={item.risk_score} />
                    </td>
                    <td>
                      <OutreachBadge status={item.outreach_status} />
                    </td>
                    <td className="dashboard__view-link">
                      <Link
                        to={`/customers/${item.customer_id}`}
                        aria-label={`View ${item.customer_id}`}
                      >
                        ›
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.items.length === 0 && (
              <p className="dashboard__empty">No customers match these filters.</p>
            )}
          </div>

          <Pagination
            offset={data.offset}
            limit={data.limit}
            total={data.total}
            onPrev={goPrev}
            onNext={goNext}
          />
        </>
      )}
    </div>
  );
}
