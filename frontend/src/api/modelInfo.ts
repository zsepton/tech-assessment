import { apiRequest } from "./client";
import type { ModelInfo } from "./types";

export function getModelInfo(): Promise<ModelInfo> {
  return apiRequest<ModelInfo>("/model/info");
}
