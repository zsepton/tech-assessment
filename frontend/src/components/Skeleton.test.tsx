import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Skeleton } from "./Skeleton";

describe("Skeleton", () => {
  it("renders with the given width and height", () => {
    const { container } = render(<Skeleton width="42px" height="7px" />);

    const el = container.querySelector(".skeleton");
    expect(el).toHaveStyle({ width: "42px", height: "7px" });
  });

  it("defaults to a full-width, text-height block", () => {
    const { container } = render(<Skeleton />);

    const el = container.querySelector(".skeleton");
    expect(el).toHaveStyle({ width: "100%", height: "14px" });
  });
});
