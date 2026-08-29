import { Skeleton } from "./Skeleton";
import "./DetailSkeleton.css";

export function DetailSkeleton() {
  return (
    <div className="detail-skeleton" aria-hidden="true">
      <div className="detail-skeleton__header">
        <div className="detail-skeleton__header-text">
          <Skeleton width="160px" height="26px" />
          <Skeleton width="260px" height="14px" />
        </div>
        <Skeleton width="120px" height="32px" />
      </div>
      <Skeleton width="100%" height="64px" />
      <div className="detail-skeleton__body">
        <Skeleton width="100%" height="220px" />
        <Skeleton width="100%" height="220px" />
      </div>
    </div>
  );
}
