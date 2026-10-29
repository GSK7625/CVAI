/**
 * @file JobDetailView.tsx
 * @description View chính hiển thị thông tin chi tiết một công việc từ API thật.
 * @architecture Feature UI container kết nối useJobDetail hook và các dumb subcomponents.
 */

import { useState } from "react";
import { Link } from "react-router";
import { IconChevronRight, IconFileText } from "@tabler/icons-react";
import { useJobDetail } from "../../hooks/useJobDetail";
import { useSavedJobIds } from "../../hooks/useSavedJobIds";
import { useToggleSaveJob } from "../../hooks/useToggleSaveJob";
import { useUIStore } from "~/stores/useUIStore";
import { QueryBoundary } from "~/components/shared";
import { EmptyState } from "~/components/ui/EmptyState";
import { Button } from "~/components/ui/Button";
import { JobDetailHeader } from "./JobDetailHeader";
import { JobDetailOverview } from "./JobDetailOverview";
import { JobDetailContent } from "./JobDetailContent";
import { JobDetailCompanyCard } from "./JobDetailCompanyCard";
import { JobDetailSimilarJobs } from "./JobDetailSimilarJobs";

interface JobDetailViewProps {
  jobId: string;
}

export function JobDetailView({ jobId }: JobDetailViewProps) {
  const query = useJobDetail(jobId);
  const showToast = useUIStore((s) => s.showToast);
  const { data: savedJobIds } = useSavedJobIds();
  const { toggleSave } = useToggleSaveJob();

  const isSaved = savedJobIds ? savedJobIds.has(jobId) : false;

  const handleShare = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      showToast("Đã sao chép liên kết việc làm vào bộ nhớ tạm!", "success");
    } else {
      showToast(`Chia sẻ: ${window.location.href}`, "info");
    }
  };

  const handleToggleSave = () => {
    toggleSave(jobId);
  };

  return (
    <div className="container-page mx-auto pb-16 pt-4">
      <QueryBoundary
        isLoading={query.isLoading}
        error={query.error}
        onRetry={query.refetch}
        skeleton={
          <div className="flex flex-col gap-6 animate-pulse">
            <div className="h-6 w-72 rounded bg-surface-low" />
            <div className="h-44 rounded-xl bg-surface-low" />
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              <div className="h-96 rounded-xl bg-surface-low lg:col-span-8" />
              <div className="h-96 rounded-xl bg-surface-low lg:col-span-4" />
            </div>
          </div>
        }
      >
        {query.data ? (
          <div className="flex flex-col gap-6">
            {/* Breadcrumb Navigation */}
            <nav
              className="flex flex-wrap items-center gap-2 text-label-sm text-ink-muted"
              aria-label="Breadcrumb"
            >
              <Link to="/" className="transition-colors hover:text-navy">
                Trang chủ
              </Link>
              <IconChevronRight size={14} className="text-ink-muted" />
              <Link to="/jobs" className="transition-colors hover:text-navy">
                Việc làm
              </Link>
              {query.data.categories?.[0] && (
                <>
                  <IconChevronRight size={14} className="text-ink-muted" />
                  <Link
                    to={`/jobs?q=${encodeURIComponent(query.data.categories[0])}`}
                    className="transition-colors hover:text-navy"
                  >
                    {query.data.categories[0]}
                  </Link>
                </>
              )}
              <IconChevronRight size={14} className="text-ink-muted" />
              <span className="line-clamp-1 font-semibold text-navy">
                {query.data.title}
              </span>
            </nav>

            {/* Header Banner */}
            <JobDetailHeader
              job={query.data}
              saved={isSaved}
              onToggleSave={handleToggleSave}
              onShare={handleShare}
            />

            {/* Content & Sidebar Grid */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              {/* Left Column: Overview + Detailed Description */}
              <div className="flex flex-col gap-6 lg:col-span-8">
                <JobDetailOverview job={query.data} />
                <JobDetailContent job={query.data} />
              </div>

              {/* Right Column: Company Info + Similar Jobs */}
              <aside className="flex flex-col gap-6 lg:col-span-4">
                <JobDetailCompanyCard job={query.data} />
                <JobDetailSimilarJobs
                  jobId={query.data.id}
                  categoryId={query.data.categoryId}
                />
              </aside>
            </div>
          </div>
        ) : (
          <EmptyState
            icon={<IconFileText size={48} stroke={1.2} />}
            title="Không tìm thấy thông tin việc làm"
            description="Công việc này có thể đã hết hạn hoặc tạm dừng nhận hồ sơ ứng tuyển."
            action={
              <Link to="/jobs">
                <Button variant="primary">Xem các việc làm khác</Button>
              </Link>
            }
          />
        )}
      </QueryBoundary>
    </div>
  );
}
