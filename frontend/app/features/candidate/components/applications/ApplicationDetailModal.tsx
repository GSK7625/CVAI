/**
 * @file ApplicationDetailModal.tsx
 * @description Modal hiển thị chi tiết hồ sơ ứng tuyển kèm Career Journey Timeline và phân tích AI (FC-81b).
 * @architecture
 * - Gọi hook useApplicationDetail(id) khi modal mở.
 * - Hiển thị timeline tiến trình xử lý hồ sơ (tiến trình từ timeline.slice(1) sau mốc nộp ban đầu).
 * - Nút rút đơn ủy quyền lại qua prop onWithdraw, không lồng modal con.
 */

import { Link } from "react-router";
import {
  IconBuilding,
  IconCalendar,
  IconFileText,
  IconSparkles,
  IconExternalLink,
  IconClock,
} from "@tabler/icons-react";
import { useApplicationDetail } from "../../hooks/useApplicationDetail";
import { CAN_WITHDRAW_STATUSES } from "../../types";
import { StatusBadgeVn } from "./StatusBadgeVn";
import { Modal, Skeleton } from "~/components/ui";

interface ApplicationDetailModalProps {
  applicationId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onWithdraw?: (id: string) => void;
}

export function ApplicationDetailModal({
  applicationId,
  isOpen,
  onClose,
  onWithdraw,
}: ApplicationDetailModalProps) {
  const { data: detail, isLoading, isError } = useApplicationDetail(applicationId || undefined);

  const canWithdraw =
    Boolean(detail && (CAN_WITHDRAW_STATUSES as readonly string[]).includes(detail.status));

  return (
    <Modal
      open={isOpen}
      onClose={onClose}
      title="Chi tiết hồ sơ ứng tuyển"
      className="max-w-2xl"
      footer={
        detail ? (
          <div className="w-full flex items-center justify-between">
            {canWithdraw && onWithdraw ? (
              <button
                type="button"
                onClick={() => {
                  if (applicationId) {
                    onClose();
                    onWithdraw(applicationId);
                  }
                }}
                className="px-4 py-2 rounded-full border border-rose-200 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
              >
                Rút đơn ứng tuyển
              </button>
            ) : (
              <span className="text-xs text-ink-muted italic">
                {detail.status === "Withdrawn"
                  ? "Đã rút hồ sơ này"
                  : "Hồ sơ đã qua giai đoạn có thể tự rút đơn"}
              </span>
            )}

            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 rounded-full bg-navy text-xs font-semibold text-white hover:bg-navy-secondary transition-colors cursor-pointer"
            >
              Đóng
            </button>
          </div>
        ) : undefined
      }
    >
      {isLoading ? (
        <div className="space-y-4 py-4">
          <Skeleton className="h-6 w-3/4 rounded-lg" />
          <Skeleton className="h-20 w-full rounded-2xl" />
          <Skeleton className="h-32 w-full rounded-2xl" />
        </div>
      ) : isError || !detail ? (
        <div className="py-8 text-center text-sm text-ink-variant">
          Không thể tải thông tin chi tiết đơn ứng tuyển. Vui lòng thử lại sau.
        </div>
      ) : (
        <div className="space-y-6 py-2">
          {/* Header info */}
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 p-4 rounded-2xl bg-surface-low/60 border border-navy/10">
            <div className="flex items-start gap-3.5">
              {detail.companyLogoUrl ? (
                <img
                  src={detail.companyLogoUrl}
                  alt={detail.companyName}
                  className="w-13 h-13 rounded-xl object-cover border border-navy/10 shadow-xs"
                />
              ) : (
                <div className="w-13 h-13 rounded-xl bg-navy/5 border border-navy/10 flex items-center justify-center text-navy">
                  <IconBuilding size={24} />
                </div>
              )}
              <div>
                <Link
                  to={`/jobs/${detail.jobId}`}
                  target="_blank"
                  className="text-base font-bold text-navy hover:text-navy-secondary transition-colors inline-flex items-center gap-1 group"
                >
                  <span>{detail.jobTitle}</span>
                  <IconExternalLink size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
                <p className="text-xs text-ink-variant mt-0.5">{detail.companyName}</p>
                <p className="text-xs text-ink-muted mt-1 flex items-center gap-2">
                  <span className="inline-flex items-center gap-1">
                    <IconCalendar size={13} />
                    Ngày nộp: {new Date(detail.appliedAt).toLocaleDateString("vi-VN")}
                  </span>
                </p>
              </div>
            </div>

            <div className="flex flex-col items-start sm:items-end gap-2">
              <StatusBadgeVn status={detail.status} size="md" />
              {detail.matchScore != null && (
                <span className="px-2.5 py-0.5 rounded-full bg-navy text-white text-[11px] font-bold shadow-2xs">
                  {detail.matchScore}% Phù hợp
                </span>
              )}
            </div>
          </div>

          {/* CV & Cover Letter */}
          <div className="p-4 rounded-2xl bg-white border border-navy/10 shadow-2xs space-y-3">
            <h4 className="text-xs uppercase tracking-wider font-semibold text-navy flex items-center gap-1.5">
              <IconFileText size={15} /> CV Ứng tuyển & Thư giới thiệu
            </h4>
            <div className="flex items-center justify-between p-3 rounded-xl bg-surface-low/80 border border-navy/5">
              <div className="flex items-center gap-2.5 min-w-0">
                <IconFileText className="text-navy shrink-0" size={18} />
                <span className="text-xs font-semibold text-navy truncate">
                  {detail.cvTitle || "CV Ứng tuyển"}
                </span>
              </div>
              {detail.cvFileUrl && (
                <a
                  href={detail.cvFileUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-1.5 rounded-lg bg-navy/5 text-navy hover:bg-navy/10 text-xs font-medium transition-colors inline-flex items-center gap-1 shrink-0"
                >
                  <span>Xem file</span>
                  <IconExternalLink size={13} />
                </a>
              )}
            </div>

            {detail.coverLetter && (
              <div className="mt-2 pt-2 border-t border-navy/5">
                <p className="text-xs text-ink-muted mb-1">Thư giới thiệu:</p>
                <p className="text-xs text-ink-variant whitespace-pre-line bg-surface-low/50 p-3 rounded-xl border border-navy/5 leading-relaxed">
                  {detail.coverLetter}
                </p>
              </div>
            )}
          </div>

          {/* AI Match Overview */}
          {detail.matchScore != null && (
            <div className="p-4 rounded-2xl bg-surface-low/40 border border-navy/10 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs uppercase tracking-wider font-semibold text-navy flex items-center gap-1.5">
                  <IconSparkles size={15} className="text-gold" /> Đánh giá độ tương thích AI
                </h4>
                <span className="text-xs font-bold text-navy">
                  Điểm số: {detail.matchScore}/100
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-white border border-emerald-200/50">
                  <span className="text-[11px] font-semibold text-emerald-800 block mb-1.5">
                    Kỹ năng tương thích ({detail.matchedSkills?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {detail.matchedSkills?.map((s) => (
                      <span
                        key={s}
                        className="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 text-[11px] border border-emerald-200"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-white border border-amber-200/50">
                  <span className="text-[11px] font-semibold text-amber-800 block mb-1.5">
                    Kỹ năng cần trau dồi ({detail.missingSkills?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {detail.missingSkills?.length ? (
                      detail.missingSkills.map((s) => (
                        <span
                          key={s}
                          className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 text-[11px] border border-amber-200"
                        >
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="text-ink-muted italic">Đạt yêu cầu</span>
                    )}
                  </div>
                </div>
              </div>

              {detail.matchExplanation && (
                <p className="text-xs text-ink-variant bg-white p-3 rounded-xl border border-navy/5 leading-relaxed">
                  <strong className="text-navy">Đánh giá: </strong>
                  {detail.matchExplanation}
                </p>
              )}
            </div>
          )}

          {/* Vertical Timeline: Tiến trình xử lý hồ sơ */}
          <div className="p-4 rounded-2xl bg-white border border-navy/10 space-y-3">
            <h4 className="text-xs uppercase tracking-wider font-semibold text-navy flex items-center gap-1.5">
              <IconClock size={15} /> Tiến trình hồ sơ (Timeline)
            </h4>

            <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-navy/10">
              {/* Initial Step */}
              <div className="relative">
                <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-navy border-2 border-white ring-2 ring-navy/20" />
                <div className="text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-navy">Nộp hồ sơ thành công</span>
                    <span className="text-ink-muted text-[11px]">
                      {new Date(detail.appliedAt).toLocaleString("vi-VN")}
                    </span>
                  </div>
                  <p className="text-ink-variant text-[11px] mt-0.5">
                    Hồ sơ đã được gửi đến nhà tuyển dụng {detail.companyName}.
                  </p>
                </div>
              </div>

              {/* Timeline items from API (slice(1) để không lặp lại mốc Applied ban đầu) */}
              {detail.timeline?.slice(1).map((item, idx) => (
                <div key={idx} className="relative">
                  <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-navy/60 border-2 border-white ring-2 ring-navy/10" />
                  <div className="text-xs">
                    <div className="flex items-center gap-2 flex-wrap">
                      <StatusBadgeVn status={item.toStatus} size="sm" />
                      <span className="text-ink-muted text-[11px]">
                        {new Date(item.changedAt).toLocaleString("vi-VN")}
                      </span>
                    </div>
                    {item.reason && (
                      <p className="text-ink-variant text-[11px] mt-1 p-2 rounded-lg bg-surface-low/80 border border-navy/5">
                        {item.reason}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
}
