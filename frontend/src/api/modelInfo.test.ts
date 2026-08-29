import { afterEach, describe, expect, it, vi } from "vitest";
import { getModelInfo } from "./modelInfo";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("getModelInfo", () => {
  it("requests /model/info and returns the parsed body", async () => {
    const body = { high_risk_threshold: 70 };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(body),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getModelInfo();

    const url = fetchMock.mock.calls[0][0] as string;
    expect(url.endsWith("/model/info")).toBe(true);
    expect(result).toEqual(body);
  });
});
