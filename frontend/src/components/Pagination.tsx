import "./Pagination.css";

interface PaginationProps {
  offset: number;
  limit: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
}

export function Pagination({ offset, limit, total, onPrev, onNext }: PaginationProps) {
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + limit, total);
  const canGoPrev = offset > 0;
  const canGoNext = offset + limit < total;

  return (
    <div className="pagination">
      <span className="pagination__summary">
        Showing {start}–{end} of {total} customers
      </span>
      <div className="pagination__controls">
        <button type="button" onClick={onPrev} disabled={!canGoPrev}>
          ‹ Prev
        </button>
        <button type="button" onClick={onNext} disabled={!canGoNext}>
          Next ›
        </button>
      </div>
    </div>
  );
}
