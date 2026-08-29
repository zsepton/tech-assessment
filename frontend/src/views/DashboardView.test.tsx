import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as api from "../api";
import { ApiError } from "../api";
import type { PaginatedCustomers } from "../api";
import { DashboardView } from "./DashboardView";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    getCustomers: vi.fn(),
  };
});

const getCustomersMock = vi.mocked(api.getCustomers);

afterEach(() => {
  vi.clearAllMocks();
});

function makePage(overrides: Partial<PaginatedCustomers> = {}): PaginatedCustomers {
  return {
    items: [
      {
        customer_id: "7590-VHVEG",
        contract: "Month-to-month",
        tenure: 2,
        monthly_charges: 53.85,
        outreach_status: "NOT_CONTACTED",
        risk_score: 91,
        risk_tier: "High",
      },
    ],
    total: 1,
    offset: 0,
    limit: 20,
    ...overrides,
  };
}

describe("DashboardView", () => {
  it("renders customers once loaded", async () => {
    getCustomersMock.mockResolvedValue(makePage());
    render(<DashboardView />);

    expect(screen.getByText("Loading…")).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());
    const table = within(screen.getByRole("table"));
    expect(table.getByText("91 · High")).toBeInTheDocument();
    expect(table.getByText("Not contacted")).toBeInTheDocument();
  });

  it("shows an error message when the request fails with an ApiError", async () => {
    getCustomersMock.mockRejectedValue(new ApiError("boom", 500, "Server error"));
    render(<DashboardView />);

    await waitFor(() => expect(screen.getByText("Server error")).toBeInTheDocument());
  });

  it("shows a generic error message for a non-ApiError failure", async () => {
    getCustomersMock.mockRejectedValue(new Error("weird"));
    render(<DashboardView />);

    await waitFor(() => expect(screen.getByText("Something went wrong.")).toBeInTheDocument());
  });

  it("shows an empty state when there are no matching customers", async () => {
    getCustomersMock.mockResolvedValue(makePage({ items: [], total: 0 }));
    render(<DashboardView />);

    await waitFor(() =>
      expect(screen.getByText("No customers match these filters.")).toBeInTheDocument(),
    );
  });

  it("resets to offset 0 and re-fetches with the new filter when a filter changes", async () => {
    getCustomersMock.mockResolvedValue(makePage());
    const user = userEvent.setup();
    render(<DashboardView />);
    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());

    await user.selectOptions(screen.getByLabelText("Filter by risk tier"), "High");

    await waitFor(() =>
      expect(getCustomersMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ offset: 0, risk_tier: "High" }),
      ),
    );
  });

  it("moves to the next page and re-fetches with the new offset", async () => {
    getCustomersMock.mockResolvedValue(makePage({ total: 100 }));
    const user = userEvent.setup();
    render(<DashboardView />);
    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());

    await user.click(screen.getByText("Next ›"));

    await waitFor(() =>
      expect(getCustomersMock).toHaveBeenLastCalledWith(expect.objectContaining({ offset: 20 })),
    );
  });

  it("moves back to the previous page and re-fetches with the earlier offset", async () => {
    getCustomersMock.mockResolvedValue(makePage({ total: 100, offset: 20 }));
    const user = userEvent.setup();
    render(<DashboardView />);
    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());

    await user.click(screen.getByText("‹ Prev"));

    await waitFor(() =>
      expect(getCustomersMock).toHaveBeenLastCalledWith(expect.objectContaining({ offset: 0 })),
    );
  });

  it("ignores a stale response that resolves after a newer request has superseded it", async () => {
    let resolveStale!: (value: PaginatedCustomers) => void;
    const stalePromise = new Promise<PaginatedCustomers>((resolve) => {
      resolveStale = resolve;
    });
    getCustomersMock.mockReturnValueOnce(stalePromise);
    getCustomersMock.mockResolvedValueOnce(makePage({ total: 5 }));

    const user = userEvent.setup();
    render(<DashboardView />);

    // Trigger a second, superseding request before the first resolves.
    await user.selectOptions(screen.getByLabelText("Filter by risk tier"), "High");
    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());

    // Resolving the stale request now must not overwrite the current view.
    resolveStale(makePage({ total: 999 }));
    await waitFor(() => expect(getCustomersMock).toHaveBeenCalledTimes(2));

    expect(screen.queryByText(/999/)).not.toBeInTheDocument();
  });

  it("ignores a stale rejection that resolves after a newer request has superseded it", async () => {
    let rejectStale!: (error: unknown) => void;
    const stalePromise = new Promise<PaginatedCustomers>((_resolve, reject) => {
      rejectStale = reject;
    });
    getCustomersMock.mockReturnValueOnce(stalePromise);
    getCustomersMock.mockResolvedValueOnce(makePage());

    const user = userEvent.setup();
    render(<DashboardView />);

    await user.selectOptions(screen.getByLabelText("Filter by risk tier"), "High");
    await waitFor(() => expect(screen.getByText("7590-VHVEG")).toBeInTheDocument());

    rejectStale(new ApiError("stale failure", 500, "Stale failure"));
    await waitFor(() => expect(getCustomersMock).toHaveBeenCalledTimes(2));

    expect(screen.queryByText("Stale failure")).not.toBeInTheDocument();
    expect(screen.getByText("7590-VHVEG")).toBeInTheDocument();
  });
});
