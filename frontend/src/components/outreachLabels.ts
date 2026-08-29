import type { OutreachStatus } from "../api";

export const OUTREACH_STATUS_LABEL: Record<OutreachStatus, string> = {
  NOT_CONTACTED: "Not contacted",
  IN_PROGRESS: "In progress",
  RESOLVED: "Resolved",
};
