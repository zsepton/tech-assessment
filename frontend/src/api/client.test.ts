import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiRequest } from "./client";

function mockFetchOnce(response: {
  ok: boolean;
  status: number;
  statusText?: string;
  json: () => unknown;
}) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: response.ok,
      status: response.status,
      statusText: response.statusText ?? "",
      json: () => Promise.resolve(response.json()),
    }),
  );
}

async function captureError(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    return error as ApiError;
  }
  throw new Error("Expected the promise to reject, but it resolved.");
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("returns the parsed body on a successful response", async () => {
    mockFetchOnce({ ok: true, status: 200, json: () => ({ hello: "world" }) });

    const result = await apiRequest<{ hello: string }>("/health");

    expect(result).toEqual({ hello: "world" });
  });

  it("throws ApiError with the string detail on a non-2xx response", async () => {
    mockFetchOnce({
      ok: false,
      status: 404,
      json: () => ({ detail: "Customer 'x' not found." }),
    });

    await expect(apiRequest("/customers/x")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      detail: "Customer 'x' not found.",
    });
  });

  it("flattens a FastAPI validation-error array into one message", async () => {
    mockFetchOnce({
      ok: false,
      status: 422,
      json: () => ({
        detail: [{ loc: ["body", "status"], msg: "field required" }],
      }),
    });

    const error = await captureError(apiRequest("/customers/x/outreach"));

    expect(error).toBeInstanceOf(ApiError);
    expect(error.detail).toBe("status: field required");
  });

  it("falls back to statusText when the error body isn't JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: () => Promise.reject(new Error("not json")),
      }),
    );

    const error = await captureError(apiRequest("/customers"));

    expect(error.status).toBe(500);
    expect(error.detail).toBe("Internal Server Error");
  });

  it("wraps a network failure (fetch itself rejecting) as an ApiError with a null status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const error = await captureError(apiRequest("/customers"));

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBeNull();
  });

  it("falls back to statusText when the body has no detail field", async () => {
    mockFetchOnce({ ok: false, status: 500, statusText: "Server Error", json: () => ({}) });

    const error = await captureError(apiRequest("/customers"));

    expect(error.detail).toBe("Server Error");
  });

  it("falls back to statusText when the body isn't an object", async () => {
    mockFetchOnce({ ok: false, status: 500, statusText: "Server Error", json: () => "oops" });

    const error = await captureError(apiRequest("/customers"));

    expect(error.detail).toBe("Server Error");
  });

  it("falls back to statusText when detail is neither a string nor an array", async () => {
    mockFetchOnce({
      ok: false,
      status: 500,
      statusText: "Server Error",
      json: () => ({ detail: 42 }),
    });

    const error = await captureError(apiRequest("/customers"));

    expect(error.detail).toBe("Server Error");
  });

  it("falls back to a generic message when there's no detail and no statusText", async () => {
    mockFetchOnce({ ok: false, status: 500, statusText: "", json: () => ({}) });

    const error = await captureError(apiRequest("/customers"));

    expect(error.detail).toBe("Request failed");
  });

  it("uses the message as-is when a validation error has no loc", async () => {
    mockFetchOnce({
      ok: false,
      status: 422,
      json: () => ({ detail: [{ msg: "field required" }] }),
    });

    const error = await captureError(apiRequest("/customers"));

    expect(error.detail).toBe("field required");
  });

  it("falls back to 'invalid' when a validation error has neither loc nor msg", async () => {
    mockFetchOnce({
      ok: false,
      status: 422,
      json: () => ({ detail: [{}] }),
    });

    const error = await captureError(apiRequest("/customers"));

    expect(error.detail).toBe("invalid");
  });

  it("falls back to 'invalid' within a located error when msg is missing", async () => {
    mockFetchOnce({
      ok: false,
      status: 422,
      json: () => ({ detail: [{ loc: ["body", "status"] }] }),
    });

    const error = await captureError(apiRequest("/customers"));

    expect(error.detail).toBe("status: invalid");
  });
});

describe("API_BASE_URL", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("uses VITE_API_BASE_URL when it's set", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://example.test");
    vi.resetModules();

    const mod = await import("./client");

    expect(mod.API_BASE_URL).toBe("http://example.test");
  });

  it("falls back to the default when VITE_API_BASE_URL is unset", async () => {
    const env = import.meta.env as Record<string, string | undefined>;
    const original = env.VITE_API_BASE_URL;
    delete env.VITE_API_BASE_URL;
    vi.resetModules();

    try {
      const mod = await import("./client");
      expect(mod.API_BASE_URL).toBe("http://localhost:8000");
    } finally {
      env.VITE_API_BASE_URL = original;
    }
  });
});
