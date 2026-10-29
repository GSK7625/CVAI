/**
 * @file ApplicationRow.tsx
 * @description Hàng hiển thị thông tin một đơn ứng tuyển trong danh sách (FC-81b).
 * @architecture
 * - Tuân thủ kiến trúc Double-bezel (Doppelrand) với khung viền lồng 2 lớp.
 * - Hiển thị logo, tiêu đề việc làm, công ty, mức lương, trạng thái tiếng Việt, điểm khớp AI.
 * - Nút xem chi tiết và nút rút hồ sơ (nếu ở trạng thái Cho phép).
 */

import { Link } from "react-router";
import {
  IconBuilding,
  IconClock,
  IconEye,
  IconMapPin,
  IconSparkles,
  IconRotateClockwise,
} from "@tabler/icons-react";
import type { ApplicationListItem } from "../../types";
import { CAN_WITHDRAW_STATUSES } from "../../types";
import { StatusBadgeVn } from "./StatusBadgeVn";
import { formatSalary } from "~/utils";

interface ApplicationRowProps {
  application: ApplicationListItem;
  onViewDetail: (id: string) => void;
  onWithdraw: (id: string) => void;
}

export function ApplicationRow({ application, onViewDetail, onWithdraw }: ApplicationRowProps) {
  const canWithdraw = (CAN_WITHDRAW_STATUSES as readonly string[]).includes(application.status);
  const isWithdrawn = application.status === "Withdrawn";

  return (
    <div className="group p-1 rounded-[2rem] bg-navy/5 border border-navy/10 hover:border-navy/20 hover:shadow-md transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]">
      <div className="p-5 sm:p-6 bg-white rounded-[calc(2rem-0.25rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.8)]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
          {/* Main Info: Logo + Title + Company + Location */}
          <div className="flex items-start gap-4 min-w-0">
            {application.companyLogo ? (
              <img
                src={application.companyLogo}
                alt={application.companyName}
                className="w-14 h-14 rounded-2xl object-cover border border-navy/10 shrink-0 shadow-2xs"
              />
            ) : (
              <div className="w-14 h-14 rounded-2xl bg-navy/5 border border-navy/10 flex items-center justify-center text-navy shrink-0">
                <IconBuilding size={26} stroke={1.5} />
              </div>
            )}

            <div className="min-w-0 space-y-1">
              <div className="flex items-center gap-2.5 flex-wrap">
                <Link
                  to={`/jobs/${application.jobId}`}
                  className="text-base sm:text-lg font-bold text-navy hover:text-navy-secondary transition-colors truncate"
                >
                  {application.jobTitle}
                </Link>
                <StatusBadgeVn status={application.status} size="sm" />
              </div>

              <p className="text-xs sm:text-sm text-ink-variant font-medium flex items-center gap-2 truncate">
                <span>{application.companyName}</span>
                <span className="text-ink-muted">•</span>
                <span className="inline-flex items-center gap-1 text-ink-muted">
                  <IconMapPin size={14} />
                  {application.location}
                </span>
              </p>

              <div className="flex items-center gap-3 pt-1 text-xs text-ink-muted flex-wrap">
                <span className="font-semibold text-navy">
                  {formatSalary(application.salaryMin, application.salaryMax)}
                </span>
                <span>•</span>
                <span className="inline-flex items-center gap-1">
                  <IconClock size={13} />
                  Ứng tuyển: {new Date(application.appliedAt).toLocaleDateString("vi-VN")}
                </span>
                {application.matchScore != null && (
                  <>
                    <span>•</span>
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/30 text-amber-800 text-[11px] font-bold">
                      <IconSparkles size={12} className="text-amber-600" />
                      {application.matchScore}% Match
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 shrink-0 self-end md:self-center">
            {isWithdrawn ? (
              <Link
                to={`/jobs/${application.jobId}/apply`}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-navy/20 bg-surface-low text-xs font-semibold text-navy hover:bg-navy/5 hover:border-navy transition-all"
              >
                <IconRotateClockwise size={14} />
                <span>Nộp lại</span>
              </Link>
            ) : canWithdraw ? (
              <button
                type="button"
                onClick={() => onWithdraw(application.id)}
                className="px-3.5 py-2 rounded-full border border-rose-200 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors"
              >
                Rút đơn
              </button>
            ) : null}

            <button
              type="button"
              onClick={() => onViewDetail(application.id)}
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-navy text-xs font-semibold text-white shadow-xs hover:bg-navy-secondary active:scale-[0.98] transition-all"
            >
              <IconEye size={15} />
              <span>Xem chi tiết</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
