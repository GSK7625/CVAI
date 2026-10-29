/**
 * @file ApplySuccess.tsx
 * @description Màn hình thông báo nộp hồ sơ thành công (FC-81a).
 * @architecture Double-bezel nesting, checkmark animation, nút điều hướng quản lý hồ sơ & tìm việc khác.
 */

import { Link } from "react-router";
import {
  IconArrowRight,
  IconCircleCheck,
  IconSparkles,
} from "@tabler/icons-react";

interface ApplySuccessProps {
  jobTitle: string;
  companyName: string;
}

export function ApplySuccess({ jobTitle, companyName }: ApplySuccessProps) {
  return (
    <div className="mx-auto max-w-2xl py-20 px-4">
      <div className="p-2 rounded-[2.5rem] bg-navy/5 border border-navy/10 shadow-xl transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]">
        <div className="p-10 sm:p-14 bg-white rounded-[calc(2.5rem-0.5rem)] text-center shadow-[inset_0_1px_1px_rgba(255,255,255,0.8)]">
          <div className="mx-auto w-20 h-20 rounded-full bg-emerald-50 border border-emerald-200/60 flex items-center justify-center text-emerald-600 mb-6 shadow-inner">
            <IconCircleCheck size={48} stroke={1.5} className="animate-in zoom-in-50 duration-500" />
          </div>
          <div className="inline-flex items-center gap-2 rounded-full px-3 py-1 bg-emerald-50 text-emerald-700 text-[11px] uppercase tracking-[0.2em] font-semibold mb-3">
            <IconSparkles size={13} /> Nộp hồ sơ thành công
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-navy">
            Hồ sơ của bạn đã được chuyển tới nhà tuyển dụng!
          </h1>
          <p className="mt-3 text-ink-variant text-sm max-w-md mx-auto leading-relaxed">
            Bạn đã ứng tuyển thành công vị trí <strong className="text-navy">{jobTitle}</strong> tại{" "}
            <strong className="text-navy">{companyName}</strong>. Nhà tuyển dụng sẽ xem xét và phản hồi trong thời gian sớm nhất.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/candidate/applications"
              className="group w-full sm:w-auto inline-flex items-center justify-between gap-4 rounded-full bg-navy px-7 py-3.5 text-sm font-semibold text-white shadow-md hover:bg-navy-secondary active:scale-[0.98] transition-all duration-300"
            >
              <span>Xem hồ sơ đã ứng tuyển</span>
              <span className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center transition-transform duration-300 group-hover:translate-x-1">
                <IconArrowRight size={14} />
              </span>
            </Link>
            <Link
              to="/jobs"
              className="w-full sm:w-auto inline-flex items-center justify-center px-7 py-3.5 rounded-full border border-navy/20 text-sm font-semibold text-navy hover:bg-navy/5 transition-all"
            >
              Tiếp tục tìm việc
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
