import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DashboardTableSkeleton } from "./DashboardTableSkeleton";

describe("DashboardTableSkeleton", () => {
  it("renders 8 placeholder rows", () => {
    const { container } = render(<DashboardTableSkeleton />);

    expect(container.querySelectorAll(".dashboard-table-skeleton__row")).toHaveLength(8);
  });
});
