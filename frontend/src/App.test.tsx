import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { getCustomer, getCustomers, getModelInfo } from "./api";
import App from "./App";
import { makeCustomerDetail } from "./testFixtures";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return { ...actual, getCustomers: vi.fn(), getCustomer: vi.fn(), getModelInfo: vi.fn() };
});

describe("App", () => {
  it("renders the customer dashboard at the root route", async () => {
    vi.mocked(getCustomers).mockResolvedValue({ items: [], total: 0, offset: 0, limit: 20 });

    render(<App />);

    await waitFor(() => expect(screen.getByText("Customer risk dashboard")).toBeInTheDocument());
  });

  it("renders the customer detail view when navigating to /customers/:id", async () => {
    window.history.pushState({}, "", "/customers/7590-VHVEG");
    vi.mocked(getCustomer).mockResolvedValue(makeCustomerDetail());
    vi.mocked(getModelInfo).mockResolvedValue({
      contract_weights: {},
      tenure_weight_buckets: [],
      electronic_check_weight: 0,
      no_tech_support_weight: 0,
      no_online_security_weight: 0,
      paperless_billing_weight: 0,
      senior_citizen_weight: 0,
      charges_increase_weight: 0,
      charges_increase_shortfall_ratio: 0,
      high_risk_threshold: 70,
      medium_risk_threshold: 40,
      min_score: 0,
      max_score: 100,
    });

    render(<App />);

    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());
  });
});
