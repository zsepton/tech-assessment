import { Skeleton } from "./Skeleton";
import "./DashboardTableSkeleton.css";

const SKELETON_ROW_COUNT = 8;

export function DashboardTableSkeleton() {
  return (
    <div className="dashboard-table-skeleton" aria-hidden="true">
      {Array.from({ length: SKELETON_ROW_COUNT }, (_, index) => (
        <div className="dashboard-table-skeleton__row" key={index}>
          <Skeleton width="90px" />
          <Skeleton width="110px" />
          <Skeleton width="45px" />
          <Skeleton width="70px" />
          <Skeleton width="85px" />
          <Skeleton width="100px" />
        </div>
      ))}
    </div>
  );
}
