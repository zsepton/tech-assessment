import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { getCustomers } from "./api";
import App from "./App";

vi.mock("./api", async () => {
  const actual = await vi.importActual<typeof import("./api")>("./api");
  return { ...actual, getCustomers: vi.fn() };
});

describe("App", () => {
  it("renders the customer dashboard", async () => {
    vi.mocked(getCustomers).mockResolvedValue({ items: [], total: 0, offset: 0, limit: 20 });

    render(<App />);

    await waitFor(() => expect(screen.getByText("Customer risk dashboard")).toBeInTheDocument());
  });
});
