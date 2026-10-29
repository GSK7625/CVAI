/**
 * @file JobListPagination.tsx
 * @description Thanh phân trang số trang chuẩn REST cho danh sách việc làm.
 * @architecture Dumb component điều khiển bởi props từ URL search params.
 */

import { memo } from "react";
import { IconChevronLeft, IconChevronRight } from "@tabler/icons-react";
import { Button } from "~/components/ui/Button";

interface JobListPaginationProps {
  currentPage: number;
  totalPages: number;
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
}

export const JobListPagination = memo(function JobListPagination({
  currentPage,
  totalPages,
  hasPreviousPage,
  hasNextPage,
  onPageChange,
}: JobListPaginationProps) {
  if (totalPages <= 1) return null;

  // Tính toán mảng các số trang hiển thị (tối đa 5 trang xung quanh currentPage)
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push("...");

      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        if (!pages.includes(i)) pages.push(i);
      }

      if (currentPage < totalPages - 2) pages.push("...");
      if (!pages.includes(totalPages)) pages.push(totalPages);
    }

    return pages;
  };

  return (
    <nav
      className="flex items-center justify-center gap-1.5 pt-6"
      aria-label="Phân trang việc làm"
    >
      <Button
        variant="secondary"
        size="sm"
        disabled={!hasPreviousPage || currentPage <= 1}
        onClick={() => onPageChange(currentPage - 1)}
        className="gap-1 px-3"
        aria-label="Trang trước"
      >
        <IconChevronLeft size={16} stroke={1.8} />
        <span className="hidden sm:inline">Trước</span>
      </Button>

      <div className="flex items-center gap-1">
        {getPageNumbers().map((p, idx) => {
          if (p === "...") {
            return (
              <span
                key={`ellipsis-${idx}`}
                className="px-2 text-ink-muted select-none"
              >
                ...
              </span>
            );
          }

          const pageNum = Number(p);
          const isActive = pageNum === currentPage;

          return (
            <button
              key={pageNum}
              type="button"
              onClick={() => onPageChange(pageNum)}
              aria-current={isActive ? "page" : undefined}
              className={`flex h-9 min-w-[36px] items-center justify-center rounded-default px-2 text-label font-medium transition-colors ${
                isActive
                  ? "bg-navy font-bold text-white shadow-sm"
                  : "border border-border-subtle bg-surface text-ink hover:border-navy hover:text-navy"
              }`}
            >
              {pageNum}
            </button>
          );
        })}
      </div>

      <Button
        variant="secondary"
        size="sm"
        disabled={!hasNextPage || currentPage >= totalPages}
        onClick={() => onPageChange(currentPage + 1)}
        className="gap-1 px-3"
        aria-label="Trang sau"
      >
        <span className="hidden sm:inline">Sau</span>
        <IconChevronRight size={16} stroke={1.8} />
      </Button>
    </nav>
  );
});
