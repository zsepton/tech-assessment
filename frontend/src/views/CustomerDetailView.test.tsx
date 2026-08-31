import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as api from "../api";
import { ApiError } from "../api";
import type { CustomerDetail, ModelInfo } from "../api";
import { CustomerDetailView } from "./CustomerDetailView";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    getCustomer: vi.fn(),
    getModelInfo: vi.fn(),
    updateOutreachStatus: vi.fn(),
  };
});

const getCustomerMock = vi.mocked(api.getCustomer);
const getModelInfoMock = vi.mocked(api.getModelInfo);
const updateOutreachStatusMock = vi.mocked(api.updateOutreachStatus);

afterEach(() => {
  vi.clearAllMocks();
});

function makeDetail(overrides: Partial<CustomerDetail> = {}): CustomerDetail {
  return {
    customer: {
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
    },
    risk: {
      score: 92,
      tier: "High",
      factors: [
        { name: "Contract: Month-to-month", contribution: 30, direction: "increases_risk" },
        { name: "Tenure: 1 months", contribution: 25, direction: "increases_risk" },
      ],
    },
    ...overrides,
  };
}

function makeModelInfo(overrides: Partial<ModelInfo> = {}): ModelInfo {
  return {
    contract_weights: { "Month-to-month": 30, "One year": 10, "Two year": 0 },
    tenure_weight_buckets: [
      [5, 25],
      [11, 15],
      [23, 5],
      [1000000000, 0],
    ],
    electronic_check_weight: 15,
    no_tech_support_weight: 10,
    no_online_security_weight: 8,
    paperless_billing_weight: 4,
    senior_citizen_weight: 5,
    charges_increase_weight: 8,
    charges_increase_shortfall_ratio: 0.1,
    high_risk_threshold: 70,
    medium_risk_threshold: 40,
    min_score: 0,
    max_score: 100,
    ...overrides,
  };
}

function renderDetail(customerId = "7590-VHVEG") {
  return render(
    <MemoryRouter initialEntries={[`/customers/${customerId}`]}>
      <Routes>
        <Route path="/customers/:customerId" element={<CustomerDetailView />} />
        <Route path="/" element={<div>Dashboard page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("CustomerDetailView", () => {
  it("renders the customer profile, risk score, and outreach status", async () => {
    getCustomerMock.mockResolvedValue(makeDetail());
    getModelInfoMock.mockResolvedValue(makeModelInfo());

    const { container } = renderDetail();

    expect(container.querySelector(".detail-skeleton")).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());
    expect(screen.getByText("92 · High")).toBeInTheDocument();
    expect(screen.getByText("Not contacted")).toBeInTheDocument();
    expect(screen.getByText("Female")).toBeInTheDocument();
    expect(screen.getByText("Contract: Month-to-month")).toBeInTheDocument();
    expect(screen.getByText("+30")).toBeInTheDocument();
  });

  it("renders a decreases_risk factor with a minus sign", async () => {
    getCustomerMock.mockResolvedValue(
      makeDetail({
        risk: {
          score: 10,
          tier: "Low",
          factors: [{ name: "Two year contract", contribution: 10, direction: "decreases_risk" }],
        },
      }),
    );
    getModelInfoMock.mockResolvedValue(makeModelInfo());

    renderDetail();

    await waitFor(() => expect(screen.getByText("−10")).toBeInTheDocument());
  });

  it("renders the inverse boolean profile fields correctly", async () => {
    const base = makeDetail();
    getCustomerMock.mockResolvedValue(
      makeDetail({
        customer: {
          ...base.customer,
          senior_citizen: true,
          partner: false,
          dependents: true,
          phone_service: true,
          paperless_billing: false,
        },
      }),
    );
    getModelInfoMock.mockResolvedValue(makeModelInfo());

    renderDetail();

    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());
    const yesValues = screen.getAllByText("Yes");
    const noValues = screen.getAllByText("No");
    // senior citizen, dependents, phone service -> Yes; partner, paperless billing -> No
    expect(yesValues.length).toBeGreaterThanOrEqual(3);
    expect(noValues.length).toBeGreaterThanOrEqual(2);
  });

  it("shows the model-info footnote once it loads", async () => {
    getCustomerMock.mockResolvedValue(makeDetail());
    getModelInfoMock.mockResolvedValue(
      makeModelInfo({ high_risk_threshold: 70, medium_risk_threshold: 40 }),
    );

    renderDetail();

    await waitFor(() =>
      expect(screen.getByText(/high risk starts at 70, medium at 40/)).toBeInTheDocument(),
    );
  });

  it("still renders the customer detail when model info fails to load", async () => {
    getCustomerMock.mockResolvedValue(makeDetail());
    getModelInfoMock.mockRejectedValue(new ApiError("boom", 500, "Server error"));

    renderDetail();

    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());
    expect(screen.queryByText(/high risk starts at/)).not.toBeInTheDocument();
  });

  it("shows a message when there are no risk factors", async () => {
    getCustomerMock.mockResolvedValue(makeDetail({ risk: { score: 0, tier: "Low", factors: [] } }));
    getModelInfoMock.mockResolvedValue(makeModelInfo());

    renderDetail();

    await waitFor(() =>
      expect(
        screen.getByText("No risk factors were triggered for this customer."),
      ).toBeInTheDocument(),
    );
  });

  it("shows a clear message for an unknown customer id", async () => {
    getCustomerMock.mockRejectedValue(new ApiError("boom", 404, "Customer 'ghost' not found."));
    getModelInfoMock.mockResolvedValue(makeModelInfo());

    renderDetail("ghost");

    await waitFor(() =>
      expect(screen.getByText("Customer 'ghost' not found.")).toBeInTheDocument(),
    );
  });

  it("shows a generic error message for a non-ApiError failure", async () => {
    getCustomerMock.mockRejectedValue(new Error("weird"));
    getModelInfoMock.mockResolvedValue(makeModelInfo());

    renderDetail();

    await waitFor(() => expect(screen.getByText("Something went wrong.")).toBeInTheDocument());
  });

  it("navigates back to the dashboard via the back link", async () => {
    getCustomerMock.mockResolvedValue(makeDetail());
    getModelInfoMock.mockResolvedValue(makeModelInfo());
    const user = userEvent.setup();

    renderDetail();
    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());

    await user.click(screen.getByText("‹ Back to dashboard"));

    expect(screen.getByText("Dashboard page")).toBeInTheDocument();
  });

  it("does not update state after unmounting while the customer request is in flight", async () => {
    let resolveStale!: (value: CustomerDetail) => void;
    const stalePromise = new Promise<CustomerDetail>((resolve) => {
      resolveStale = resolve;
    });
    getCustomerMock.mockReturnValueOnce(stalePromise);
    getModelInfoMock.mockResolvedValue(makeModelInfo());

    const { unmount } = renderDetail();
    unmount();

    resolveStale(makeDetail());
    await waitFor(() => expect(getCustomerMock).toHaveBeenCalledTimes(1));
  });

  it("does not update state after unmounting while the customer request is failing", async () => {
    let rejectStale!: (error: unknown) => void;
    const stalePromise = new Promise<CustomerDetail>((_resolve, reject) => {
      rejectStale = reject;
    });
    getCustomerMock.mockReturnValueOnce(stalePromise);
    getModelInfoMock.mockResolvedValue(makeModelInfo());

    const { unmount } = renderDetail();
    unmount();

    rejectStale(new ApiError("stale", 500, "Stale failure"));
    await waitFor(() => expect(getCustomerMock).toHaveBeenCalledTimes(1));
  });

  it("does not update state after unmounting while the model-info request is in flight", async () => {
    let resolveStale!: (value: ModelInfo) => void;
    const stalePromise = new Promise<ModelInfo>((resolve) => {
      resolveStale = resolve;
    });
    getCustomerMock.mockResolvedValue(makeDetail());
    getModelInfoMock.mockReturnValueOnce(stalePromise);

    const { unmount } = renderDetail();
    unmount();

    resolveStale(makeModelInfo());
    await waitFor(() => expect(getModelInfoMock).toHaveBeenCalledTimes(1));
  });

  it("shows a message when rendered with no customer id", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<CustomerDetailView />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("No customer id was provided.")).toBeInTheDocument();
    expect(getCustomerMock).not.toHaveBeenCalled();
  });

  it("updates the displayed outreach status after a successful transition", async () => {
    getCustomerMock.mockResolvedValue(makeDetail());
    getModelInfoMock.mockResolvedValue(makeModelInfo());
    updateOutreachStatusMock.mockResolvedValue(
      makeDetail({
        customer: { ...makeDetail().customer, outreach_status: "IN_PROGRESS" },
      }),
    );
    const user = userEvent.setup();

    renderDetail();
    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());
    expect(screen.getByText("Not contacted")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Mark as In progress →" }));

    await waitFor(() => expect(screen.getByText("In progress")).toBeInTheDocument());
    expect(updateOutreachStatusMock).toHaveBeenCalledWith("7590-VHVEG", "IN_PROGRESS");
  });
});
