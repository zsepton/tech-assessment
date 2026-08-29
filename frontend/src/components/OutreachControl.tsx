import { useState } from "react";
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

  const nextStatuses = OUTREACH_TRANSITIONS[status];

  async function handleTransition(next: OutreachStatus) {
    setUpdating(true);
    setError(null);

    try {
      const detail = await updateOutreachStatus(customerId, next);
      // Pessimistic update: reflect the status the server actually
      // confirmed, not the one we asked for — on failure, `status` (from
      // props) is untouched, so the badge simply keeps showing the last
      // confirmed server state.
      onUpdated(detail);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Something went wrong.");
    } finally {
      setUpdating(false);
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
