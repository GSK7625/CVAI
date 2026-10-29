/**
 * @file SavedJobsView.tsx
 * @description Giao diện danh sách việc làm đã lưu của ứng viên (P3-UC04).
 * @architecture Dùng QueryBoundary, reuse JobListPagination, Modal xác nhận bỏ lưu, EmptyState.
 */

import { useState } from "react";
import { Link, useSearchParams } from "react-router";
import {
  IconBookmarkFilled,
  IconBookmarkOff,
  IconCalendar,
  IconClock,
  IconMapPin,
  IconSearch,
} from "@tabler/icons-react";
import { Badge } from "~/components/ui/Badge";
import { Button } from "~/components/ui/Button";
import { EmptyState } from "~/components/ui/EmptyState";
import { Modal } from "~/components/ui/Modal";
import { Skeleton } from "~/components/ui/Skeleton";
import { QueryBoundary } from "~/components/shared/QueryBoundary";
import { JobListPagination } from "../job-list/JobListPagination";
import { useSavedJobs } from "../../hooks/useSavedJobs";
import { useToggleSaveJob } from "../../hooks/useToggleSaveJob";
import { formatSalary, timeAgo } from "~/utils";
import type { SavedJob } from "../../types";

/**
 * Chuyển đổi mốc thời gian lưu thành chuỗi tương đối thân thiện (ví dụ: "2 ngày trước", "Vừa xong").
 * @param savedAt Chuỗi thời gian ISO khi ứng viên lưu việc làm
 */
function formatSavedTime(savedAt: string): string {
  const relative = timeAgo(savedAt);
  return relative.replace("Đăng ", "").replace("Vừa đăng", "Vừa xong");
}

/**
 * Skeleton tải dữ liệu giả lập layout các card việc làm đã lưu.
 */
function SavedJobsSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="p-1 rounded-[2rem] bg-navy/5 border border-navy/10"
        >
          <div className="p-6 bg-white rounded-[calc(2rem-0.25rem)] flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <Skeleton className="w-14 h-14 rounded-2xl shrink-0" />
              <div className="space-y-2.5">
                <Skeleton className="h-6 w-56 rounded-md" />
                <Skeleton className="h-4 w-40 rounded-md" />
                <Skeleton className="h-4 w-64 rounded-md" />
              </div>
            </div>
            <div className="flex items-center gap-2 self-end md:self-center">
              <Skeleton className="h-9 w-24 rounded-full" />
              <Skeleton className="h-9 w-28 rounded-full" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Giao diện chính hiển thị danh sách các công việc ứng viên đã lưu.
 * Cho phép phân trang số trang, điều hướng xem chi tiết, và bỏ lưu có hộp thoại xác nhận.
 */
export function SavedJobsView() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Math.max(1, Number(searchParams.get("page") || "1"));

  // Lấy danh sách việc làm đã lưu từ backend
  const { data, isLoading, error, refetch } = useSavedJobs(page);
  // Mutation chuyển đổi trạng thái lưu
  const { toggleSave, isPending } = useToggleSaveJob();
  // State lưu trữ công việc đang được chọn để xác nhận bỏ lưu
  const [jobToUnsave, setJobToUnsave] = useState<SavedJob | null>(null);

  /**
   * Cập nhật số trang lên search params trên URL.
   */
  const handlePageChange = (newPage: number) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (newPage <= 1) {
        next.delete("page");
      } else {
        next.set("page", String(newPage));
      }
      return next;
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  /**
   * Xác nhận hủy lưu công việc và đóng hộp thoại modal.
   */
  const handleConfirmUnsave = () => {
    if (!jobToUnsave) return;
    toggleSave(jobToUnsave.jobId, {
      onSuccess: () => {
        setJobToUnsave(null);
      },
    });
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header section with Double-bezel accent */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 border-b border-navy/10 pb-6">
        <div className="space-y-1.5">
          <nav className="flex items-center gap-2 text-xs text-ink-muted mb-1.5">
            <Link to="/" className="hover:text-navy transition-colors">
              Trang chủ
            </Link>
            <span>/</span>
            <span className="font-semibold text-navy">Việc làm đã lưu</span>
          </nav>
          <h1 className="text-2xl sm:text-3xl font-bold text-navy">
            Việc làm đã lưu {data?.total != null ? `(${data.total})` : ""}
          </h1>
          <p className="mt-1 text-sm text-ink-variant">
            Quản lý danh sách các cơ hội nghề nghiệp bạn đã lưu để ứng tuyển.
          </p>
        </div>
        <Link
          to="/jobs"
          className="self-start sm:self-center inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-navy/20 bg-surface-low text-xs font-semibold text-navy hover:bg-navy/5 transition-all active:scale-[0.98]"
        >
          <IconSearch size={15} />
          <span>Tìm thêm việc làm</span>
        </Link>
      </div>

      {/* Main Content with QueryBoundary */}
      <QueryBoundary
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        skeleton={<SavedJobsSkeleton />}
      >
        {data && data.items.length === 0 ? (
          <EmptyState
            icon={<IconBookmarkOff size={48} className="text-ink-muted" stroke={1.5} />}
            title="Chưa có việc làm nào được lưu"
            description="Bạn chưa lưu việc làm nào. Hãy khám phá các tin tuyển dụng hấp dẫn và nhấn Lưu để xem lại tại đây!"
            action={
              <Link to="/jobs">
                <Button variant="primary">
                  <IconSearch size={18} />
                  Tìm việc làm
                </Button>
              </Link>
            }
            className="my-10"
          />
        ) : (
          <div className="space-y-4">
            {data?.items.map((job) => {
              const companyInitial = job.company ? job.company.charAt(0).toUpperCase() : "C";

              return (
                <article
                  key={job.jobId}
                  className="group p-1 rounded-[2rem] bg-navy/5 border border-navy/10 hover:border-navy/20 hover:shadow-md transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
                >
                  <div className="p-5 sm:p-6 bg-white rounded-[calc(2rem-0.25rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.8)] flex flex-col md:flex-row md:items-center justify-between gap-5">
                    {/* Main Info */}
                    <div className="flex items-start gap-4 min-w-0 flex-1">
                      {/* Company Logo */}
                      <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl border border-navy/10 bg-navy/5">
                        {job.companyLogo ? (
                          <img
                            src={job.companyLogo}
                            alt={job.company}
                            className="h-full w-full object-cover shadow-2xs"
                            loading="lazy"
                          />
                        ) : (
                          <span className="text-lg font-bold text-navy">
                            {companyInitial}
                          </span>
                        )}
                      </div>

                      <div className="min-w-0 space-y-1">
                        <div className="flex items-center gap-2.5 flex-wrap">
                          <Link
                            to={`/jobs/${job.jobId}`}
                            className="text-base sm:text-lg font-bold text-navy hover:text-navy-secondary transition-colors truncate"
                          >
                            {job.title}
                          </Link>
                          {job.isExpired ? (
                            <Badge variant="danger">Hết hạn</Badge>
                          ) : !job.isActive ? (
                            <Badge variant="neutral">Đã đóng</Badge>
                          ) : null}
                        </div>

                        <p className="text-xs sm:text-sm text-ink-variant font-medium flex items-center gap-2 truncate">
                          <span>{job.company}</span>
                          <span className="text-ink-muted">•</span>
                          <span className="inline-flex items-center gap-1 text-ink-muted">
                            <IconMapPin size={14} />
                            {job.location}
                          </span>
                        </p>

                        <div className="flex items-center gap-3 pt-1 text-xs text-ink-muted flex-wrap">
                          <span className="font-semibold text-navy">
                            {formatSalary(job.salaryMin, job.salaryMax)}
                          </span>
                          <span>•</span>
                          {job.deadline && (
                            <>
                              <span className="inline-flex items-center gap-1">
                                <IconCalendar size={13} />
                                Hạn nộp: {job.deadline}
                              </span>
                              <span>•</span>
                            </>
                          )}
                          <span className="inline-flex items-center gap-1">
                            <IconClock size={13} />
                            Lưu: {formatSavedTime(job.savedAt)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2.5 shrink-0 self-end md:self-center">
                      <button
                        type="button"
                        onClick={() => setJobToUnsave(job)}
                        className="px-4 py-2 rounded-full border border-rose-200 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors inline-flex items-center gap-1.5"
                      >
                        Bỏ lưu
                      </button>

                      <Link
                        to={`/jobs/${job.jobId}`}
                        className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-navy text-xs font-semibold text-white shadow-xs hover:bg-navy-secondary active:scale-[0.98] transition-all"
                      >
                        Ứng tuyển
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}

            {/* Pagination */}
            {data && data.totalPages > 1 && (
              <div className="mt-6 flex justify-center">
                <JobListPagination
                  currentPage={data.page}
                  totalPages={data.totalPages}
                  hasPreviousPage={data.hasPreviousPage}
                  hasNextPage={data.hasNextPage}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </div>
        )}
      </QueryBoundary>

      {/* Confirmation Modal */}
      <Modal
        open={!!jobToUnsave}
        onClose={() => setJobToUnsave(null)}
        title="Bỏ lưu việc làm"
        footer={
          <div className="flex justify-end gap-3">
            <Button
              variant="ghost"
              onClick={() => setJobToUnsave(null)}
              disabled={isPending}
            >
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirmUnsave}
              disabled={isPending}
            >
              {isPending ? "Đang xử lý..." : "Xác nhận bỏ lưu"}
            </Button>
          </div>
        }
      >
        <p className="text-body text-ink">
          Bạn có chắc chắn muốn bỏ lưu việc làm{" "}
          <strong className="text-navy">{jobToUnsave?.title}</strong> tại{" "}
          <strong className="text-navy">{jobToUnsave?.company}</strong> không?
        </p>
      </Modal>
    </div>
  );
}
