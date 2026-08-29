import type { OutreachStatus } from "../api";
import "./OutreachBadge.css";

interface OutreachBadgeProps {
  status: OutreachStatus;
}

const LABEL: Record<OutreachStatus, string> = {
  NOT_CONTACTED: "Not contacted",
  IN_PROGRESS: "In progress",
  RESOLVED: "Resolved",
};

const STATUS_CLASS: Record<OutreachStatus, string> = {
  NOT_CONTACTED: "outreach-badge--neutral",
  IN_PROGRESS: "outreach-badge--progress",
  RESOLVED: "outreach-badge--resolved",
};

export function OutreachBadge({ status }: OutreachBadgeProps) {
  return (
    <span className={`outreach-badge ${STATUS_CLASS[status]}`}>
      <span className="outreach-badge__dot" />
      {LABEL[status]}
    </span>
  );
}
