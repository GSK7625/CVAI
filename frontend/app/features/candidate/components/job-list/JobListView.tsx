/**
 * @file JobListView.tsx
 * @description Giao diện chính danh sách việc làm ứng viên (Search, Filters, Job cards, Pagination).
 * @architecture Feature UI container kết nối URL params với Custom Hooks và dumb components.
 * Tối ưu hóa Fine-grained Render Isolation: cô lập Hero/Search bar và header khỏi filter changes.
 */

import { useState, useMemo, useCallback } from "react";
import { useSearchParams } from "react-router";
import {
  IconFilter,
  IconFileText,
  IconSortDescending,
} from "@tabler/icons-react";
import { useJobList } from "../../hooks/useJobList";
import { QueryBoundary, SkeletonCard } from "~/components/shared";
import { EmptyState } from "~/components/ui/EmptyState";
import { Button } from "~/components/ui/Button";
import { JobListFilters } from "./JobListFilters";
import { JobListItemRow } from "./JobListItemRow";
import { JobListPagination } from "./JobListPagination";
import { MobileFilterSheet } from "./MobileFilterSheet";
import { JobSearchHero } from "./JobSearchHero";
import { useJobMasterData } from "../../hooks/useJobMasterData";
import type { LookupOption } from "../../types";

const EMPTY_LOCATIONS: LookupOption[] = [];

// Resolve một master-data option từ id trực tiếp HOẶC text (label từ link trang chủ)
function resolveOptionId(
  opts: { id: string; name: string }[] | undefined,
  directId: string | undefined,
  text: string | undefined,
): string | undefined {
  if (directId) return directId;
  if (!text || !opts) return undefined;
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "");
  const nt = norm(text);
  return opts.find((o) => {
    const on = norm(o.name);
    return on === nt || on.includes(nt) || nt.includes(on);
  })?.id;
}

export function JobListView() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);
  const { data: masterData, isLoading: loadingMasterData } = useJobMasterData();

  // Đọc filters từ URL search params (Single Source of Truth)
  const urlKeyword = searchParams.get("q") ?? "";
  const rawCategoryId = searchParams.get("categoryId") || undefined;
  const urlCategoryText = searchParams.get("category") || undefined;
  const rawLocationId = searchParams.get("locationId") || undefined;
  const urlLocationText = searchParams.get("location") || undefined;
  const employmentTypeId = searchParams.get("employmentTypeId") || undefined;
  const salaryMinStr = searchParams.get("salaryMin");
  const salaryMaxStr = searchParams.get("salaryMax");
  const sortBy = searchParams.get("sortBy") ?? "newest";
  const page = Math.max(1, parseInt(searchParams.get("page") ?? "1", 10) || 1);

  const categoryId = useMemo(
    () => resolveOptionId(masterData?.categories, rawCategoryId, urlCategoryText),
    [rawCategoryId, urlCategoryText, masterData?.categories],
  );

  const locationId = useMemo(
    () => resolveOptionId(masterData?.locations, rawLocationId, urlLocationText),
    [rawLocationId, urlLocationText, masterData?.locations],
  );

  const salaryMin = salaryMinStr ? parseInt(salaryMinStr, 10) : undefined;
  const salaryMax = salaryMaxStr ? parseInt(salaryMaxStr, 10) : undefined;

  // Chuẩn bị filter object gửi tới useJobList hook
  const filters = useMemo(
    () => ({
      keyword: urlKeyword || undefined,
      categoryId,
      locationId,
      employmentTypeId,
      salaryMin,
      salaryMax,
      sortBy,
      page,
      pageSize: 10,
    }),
    [urlKeyword, categoryId, locationId, employmentTypeId, salaryMin, salaryMax, sortBy, page],
  );

  const query = useJobList(filters);

  // Đếm số lượng bộ lọc đang active (ngoại trừ q và page)
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (categoryId) count++;
    if (locationId) count++;
    if (employmentTypeId) count++;
    if (salaryMin != null || salaryMax != null) count++;
    return count;
  }, [categoryId, locationId, employmentTypeId, salaryMin, salaryMax]);

  const hasActiveFilters = activeFilterCount > 0 || Boolean(urlKeyword);

  // Hàm submit tìm kiếm từ JobSearchBar (memoized, functional updater)
  const handleSearchSubmit = useCallback(
    (v: { keyword: string; locationId?: string }) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (v.keyword) next.set("q", v.keyword);
          else next.delete("q");

          if (v.locationId) next.set("locationId", v.locationId);
          else next.delete("locationId");
          next.delete("location"); // Xóa text param cũ nếu có

          next.delete("page");
          return next;
        },
        { replace: true, preventScrollReset: true },
      );
    },
    [setSearchParams],
  );

  // Hàm cập nhật filter lên URL (memoized, functional updater, không reload scroll)
  const handleFilterChange = useCallback(
    (updates: {
      categoryId?: string;
      locationId?: string;
      employmentTypeId?: string;
      salaryMin?: number;
      salaryMax?: number;
    }) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);

          if ("categoryId" in updates) {
            if (updates.categoryId) next.set("categoryId", updates.categoryId);
            else next.delete("categoryId");
          }
          if ("locationId" in updates) {
            if (updates.locationId) next.set("locationId", updates.locationId);
            else next.delete("locationId");
          }
          if ("employmentTypeId" in updates) {
            if (updates.employmentTypeId) next.set("employmentTypeId", updates.employmentTypeId);
            else next.delete("employmentTypeId");
          }
          if ("salaryMin" in updates) {
            if (updates.salaryMin != null) next.set("salaryMin", String(updates.salaryMin));
            else next.delete("salaryMin");
          }
          if ("salaryMax" in updates) {
            if (updates.salaryMax != null) next.set("salaryMax", String(updates.salaryMax));
            else next.delete("salaryMax");
          }

          next.delete("page"); // Reset về trang 1
          return next;
        },
        { replace: true, preventScrollReset: true },
      );
    },
    [setSearchParams],
  );

  const handleClearAll = useCallback(() => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams();
        const currentSort = prev.get("sortBy");
        if (currentSort && currentSort !== "newest") next.set("sortBy", currentSort);
        return next;
      },
      { replace: true, preventScrollReset: true },
    );
  }, [setSearchParams]);

  const handleSortChange = useCallback(
    (newSort: string) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (newSort === "newest") next.delete("sortBy");
          else next.set("sortBy", newSort);
          next.delete("page");
          return next;
        },
        { replace: true, preventScrollReset: true },
      );
    },
    [setSearchParams],
  );

  const handlePageChange = useCallback(
    (newPage: number) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (newPage <= 1) next.delete("page");
          else next.set("page", String(newPage));
          return next;
        },
        { replace: true },
      );
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    [setSearchParams],
  );

  return (
    <div className="container-page mx-auto py-8">
      {/* Search Header Hero (Memoized: giữ nguyên 100% khi lọc danh mục/lương) */}
      <JobSearchHero
        keyword={urlKeyword}
        locationId={rawLocationId || locationId || ""}
        locations={masterData?.locations ?? EMPTY_LOCATIONS}
        loadingLocations={loadingMasterData}
        onSearch={handleSearchSubmit}
      />

      {/* Control Bar (Total Count, Mobile Filter Button, Sort Dropdown) */}
      <div className="mt-8 flex flex-col justify-between gap-4 border-b border-border-subtle pb-4 sm:flex-row sm:items-center">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-headline-md font-bold text-navy">
            {query.data ? `${query.data.total} việc làm phù hợp` : "Đang tìm kiếm việc làm..."}
          </span>
          {urlKeyword && (
            <span className="text-body-sm text-ink-muted">
              với từ khóa &ldquo;<strong className="text-navy">{urlKeyword}</strong>&rdquo;
            </span>
          )}
          {query.isFetching && !query.isLoading && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-low px-2.5 py-0.5 text-label-sm text-ink-muted animate-pulse">
              <span className="h-1.5 w-1.5 rounded-full bg-gold" />
              Đang cập nhật...
            </span>
          )}
          {import.meta.env.DEV && query.data?.isDemoFallback && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-label-sm font-semibold text-amber-700">
              <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
              Chế độ Demo (Backend offline)
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Mobile Filter Toggle Button */}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setMobileFilterOpen(true)}
            className="flex items-center gap-2 lg:hidden"
          >
            <IconFilter size={16} stroke={1.8} />
            <span>Bộ lọc {activeFilterCount > 0 && `(${activeFilterCount})`}</span>
          </Button>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2 text-body-sm">
            <IconSortDescending size={18} stroke={1.6} className="text-ink-muted" />
            <label htmlFor="sort-select" className="hidden sm:inline text-ink-variant">
              Sắp xếp:
            </label>
            <select
              id="sort-select"
              value={sortBy}
              onChange={(e) => handleSortChange(e.target.value)}
              className="h-9 rounded-default border border-border-strong bg-surface px-3 py-1 text-label text-ink outline-none transition-colors hover:border-navy focus:border-navy"
            >
              <option value="newest">Mới nhất</option>
              <option value="salary_desc">Lương cao nhất</option>
              <option value="deadline">Hạn nộp gần nhất</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Layout: Filters Sidebar + Job Rows */}
      <div className="mt-6 flex flex-col gap-6 lg:flex-row lg:h-[950px]">
        {/* Desktop Sidebar */}
        <div className="hidden lg:block lg:w-72 lg:shrink-0 lg:h-full lg:overflow-y-auto lg:pr-2 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-navy/20 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-navy/30">
          <JobListFilters
            categoryId={categoryId}
            locationId={locationId}
            employmentTypeId={employmentTypeId}
            salaryMin={salaryMin}
            salaryMax={salaryMax}
            onFilterChange={handleFilterChange}
            onClearAll={handleClearAll}
            hasActiveFilters={hasActiveFilters}
          />
        </div>

        {/* Mobile Sheet */}
        <MobileFilterSheet
          isOpen={mobileFilterOpen}
          onClose={() => setMobileFilterOpen(false)}
          categoryId={categoryId}
          locationId={locationId}
          employmentTypeId={employmentTypeId}
          salaryMin={salaryMin}
          salaryMax={salaryMax}
          onFilterChange={handleFilterChange}
          onClearAll={handleClearAll}
          hasActiveFilters={hasActiveFilters}
          activeCount={activeFilterCount}
        />

        {/* Job Cards List (Chỉ vùng này re-render và hiển thị dữ liệu mới) */}
        <div
          className={`flex min-w-0 flex-1 flex-col gap-4 min-h-[480px] lg:h-full lg:overflow-y-auto lg:pr-2 transition-opacity duration-200 ${
            query.isFetching && !query.isLoading ? "opacity-60 pointer-events-none" : "opacity-100"
          } [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-navy/20 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-navy/30`}
          aria-label="Danh sách việc làm"
        >
          <QueryBoundary
            isLoading={query.isLoading}
            error={query.error}
            onRetry={query.refetch}
            skeleton={
              <div className="flex flex-col gap-4">
                <SkeletonCard lines={2} />
                <SkeletonCard lines={2} />
                <SkeletonCard lines={2} />
              </div>
            }
          >
            {query.data && query.data.items.length > 0 ? (
              <div className="flex flex-col gap-4">
                {query.data.items.map((job) => (
                  <JobListItemRow key={job.id} job={job} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<IconFileText size={48} stroke={1.2} />}
                title="Không tìm thấy việc làm phù hợp"
                description="Thử điều chỉnh từ khóa tìm kiếm hoặc xóa bớt các bộ lọc để tiếp tục xem việc làm."
                action={
                  hasActiveFilters ? (
                    <Button variant="primary" onClick={handleClearAll}>
                      Xóa bộ lọc
                    </Button>
                  ) : undefined
                }
              />
            )}
          </QueryBoundary>
        </div>
      </div>

      {/* Pagination moved outside of scrolling area */}
      {query.data && query.data.items.length > 0 && (
        <div className="mt-6">
          <JobListPagination
            currentPage={query.data.page}
            totalPages={query.data.totalPages}
            hasPreviousPage={query.data.hasPreviousPage}
            hasNextPage={query.data.hasNextPage}
            onPageChange={handlePageChange}
          />
        </div>
      )}
    </div>
  );
}
