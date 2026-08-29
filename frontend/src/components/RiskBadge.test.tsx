import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RiskBadge } from "./RiskBadge";

describe("RiskBadge", () => {
  it("renders the score and tier", () => {
    render(<RiskBadge tier="High" score={91} />);

    expect(screen.getByText("91 · High")).toBeInTheDocument();
  });

  it.each([
    ["High", "risk-badge--high"],
    ["Medium", "risk-badge--medium"],
    ["Low", "risk-badge--low"],
  ] as const)("applies the %s tier class", (tier, expectedClass) => {
    render(<RiskBadge tier={tier} score={50} />);

    expect(screen.getByText(`50 · ${tier}`)).toHaveClass(expectedClass);
  });
});
