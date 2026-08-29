import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Pagination } from "./Pagination";

describe("Pagination", () => {
  it("renders the showing summary", () => {
    render(<Pagination offset={20} limit={20} total={100} onPrev={vi.fn()} onNext={vi.fn()} />);

    expect(screen.getByText("Showing 21–40 of 100 customers")).toBeInTheDocument();
  });

  it("shows 0-0 when there are no results", () => {
    render(<Pagination offset={0} limit={20} total={0} onPrev={vi.fn()} onNext={vi.fn()} />);

    expect(screen.getByText("Showing 0–0 of 0 customers")).toBeInTheDocument();
  });

  it("disables Prev on the first page and enables Next when more remain", () => {
    render(<Pagination offset={0} limit={20} total={100} onPrev={vi.fn()} onNext={vi.fn()} />);

    expect(screen.getByText("‹ Prev")).toBeDisabled();
    expect(screen.getByText("Next ›")).toBeEnabled();
  });

  it("disables Next on the last page and enables Prev", () => {
    render(<Pagination offset={80} limit={20} total={100} onPrev={vi.fn()} onNext={vi.fn()} />);

    expect(screen.getByText("‹ Prev")).toBeEnabled();
    expect(screen.getByText("Next ›")).toBeDisabled();
  });

  it("calls onPrev and onNext when clicked", async () => {
    const onPrev = vi.fn();
    const onNext = vi.fn();
    const user = userEvent.setup();
    render(<Pagination offset={20} limit={20} total={100} onPrev={onPrev} onNext={onNext} />);

    await user.click(screen.getByText("‹ Prev"));
    await user.click(screen.getByText("Next ›"));

    expect(onPrev).toHaveBeenCalledOnce();
    expect(onNext).toHaveBeenCalledOnce();
  });
});
