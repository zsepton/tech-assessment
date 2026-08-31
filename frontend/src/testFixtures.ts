import type { Customer, CustomerDetail } from "./api";

/**
 * Shared customer test fixture, used across App/DashboardView/
 * CustomerDetailView/OutreachControl's test suites so the same ~20-field
 * `Customer` object isn't hand-duplicated in each file. `overrides` merges
 * shallowly, matching how each call site previously spread its own
 * `overrides` over a local literal.
 */
export function makeCustomer(overrides: Partial<Customer> = {}): Customer {
  return {
    customer_id: "7590-VHVEG",
    gender: "Female",
    senior_citizen: false,
    partner: true,
    dependents: false,
    tenure: 1,
    phone_service: false,
    multiple_lines: "No phone service",
    internet_service: "DSL",
    online_security: "No",
    online_backup: "Yes",
    device_protection: "No",
    tech_support: "No",
    streaming_tv: "No",
    streaming_movies: "No",
    contract: "Month-to-month",
    paperless_billing: true,
    payment_method: "Electronic check",
    monthly_charges: 29.85,
    total_charges: 29.85,
    outreach_status: "NOT_CONTACTED",
    ...overrides,
  };
}

export function makeCustomerDetail(overrides: Partial<CustomerDetail> = {}): CustomerDetail {
  return {
    customer: makeCustomer(),
    risk: { score: 92, tier: "High", factors: [] },
    ...overrides,
  };
}
