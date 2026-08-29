import type { OutreachStatus, RiskTier } from "../api";
import "./FilterBar.css";

export interface CustomerFilters {
  riskTier: RiskTier | "";
  contract: string;
  outreachStatus: OutreachStatus | "";
}

interface FilterBarProps {
  filters: CustomerFilters;
  onChange: (filters: CustomerFilters) => void;
}

const CONTRACTS = ["Month-to-month", "One year", "Two year"];

export function FilterBar({ filters, onChange }: FilterBarProps) {
  return (
    <div className="filter-bar">
      <select
        aria-label="Filter by risk tier"
        value={filters.riskTier}
        onChange={(e) => onChange({ ...filters, riskTier: e.target.value as RiskTier | "" })}
      >
        <option value="">All risk tiers</option>
        <option value="High">High</option>
        <option value="Medium">Medium</option>
        <option value="Low">Low</option>
      </select>

      <select
        aria-label="Filter by contract"
        value={filters.contract}
        onChange={(e) => onChange({ ...filters, contract: e.target.value })}
      >
        <option value="">All contracts</option>
        {CONTRACTS.map((contract) => (
          <option key={contract} value={contract}>
            {contract}
          </option>
        ))}
      </select>

      <select
        aria-label="Filter by outreach status"
        value={filters.outreachStatus}
        onChange={(e) =>
          onChange({ ...filters, outreachStatus: e.target.value as OutreachStatus | "" })
        }
      >
        <option value="">All outreach statuses</option>
        <option value="NOT_CONTACTED">Not contacted</option>
        <option value="IN_PROGRESS">In progress</option>
        <option value="RESOLVED">Resolved</option>
      </select>

      {(filters.riskTier || filters.contract || filters.outreachStatus) && (
        <button
          type="button"
          className="filter-bar__clear"
          onClick={() => onChange({ riskTier: "", contract: "", outreachStatus: "" })}
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
