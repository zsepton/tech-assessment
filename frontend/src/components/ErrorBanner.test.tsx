import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ErrorBanner } from "./ErrorBanner";

describe("ErrorBanner", () => {
  it("renders the message with an alert role", () => {
    render(<ErrorBanner message="Something went wrong." />);

    const banner = screen.getByRole("alert");
    expect(banner).toHaveTextContent("Something went wrong.");
  });
});
