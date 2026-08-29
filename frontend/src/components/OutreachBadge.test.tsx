import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { OutreachBadge } from "./OutreachBadge";

describe("OutreachBadge", () => {
  it.each([
    ["NOT_CONTACTED", "Not contacted", "outreach-badge--neutral"],
    ["IN_PROGRESS", "In progress", "outreach-badge--progress"],
    ["RESOLVED", "Resolved", "outreach-badge--resolved"],
  ] as const)("renders %s as %s", (status, label, expectedClass) => {
    render(<OutreachBadge status={status} />);

    expect(screen.getByText(label)).toHaveClass(expectedClass);
  });
});
