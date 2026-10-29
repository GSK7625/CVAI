/**
 * @file ApplicationsView.tsx
 * @description Giao diện danh sách hồ sơ việc làm đã ứng tuyển của ứng viên (FC-81b, P3-UC06).
 * @architecture
 * - Dữ liệu thực qua useMyApplications, kết nối trực tiếp GET /api/candidate/applications (KHÔNG MOCK).
 * - Bộ lọc Tab trạng thái (Tất cả, Tiếp nhận, Đang duyệt, Phỏng vấn, Đề nghị việc, Trúng tuyển, Chưa phù hợp, Đã rút).
 * - Đồng bộ trạng thái bộ lọc và phân trang qua URL search params (?status=...&page=...).
 * - Tích hợp ApplicationDetailModal để xem chi tiết timeline và phân tích match AI, hỗ trợ rút đơn tức thì.
 */

import { useState } from "react";
import { Link, useSearchParams } from "react-router";
import {
  IconBriefcase,
  IconClock,
  IconFileText,
  IconSearch,
  IconSparkles,
} from "@tabler/icons-react";
import { useMyApplications } from "../../hooks/useMyApplications";
import { useWithdrawApplication } from "../../hooks/useWithdrawApplication";
import { ApplicationRow } from "./ApplicationRow";
import { ApplicationDetailModal } from "./ApplicationDetailModal";
import { JobListPagination } from "../job-list/JobListPagination";
import { QueryBoundary } from "~/components/shared/QueryBoundary";
import { Button, EmptyState, Modal, Skeleton } from "~/components/ui";

const APPLICATION_TABS = [
  { key: "", label: "Tất cả" },
  { key: "Applied", label: "Tiếp nhận" },
  { key: "Screening", label: "Đang duyệt" },
  { key: "Interview", label: "Phỏng vấn" },
  { key: "Offer", label: "Đề nghị việc" },
  { key: "Hired", label: "Trúng tuyển" },
  { key: "Rejected", label: "Chưa phù hợp" },
  { key: "Withdrawn", label: "Đã rút đơn" },
];

function ApplicationsSkeleton() {
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

export function ApplicationsView() {
  const [searchParams, setSearchParams] = useSearchParams();

  const currentStatus = searchParams.get("status") || "";
  const currentPage = Math.max(1, Number(searchParams.get("page") || "1"));

  // State modal chi tiết hồ sơ & modal rút đơn
  const [detailModalAppId, setDetailModalAppId] = useState<string | null>(null);
  const [withdrawAppId, setWithdrawAppId] = useState<string | null>(null);
  const [withdrawReason, setWithdrawReason] = useState("");

  // Query dữ liệu hồ sơ
  const { data, isLoading, error, refetch } = useMyApplications({
    status: currentStatus || undefined,
    page: currentPage,
    pageSize: 10,
  });

  const withdrawMutation = useWithdrawApplication();

  const handleTabChange = (newStatus: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (!newStatus) {
        next.delete("status");
      } else {
        next.set("status", newStatus);
      }
      next.delete("page"); // Reset về trang 1
      return next;
    });
  };

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

  const handleConfirmQuickWithdraw = async () => {
    if (!withdrawAppId) return;
    try {
      await withdrawMutation.mutateAsync({
        id: withdrawAppId,
        reason: withdrawReason.trim() || undefined,
      });
      setWithdrawAppId(null);
      setWithdrawReason("");
    } catch {
      // Error handled in hook toast
    }
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
            <span className="font-semibold text-navy">Việc làm đã ứng tuyển</span>
          </nav>
          <h1 className="text-2xl sm:text-3xl font-bold text-navy">
            Việc làm đã ứng tuyển {data?.total != null ? `(${data.total})` : ""}
          </h1>
          <p className="mt-1 text-sm text-ink-variant">
            Theo dõi tiến trình xét duyệt hồ sơ, phản hồi phỏng vấn và cơ hội việc làm từ nhà tuyển dụng.
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

      {/* Tabs bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none border-b border-navy/5">
        {APPLICATION_TABS.map((tab) => {
          const isActive = currentStatus === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => handleTabChange(tab.key)}
              className={`px-4 py-2 rounded-full text-xs font-semibold shrink-0 transition-all duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] ${
                isActive
                  ? "bg-navy text-white shadow-sm"
                  : "bg-surface-low/80 text-ink-variant hover:bg-navy/5 hover:text-navy"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Main List with QueryBoundary */}
      <QueryBoundary
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        skeleton={<ApplicationsSkeleton />}
      >
        {data && data.items.length === 0 ? (
          <EmptyState
            icon={<IconFileText size={48} className="text-ink-muted" stroke={1.5} />}
            title={
              currentStatus
                ? "Không có hồ sơ nào ở trạng thái này"
                : "Bạn chưa nộp hồ sơ ứng tuyển nào"
            }
            description={
              currentStatus
                ? "Thử chuyển sang tab trạng thái khác hoặc xem danh sách tất cả hồ sơ."
                : "Khám phá hàng trăm cơ hội việc làm phù hợp và nộp hồ sơ ứng tuyển ngay hôm nay!"
            }
            action={
              currentStatus ? (
                <Button variant="secondary" onClick={() => handleTabChange("")}>
                  Xem tất cả hồ sơ
                </Button>
              ) : (
                <Link to="/jobs">
                  <Button variant="primary">
                    <IconSearch size={18} />
                    Tìm việc làm ngay
                  </Button>
                </Link>
              )
            }
            className="my-10"
          />
        ) : (
          <div className="space-y-4">
            {data?.items.map((app) => (
              <ApplicationRow
                key={app.id}
                application={app}
                onViewDetail={(id) => setDetailModalAppId(id)}
                onWithdraw={(id) => setWithdrawAppId(id)}
              />
            ))}

            {/* Phân trang */}
            {data && data.totalPages > 1 && (
              <div className="mt-8 flex justify-center">
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

      {/* Modal Chi tiết đơn ứng tuyển */}
      <ApplicationDetailModal
        applicationId={detailModalAppId}
        isOpen={Boolean(detailModalAppId)}
        onClose={() => setDetailModalAppId(null)}
        onWithdraw={(id) => {
          setDetailModalAppId(null);
          setWithdrawAppId(id);
        }}
      />

      {/* Quick Withdraw Modal */}
      <Modal
        open={Boolean(withdrawAppId)}
        onClose={() => setWithdrawAppId(null)}
        title="Xác nhận rút đơn ứng tuyển"
      >
        <div className="py-2 space-y-4">
          <p className="text-xs text-ink-variant leading-relaxed">
            Bạn có chắc chắn muốn rút đơn ứng tuyển này? Nhà tuyển dụng sẽ thấy hồ sơ ở trạng thái Đã rút.
          </p>

          <div>
            <label htmlFor="quick-withdraw-reason" className="block text-xs font-semibold text-navy mb-1">
              Lý do rút đơn (Không bắt buộc):
            </label>
            <textarea
              id="quick-withdraw-reason"
              rows={3}
              value={withdrawReason}
              onChange={(e) => setWithdrawReason(e.target.value)}
              placeholder="VD: Đã tìm được công việc khác..."
              className="w-full p-3 text-xs rounded-xl border border-navy/15 bg-surface-low outline-none focus:border-navy focus:bg-white"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setWithdrawAppId(null)}
              className="px-4 py-2 rounded-full border border-navy/20 text-xs font-semibold text-navy hover:bg-navy/5"
            >
              Hủy
            </button>
            <button
              type="button"
              disabled={withdrawMutation.isPending}
              onClick={handleConfirmQuickWithdraw}
              className="px-5 py-2 rounded-full bg-rose-600 text-xs font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
            >
              {withdrawMutation.isPending ? "Đang xử lý..." : "Xác nhận rút đơn"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
