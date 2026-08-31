import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ApiError } from "../api";
import { useAsync } from "./useAsync";

describe("useAsync", () => {
  it("starts loading and resolves with the fetched data", async () => {
    const fetcher = vi.fn().mockResolvedValue("result");
    const { result } = renderHook(() => useAsync(fetcher, null, []));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBe("result");
    expect(result.current.error).toBeNull();
  });

  it("exposes an ApiError's detail as the error message", async () => {
    const fetcher = vi.fn().mockRejectedValue(new ApiError("boom", 400, "Bad request"));
    const { result } = renderHook(() => useAsync(fetcher, null, []));

    await waitFor(() => expect(result.current.error).toBe("Bad request"));
    expect(result.current.loading).toBe(false);
  });

  it("falls back to a generic message for a non-ApiError failure", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("network down"));
    const { result } = renderHook(() => useAsync(fetcher, null, []));

    await waitFor(() => expect(result.current.error).toBe("Something went wrong."));
  });

  it("re-fetches and resets loading when deps change", async () => {
    const fetcher = vi.fn().mockResolvedValueOnce("first").mockResolvedValueOnce("second");
    const { result, rerender } = renderHook(({ dep }) => useAsync(fetcher, null, [dep]), {
      initialProps: { dep: 1 },
    });

    await waitFor(() => expect(result.current.data).toBe("first"));

    rerender({ dep: 2 });

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.data).toBe("second"));
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("does not re-fetch when deps are equal by value across a rerender", async () => {
    const fetcher = vi.fn().mockResolvedValue("only-fetch");
    const { result, rerender } = renderHook(({ dep }) => useAsync(fetcher, null, [dep]), {
      initialProps: { dep: 1 },
    });

    await waitFor(() => expect(result.current.data).toBe("only-fetch"));

    rerender({ dep: 1 });

    expect(result.current.loading).toBe(false);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("clears a stale error as soon as a retry starts", async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValueOnce(new ApiError("boom", 500, "Server error"))
      .mockResolvedValueOnce("recovered");
    const { result, rerender } = renderHook(({ dep }) => useAsync(fetcher, null, [dep]), {
      initialProps: { dep: 1 },
    });

    await waitFor(() => expect(result.current.error).toBe("Server error"));

    rerender({ dep: 2 });

    // The retry starts in the same render as the deps change, before its
    // own promise has settled, so the stale error must already be gone
    // rather than lingering next to the loading skeleton.
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(true);

    await waitFor(() => expect(result.current.data).toBe("recovered"));
  });

  it("does not update state after a stale request resolves post-unmount", async () => {
    let resolveStale!: (value: string) => void;
    const stalePromise = new Promise<string>((resolve) => {
      resolveStale = resolve;
    });
    const fetcher = vi.fn().mockReturnValue(stalePromise);
    const { unmount } = renderHook(() => useAsync(fetcher, null, []));

    unmount();
    resolveStale("late");

    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
  });

  it("allows setData to apply an update outside the fetch lifecycle", async () => {
    const fetcher = vi.fn().mockResolvedValue("initial");
    const { result } = renderHook(() => useAsync(fetcher, null, []));

    await waitFor(() => expect(result.current.data).toBe("initial"));

    act(() => {
      result.current.setData("overridden");
    });

    expect(result.current.data).toBe("overridden");
  });
});
