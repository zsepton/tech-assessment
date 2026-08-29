import type { OutreachStatus } from "../api";
import { OUTREACH_STATUS_LABEL } from "./outreachLabels";
import "./OutreachBadge.css";

interface OutreachBadgeProps {
  status: OutreachStatus;
}

const STATUS_CLASS: Record<OutreachStatus, string> = {
  NOT_CONTACTED: "outreach-badge--neutral",
  IN_PROGRESS: "outreach-badge--progress",
  RESOLVED: "outreach-badge--resolved",
};

export function OutreachBadge({ status }: OutreachBadgeProps) {
  return (
    <span className={`outreach-badge ${STATUS_CLASS[status]}`}>
      <span className="outreach-badge__dot" />
      {OUTREACH_STATUS_LABEL[status]}
    </span>
  );
}
