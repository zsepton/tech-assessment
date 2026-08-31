import { useEffect, useRef, useState } from "react";
import { ApiError, updateOutreachStatus } from "../api";
import type { CustomerDetail, OutreachStatus } from "../api";
import { OUTREACH_TRANSITIONS } from "../outreachTransitions";
import { OutreachBadge } from "./OutreachBadge";
import { OUTREACH_STATUS_LABEL } from "./outreachLabels";
import "./OutreachControl.css";

interface OutreachControlProps {
  customerId: string;
  status: OutreachStatus;
  onUpdated: (detail: CustomerDetail) => void;
}

export function OutreachControl({ customerId, status, onUpdated }: OutreachControlProps) {
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Unlike the effect-scoped `cancelled` flags in DashboardView/
  // CustomerDetailView, this guard spans the component's whole lifetime
  // (not one fetch), since a click can be followed by an unmount at any
  // point before the PATCH resolves. The ref is reset to `true` at the top
  // of the effect body, not just via `useRef(true)`'s initial value: React
  // 18 StrictMode mounts, cleans up, and re-mounts every component once in
  // development, and without this reset the cleanup's `= false` would never
  // be undone, permanently disabling every future update for the rest of
  // the component's real lifetime (this was a live, reproduced bug: the
  // PATCH request succeeded, but the button stayed stuck on "Updating…"
  // forever because `onUpdated`/`setUpdating(false)` were both silently
  // skipped every time afterward).
  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const nextStatuses = OUTREACH_TRANSITIONS[status];

  async function handleTransition(next: OutreachStatus) {
    setUpdating(true);
    setError(null);

    try {
      const detail = await updateOutreachStatus(customerId, next);
      if (mountedRef.current) {
        // Pessimistic update: reflect the status the server actually
        // confirmed, not the one we asked for — on failure, `status` (from
        // props) is untouched, so the badge simply keeps showing the last
        // confirmed server state.
        onUpdated(detail);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof ApiError ? err.detail : "Something went wrong.");
      }
    } finally {
      if (mountedRef.current) {
        setUpdating(false);
      }
    }
  }

  return (
    <div className="outreach-control">
      <OutreachBadge status={status} />

      {nextStatuses.length === 0 ? (
        <span className="outreach-control__terminal">No further action</span>
      ) : (
        nextStatuses.map((next) => (
          <button
            key={next}
            type="button"
            className="outreach-control__button"
            disabled={updating}
            onClick={() => void handleTransition(next)}
          >
            {updating ? "Updating…" : `Mark as ${OUTREACH_STATUS_LABEL[next]} →`}
          </button>
        ))
      )}

      {error && <span className="outreach-control__error">{error}</span>}
    </div>
  );
}
