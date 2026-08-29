import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DetailSkeleton } from "./DetailSkeleton";

describe("DetailSkeleton", () => {
  it("renders the header and two-card body placeholders", () => {
    const { container } = render(<DetailSkeleton />);

    expect(container.querySelector(".detail-skeleton__header")).toBeInTheDocument();
    expect(container.querySelector(".detail-skeleton__body")).toBeInTheDocument();
  });
});
