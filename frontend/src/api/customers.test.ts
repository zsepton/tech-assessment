import { afterEach, describe, expect, it, vi } from "vitest";
import { getCustomer, getCustomers, updateOutreachStatus } from "./customers";

function mockFetchJson(body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("getCustomers", () => {
  it("requests /customers with no query string when no params are given", async () => {
    const fetchMock = mockFetchJson({ items: [], total: 0, offset: 0, limit: 20 });

    await getCustomers();

    const url = fetchMock.mock.calls[0][0] as string;
    expect(url.endsWith("/customers")).toBe(true);
  });

  it("builds a query string from the provided params, omitting undefined ones", async () => {
    const fetchMock = mockFetchJson({ items: [], total: 0, offset: 5, limit: 10 });

    await getCustomers({ offset: 5, limit: 10, risk_tier: "High", contract: undefined });

    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("offset=5");
    expect(url).toContain("limit=10");
    expect(url).toContain("risk_tier=High");
    expect(url).not.toContain("contract");
  });
});

describe("getCustomer", () => {
  it("requests /customers/{id} with the id url-encoded", async () => {
    const fetchMock = mockFetchJson({ customer: {}, risk: {} });

    await getCustomer("abc/123");

    const url = fetchMock.mock.calls[0][0] as string;
    expect(url.endsWith("/customers/abc%2F123")).toBe(true);
  });
});

describe("updateOutreachStatus", () => {
  it("sends a PATCH with the status in the body", async () => {
    const fetchMock = mockFetchJson({ customer: {}, risk: {} });

    await updateOutreachStatus("7590-VHVEG", "IN_PROGRESS");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url.endsWith("/customers/7590-VHVEG/outreach")).toBe(true);
    expect(init.method).toBe("PATCH");
    expect(init.body).toBe(JSON.stringify({ status: "IN_PROGRESS" }));
  });
});
