export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

/**
 * Normalized error shape for every API failure — network failures (no
 * response at all) and non-2xx HTTP responses alike — so calling views can
 * catch one error type regardless of what went wrong.
 */
export class ApiError extends Error {
  /** HTTP status code, or null when the request never reached the server. */
  readonly status: number | null;
  /** Human-readable detail extracted from the response body, when available. */
  readonly detail: string;

  constructor(message: string, status: number | null, detail: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

interface FastApiValidationError {
  msg?: string;
  loc?: (string | number)[];
}

function extractDetail(body: unknown): string | null {
  if (body === null || typeof body !== "object" || !("detail" in body)) {
    return null;
  }

  const detail = (body as { detail: unknown }).detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((err: FastApiValidationError) => {
        const field = err.loc?.at(-1);
        return field ? `${field}: ${err.msg ?? "invalid"}` : (err.msg ?? "invalid");
      })
      .join("; ");
  }

  return null;
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(
      "Unable to reach the server. Check your connection and try again.",
      null,
      "Network error",
    );
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    const detail = (extractDetail(body) ?? response.statusText) || "Request failed";
    throw new ApiError(detail, response.status, detail);
  }

  return body as T;
}
