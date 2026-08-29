import type { OutreachStatus } from "./api";

/**
 * Mirrors the backend's outreach state machine (backend/app/services/outreach.py):
 * NOT_CONTACTED -> IN_PROGRESS -> RESOLVED, with RESOLVED terminal.
 *
 * Duplicated here as a small explicit constant rather than fetched from the
 * API — unlike the scoring weights (exposed via /model/info because they're
 * meant to be introspectable/tunable), this 3-state flow is fixed, and the
 * backend is still the authority: it validates every transition server-side
 * regardless of what this list offers, so a client/server drift here would
 * only ever produce an extra rejected request, not an invalid state.
 */
export const OUTREACH_TRANSITIONS: Record<OutreachStatus, OutreachStatus[]> = {
  NOT_CONTACTED: ["IN_PROGRESS"],
  IN_PROGRESS: ["RESOLVED"],
  RESOLVED: [],
};
