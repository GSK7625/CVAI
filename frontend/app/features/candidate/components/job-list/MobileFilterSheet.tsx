/**
 * @file MobileFilterSheet.tsx
 * @description Drawer/Modal bộ lọc cho màn hình mobile/tablet (< 1024px).
 */

import { useEffect } from "react";
import { IconX, IconFilter, IconRotate2 } from "@tabler/icons-react";
import { Button } from "~/components/ui/Button";
import { JobListFilters } from "./JobListFilters";

interface MobileFilterSheetProps {
  isOpen: boolean;
  onClose: () => void;
  categoryId?: string;
  locationId?: string;
  employmentTypeId?: string;
  salaryMin?: number;
  salaryMax?: number;
  onFilterChange: (updates: {
    categoryId?: string;
    locationId?: string;
    employmentTypeId?: string;
    salaryMin?: number;
    salaryMax?: number;
  }) => void;
  onClearAll: () => void;
  hasActiveFilters: boolean;
  activeCount: number;
}

export function MobileFilterSheet({
  isOpen,
  onClose,
  categoryId,
  locationId,
  employmentTypeId,
  salaryMin,
  salaryMax,
  onFilterChange,
  onClearAll,
  hasActiveFilters,
  activeCount,
}: MobileFilterSheetProps) {
  // Khóa scroll body khi sheet mở
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex lg:hidden" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-navy/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Sheet Container */}
      <div className="relative ml-auto flex h-full w-full max-w-xs flex-col bg-surface shadow-2xl animate-in slide-in-from-right duration-200 sm:max-w-sm">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border-subtle p-4">
          <div className="flex items-center gap-2 font-bold text-navy">
            <IconFilter size={20} stroke={1.8} className="text-gold" />
            <span>Bộ lọc {activeCount > 0 && `(${activeCount})`}</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng bộ lọc"
            className="rounded p-1 text-ink-muted transition-colors hover:bg-surface-low hover:text-navy"
          >
            <IconX size={20} stroke={1.8} />
          </button>
        </div>

        {/* Filters Body */}
        <div className="flex-1 overflow-y-auto p-4">
          <JobListFilters
            categoryId={categoryId}
            locationId={locationId}
            employmentTypeId={employmentTypeId}
            salaryMin={salaryMin}
            salaryMax={salaryMax}
            onFilterChange={onFilterChange}
            onClearAll={onClearAll}
            hasActiveFilters={hasActiveFilters}
          />
        </div>

        {/* Footer Actions */}
        <div className="flex items-center gap-3 border-t border-border-subtle p-4">
          {hasActiveFilters && (
            <Button
              variant="secondary"
              size="md"
              onClick={onClearAll}
              className="flex-1 gap-1"
            >
              <IconRotate2 size={16} stroke={1.6} />
              <span>Xóa tất cả</span>
            </Button>
          )}
          <Button
            variant="accent"
            size="md"
            onClick={onClose}
            className="flex-1 font-semibold"
          >
            Áp dụng
          </Button>
        </div>
      </div>
    </div>
  );
}
