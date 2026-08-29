import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { FilterBar } from "./FilterBar";
import type { CustomerFilters } from "./FilterBar";

const EMPTY: CustomerFilters = { riskTier: "", contract: "", outreachStatus: "" };

describe("FilterBar", () => {
  it("does not render a clear button when no filters are active", () => {
    render(<FilterBar filters={EMPTY} onChange={vi.fn()} />);

    expect(screen.queryByText("Clear filters")).not.toBeInTheDocument();
  });

  it("calls onChange with the updated risk tier when changed", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar filters={EMPTY} onChange={onChange} />);

    await user.selectOptions(screen.getByLabelText("Filter by risk tier"), "High");

    expect(onChange).toHaveBeenCalledWith({ ...EMPTY, riskTier: "High" });
  });

  it("calls onChange with the updated contract when changed", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar filters={EMPTY} onChange={onChange} />);

    await user.selectOptions(screen.getByLabelText("Filter by contract"), "Two year");

    expect(onChange).toHaveBeenCalledWith({ ...EMPTY, contract: "Two year" });
  });

  it("calls onChange with the updated outreach status when changed", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar filters={EMPTY} onChange={onChange} />);

    await user.selectOptions(screen.getByLabelText("Filter by outreach status"), "IN_PROGRESS");

    expect(onChange).toHaveBeenCalledWith({ ...EMPTY, outreachStatus: "IN_PROGRESS" });
  });

  it("shows a clear button when a filter is active and resets all filters when clicked", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<FilterBar filters={{ ...EMPTY, riskTier: "High" }} onChange={onChange} />);

    const clearButton = screen.getByText("Clear filters");
    await user.click(clearButton);

    expect(onChange).toHaveBeenCalledWith(EMPTY);
  });
});
