/**
 * @file CandidateInfoSection.tsx
 * @description Phần hiển thị thông tin ứng viên đã xác thực từ tài khoản (FC-81a).
 * @architecture Double-bezel nesting, hiển thị họ tên, email, số điện thoại thật của ứng viên.
 */

import { IconCheck } from "@tabler/icons-react";
import { Skeleton } from "~/components/ui";

interface CandidateInfoSectionProps {
  fullName?: string;
  email?: string;
  phone?: string;
  isLoading?: boolean;
}

export function CandidateInfoSection({
  fullName,
  email,
  phone,
  isLoading,
}: CandidateInfoSectionProps) {
  return (
    <div className="p-1.5 rounded-[2rem] bg-navy/5 border border-navy/10">
      <div className="p-6 sm:p-8 bg-white rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.8)]">
        <div className="flex items-center justify-between border-b border-navy/5 pb-4 mb-4">
          <div>
            <h2 className="text-base font-bold text-navy">1. Thông tin ứng viên</h2>
            <p className="text-xs text-ink-variant mt-0.5">
              Hồ sơ được liên kết trực tiếp với tài khoản của bạn
            </p>
          </div>
          <div className="px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200/60 text-emerald-700 text-xs font-semibold flex items-center gap-1.5">
            <IconCheck size={14} /> Đã xác thực
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div className="p-3.5 rounded-xl bg-surface-low/80 border border-navy/5">
            <span className="text-xs text-ink-muted block">Họ và tên</span>
            <span className="font-semibold text-navy">
              {isLoading ? (
                <Skeleton className="h-5 w-28 mt-0.5 rounded-md" />
              ) : (
                fullName || ""
              )}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-low/80 border border-navy/5">
            <span className="text-xs text-ink-muted block">Email liên hệ</span>
            <span className="font-semibold text-navy">
              {isLoading ? (
                <Skeleton className="h-5 w-36 mt-0.5 rounded-md" />
              ) : (
                email || ""
              )}
            </span>
          </div>

          {phone && (
            <div className="p-3.5 rounded-xl bg-surface-low/80 border border-navy/5">
              <span className="text-xs text-ink-muted block">Số điện thoại</span>
              <span className="font-semibold text-navy">{phone}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
