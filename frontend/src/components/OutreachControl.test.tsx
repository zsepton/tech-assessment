import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as api from "../api";
import { ApiError } from "../api";
import type { CustomerDetail } from "../api";
import { OutreachControl } from "./OutreachControl";

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return { ...actual, updateOutreachStatus: vi.fn() };
});

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
      outreach_status: "IN_PROGRESS",
    },
    risk: { score: 92, tier: "High", factors: [] },
    ...overrides,
  };
}

describe("OutreachControl", () => {
  it("offers the legal next transition for NOT_CONTACTED", () => {
    render(<OutreachControl customerId="7590-VHVEG" status="NOT_CONTACTED" onUpdated={vi.fn()} />);

    expect(screen.getByText("Not contacted")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark as In progress →" })).toBeInTheDocument();
  });

  it("offers the legal next transition for IN_PROGRESS", () => {
    render(<OutreachControl customerId="7590-VHVEG" status="IN_PROGRESS" onUpdated={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Mark as Resolved →" })).toBeInTheDocument();
  });

  it("shows a terminal message with no button for RESOLVED", () => {
    render(<OutreachControl customerId="7590-VHVEG" status="RESOLVED" onUpdated={vi.fn()} />);

    expect(screen.getByText("No further action")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows an updating state and calls onUpdated with the server response on success", async () => {
    let resolveUpdate!: (value: CustomerDetail) => void;
    const updatePromise = new Promise<CustomerDetail>((resolve) => {
      resolveUpdate = resolve;
    });
    updateOutreachStatusMock.mockReturnValue(updatePromise);
    const onUpdated = vi.fn();
    const user = userEvent.setup();

    render(
      <OutreachControl customerId="7590-VHVEG" status="NOT_CONTACTED" onUpdated={onUpdated} />,
    );

    const button = screen.getByRole("button", { name: "Mark as In progress →" });
    await user.click(button);

    expect(screen.getByRole("button", { name: "Updating…" })).toBeDisabled();
    expect(updateOutreachStatusMock).toHaveBeenCalledWith("7590-VHVEG", "IN_PROGRESS");

    resolveUpdate(makeDetail());
    await waitFor(() => expect(onUpdated).toHaveBeenCalledWith(makeDetail()));
    expect(screen.getByRole("button", { name: "Mark as In progress →" })).toBeEnabled();
  });

  it("shows the ApiError detail and does not call onUpdated on failure", async () => {
    updateOutreachStatusMock.mockRejectedValue(
      new ApiError(
        "boom",
        400,
        "Cannot transition outreach status from NOT_CONTACTED to RESOLVED.",
      ),
    );
    const onUpdated = vi.fn();
    const user = userEvent.setup();

    render(
      <OutreachControl customerId="7590-VHVEG" status="NOT_CONTACTED" onUpdated={onUpdated} />,
    );

    await user.click(screen.getByRole("button", { name: "Mark as In progress →" }));

    await waitFor(() =>
      expect(
        screen.getByText("Cannot transition outreach status from NOT_CONTACTED to RESOLVED."),
      ).toBeInTheDocument(),
    );
    expect(onUpdated).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Mark as In progress →" })).toBeEnabled();
  });

  it("shows a generic error message for a non-ApiError failure", async () => {
    updateOutreachStatusMock.mockRejectedValue(new Error("network down"));
    const user = userEvent.setup();

    render(<OutreachControl customerId="7590-VHVEG" status="NOT_CONTACTED" onUpdated={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Mark as In progress →" }));

    await waitFor(() => expect(screen.getByText("Something went wrong.")).toBeInTheDocument());
  });

  it("does not call onUpdated if unmounted while the update request is in flight", async () => {
    let resolveUpdate!: (value: CustomerDetail) => void;
    const updatePromise = new Promise<CustomerDetail>((resolve) => {
      resolveUpdate = resolve;
    });
    updateOutreachStatusMock.mockReturnValue(updatePromise);
    const onUpdated = vi.fn();
    const user = userEvent.setup();

    const { unmount } = render(
      <OutreachControl customerId="7590-VHVEG" status="NOT_CONTACTED" onUpdated={onUpdated} />,
    );
    await user.click(screen.getByRole("button", { name: "Mark as In progress →" }));

    unmount();
    resolveUpdate(makeDetail());

    await waitFor(() => expect(updateOutreachStatusMock).toHaveBeenCalledTimes(1));
    expect(onUpdated).not.toHaveBeenCalled();
  });

  it("does not throw if unmounted while the update request is failing", async () => {
    let rejectUpdate!: (error: unknown) => void;
    const updatePromise = new Promise<CustomerDetail>((_resolve, reject) => {
      rejectUpdate = reject;
    });
    updateOutreachStatusMock.mockReturnValue(updatePromise);
    const user = userEvent.setup();

    const { unmount } = render(
      <OutreachControl customerId="7590-VHVEG" status="NOT_CONTACTED" onUpdated={vi.fn()} />,
    );
    await user.click(screen.getByRole("button", { name: "Mark as In progress →" }));

    unmount();
    rejectUpdate(new ApiError("stale", 500, "Stale failure"));

    await waitFor(() => expect(updateOutreachStatusMock).toHaveBeenCalledTimes(1));
  });
});
