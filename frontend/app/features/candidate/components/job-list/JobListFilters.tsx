/**
 * @file JobListFilters.tsx
 * @description Sidebar bộ lọc tìm kiếm việc làm (desktop) kết nối với Master Data.
 * @architecture Dumb/Controlled component — toàn bộ trạng thái đẩy lên URL search params.
 */

import { memo } from "react";
import { IconFilter, IconRotate2 } from "@tabler/icons-react";
import { useJobMasterData } from "../../hooks/useJobMasterData";
import { Button } from "~/components/ui/Button";

// TODO(FC-80): Bật lại khi backend triển khai param ExperienceYearsMax trong JobFilterRequest
const EXPERIENCE_FILTER_ENABLED = false;

interface JobListFiltersProps {
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
}

const SALARY_RANGES = [
  { label: "Tất cả mức lương", min: undefined, max: undefined },
  { label: "Dưới 10 triệu", min: undefined, max: 10_000_000 },
  { label: "10 - 20 triệu", min: 10_000_000, max: 20_000_000 },
  { label: "20 - 35 triệu", min: 20_000_000, max: 35_000_000 },
  { label: "Trên 35 triệu", min: 35_000_000, max: undefined },
];

export const JobListFilters = memo(function JobListFilters({
  categoryId,
  employmentTypeId,
  salaryMin,
  salaryMax,
  onFilterChange,
  onClearAll,
  hasActiveFilters,
}: JobListFiltersProps) {
  const { data: masterData, isLoading } = useJobMasterData();

  const isCurrentSalary = (min?: number, max?: number) => {
    return salaryMin === min && salaryMax === max;
  };

  return (
    <aside className="flex min-h-full w-full shrink-0 flex-col gap-6 rounded-default border border-border-subtle bg-surface p-5 shadow-surface overscroll-contain">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2 font-semibold text-navy">
          <IconFilter size={18} stroke={1.8} className="text-gold" />
          <span>Bộ lọc tìm kiếm</span>
        </div>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={onClearAll}
            className="flex items-center gap-1 text-label-sm font-medium text-ink-muted hover:text-navy"
          >
            <IconRotate2 size={14} stroke={1.6} />
            <span>Xóa lọc</span>
          </button>
        )}
      </div>

      {import.meta.env.DEV && masterData?.isDemoFallback && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-2.5 py-1.5 text-[11px] font-medium text-amber-700">
          ⚡ Chế độ demo: Đang dùng bộ lọc mẫu
        </div>
      )}

      {isLoading ? (
        <div className="flex flex-col gap-4 animate-pulse">
          <div className="h-4 w-24 rounded bg-surface-low" />
          <div className="h-20 rounded bg-surface-low" />
          <div className="h-4 w-24 rounded bg-surface-low" />
          <div className="h-20 rounded bg-surface-low" />
        </div>
      ) : (
        <>
          {/* Ngành nghề / Danh mục */}
          <div>
            <h4 className="mb-2.5 text-label font-bold text-navy">
              Ngành nghề
            </h4>
            <div className="flex flex-col gap-1.5 max-h-56 overflow-y-auto pr-1">
              <label className="flex cursor-pointer items-center gap-2.5 rounded px-2 py-1 text-body-sm transition-colors hover:bg-surface-low">
                <input
                  type="radio"
                  name="category"
                  checked={!categoryId}
                  onChange={() => onFilterChange({ categoryId: undefined })}
                  className="accent-[#0B132B]"
                />
                <span className={!categoryId ? "font-semibold text-navy" : "text-ink-variant"}>
                  Tất cả ngành nghề
                </span>
              </label>

              {masterData?.categories.map((cat) => (
                <label
                  key={cat.id}
                  className="flex cursor-pointer items-center gap-2.5 rounded px-2 py-1 text-body-sm transition-colors hover:bg-surface-low"
                >
                  <input
                    type="radio"
                    name="category"
                    checked={categoryId === cat.id}
                    onChange={() => onFilterChange({ categoryId: cat.id })}
                    className="accent-[#0B132B]"
                  />
                  <span className={categoryId === cat.id ? "font-semibold text-navy" : "text-ink-variant"}>
                    {cat.name}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Mức lương */}
          <div className="border-t border-border-subtle pt-4">
            <h4 className="mb-2.5 text-label font-bold text-navy">
              Mức lương
            </h4>
            <div className="flex flex-col gap-1.5">
              {SALARY_RANGES.map((sal, idx) => {
                const active = isCurrentSalary(sal.min, sal.max);
                return (
                  <label
                    key={idx}
                    className="flex cursor-pointer items-center gap-2.5 rounded px-2 py-1 text-body-sm transition-colors hover:bg-surface-low"
                  >
                    <input
                      type="radio"
                      name="salary"
                      checked={active}
                      onChange={() =>
                        onFilterChange({ salaryMin: sal.min, salaryMax: sal.max })
                      }
                      className="accent-[#0B132B]"
                    />
                    <span className={active ? "font-semibold text-navy" : "text-ink-variant"}>
                      {sal.label}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Hình thức làm việc */}
          <div className="border-t border-border-subtle pt-4">
            <h4 className="mb-2.5 text-label font-bold text-navy">
              Hình thức làm việc
            </h4>
            <div className="flex flex-col gap-1.5">
              <label className="flex cursor-pointer items-center gap-2.5 rounded px-2 py-1 text-body-sm transition-colors hover:bg-surface-low">
                <input
                  type="radio"
                  name="employmentType"
                  checked={!employmentTypeId}
                  onChange={() => onFilterChange({ employmentTypeId: undefined })}
                  className="accent-[#0B132B]"
                />
                <span className={!employmentTypeId ? "font-semibold text-navy" : "text-ink-variant"}>
                  Tất cả hình thức
                </span>
              </label>

              {masterData?.employmentTypes.map((type) => (
                <label
                  key={type.id}
                  className="flex cursor-pointer items-center gap-2.5 rounded px-2 py-1 text-body-sm transition-colors hover:bg-surface-low"
                >
                  <input
                    type="radio"
                    name="employmentType"
                    checked={employmentTypeId === type.id}
                    onChange={() => onFilterChange({ employmentTypeId: type.id })}
                    className="accent-[#0B132B]"
                  />
                  <span className={employmentTypeId === type.id ? "font-semibold text-navy" : "text-ink-variant"}>
                    {type.name}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Feature-flagged Experience filter */}
          {EXPERIENCE_FILTER_ENABLED && (
            <div className="border-t border-border-subtle pt-4">
              <h4 className="mb-2.5 text-label font-bold text-navy">
                Kinh nghiệm
              </h4>
              <p className="text-label-sm text-ink-muted">Chờ backend hỗ trợ</p>
            </div>
          )}

          {hasActiveFilters && (
            <div className="border-t border-border-subtle pt-4">
              <Button
                variant="secondary"
                size="sm"
                onClick={onClearAll}
                className="w-full text-label"
              >
                Xóa bộ lọc
              </Button>
            </div>
          )}
        </>
      )}
    </aside>
  );
});
