/**
 * @file JobSearchHero.tsx
 * @description Hero Banner và thanh tìm kiếm chính cho trang danh sách việc làm (/jobs).
 * @architecture Memoized container tách biệt phần tìm kiếm/hero tĩnh khỏi luồng lọc danh sách việc làm.
 */

import { memo } from "react";
import { Link } from "react-router";
import { JobSearchBar } from "./JobSearchBar";
import type { LookupOption } from "../../types";

interface JobSearchHeroProps {
  keyword: string;
  locationId: string;
  locations: LookupOption[];
  loadingLocations: boolean;
  onSearch: (v: { keyword: string; locationId?: string }) => void;
}

export const JobSearchHero = memo(function JobSearchHero({
  keyword,
  locationId,
  locations,
  loadingLocations,
  onSearch,
}: JobSearchHeroProps) {
  return (
    <>
      {/* Breadcrumbs */}
      <div className="mb-4 flex items-center gap-2 text-label-sm font-medium text-ink-muted">
        <Link to="/" className="hover:text-navy transition-colors">
          Trang chủ
        </Link>
        <span>/</span>
        <span className="text-navy">Việc làm</span>
      </div>

      {/* Search Header Banner */}
      <div className="rounded-2xl bg-navy p-6 text-white shadow-xl md:p-8">
        <h1 className="text-display-sm font-bold md:text-headline-lg">
          Khám phá cơ hội nghề nghiệp
        </h1>
        <p className="mt-2 text-body text-white/75">
          Tìm kiếm công việc lý tưởng theo chuyên môn, mức lương và địa điểm của bạn.
        </p>

        <JobSearchBar
          keyword={keyword}
          locationId={locationId}
          locations={locations}
          loadingLocations={loadingLocations}
          className="mt-6"
          onSubmit={onSearch}
        />
      </div>
    </>
  );
});
