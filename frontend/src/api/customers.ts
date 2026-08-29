import { apiRequest } from "./client";
import type {
  CustomerDetail,
  CustomerListParams,
  OutreachStatus,
  PaginatedCustomers,
} from "./types";

function buildQueryString(params: CustomerListParams): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      searchParams.set(key, String(value));
    }
  }

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function getCustomers(params: CustomerListParams = {}): Promise<PaginatedCustomers> {
  return apiRequest<PaginatedCustomers>(`/customers${buildQueryString(params)}`);
}

export function getCustomer(customerId: string): Promise<CustomerDetail> {
  return apiRequest<CustomerDetail>(`/customers/${encodeURIComponent(customerId)}`);
}

export function updateOutreachStatus(
  customerId: string,
  status: OutreachStatus,
): Promise<CustomerDetail> {
  return apiRequest<CustomerDetail>(`/customers/${encodeURIComponent(customerId)}/outreach`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
