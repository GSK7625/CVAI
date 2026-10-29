/**
 * @file StatusBadgeVn.tsx
 * @description Huy hiệu trạng thái hồ sơ ứng tuyển bằng tiếng Việt với phong cách tinh tế (FC-81b).
 * @architecture Map trạng thái CandidateApplicationStatus sang nhãn hiển thị và bảng màu hài hòa.
 */

import type { CandidateApplicationStatus } from "../../types";

interface StatusBadgeVnProps {
  status: CandidateApplicationStatus | string;
  className?: string;
  size?: "sm" | "md";
}

interface StatusConfig {
  label: string;
  dotColor: string;
  badgeStyle: string;
}

const STATUS_CONFIGS: Record<string, StatusConfig> = {
  Applied: {
    label: "Tiếp nhận",
    dotColor: "bg-sky-500",
    badgeStyle: "bg-sky-50/80 text-sky-700 border-sky-200/60",
  },
  Screening: {
    label: "Đang duyệt",
    dotColor: "bg-indigo-500",
    badgeStyle: "bg-indigo-50/80 text-indigo-700 border-indigo-200/60",
  },
  Interview: {
    label: "Phỏng vấn",
    dotColor: "bg-amber-500",
    badgeStyle: "bg-amber-50/80 text-amber-700 border-amber-200/60",
  },
  Offer: {
    label: "Đề nghị nhận việc",
    dotColor: "bg-teal-500",
    badgeStyle: "bg-teal-50/80 text-teal-700 border-teal-200/60",
  },
  Hired: {
    label: "Trúng tuyển",
    dotColor: "bg-emerald-500",
    badgeStyle: "bg-emerald-50/80 text-emerald-700 border-emerald-200/60",
  },
  Rejected: {
    label: "Chưa phù hợp",
    dotColor: "bg-rose-400",
    badgeStyle: "bg-rose-50/80 text-rose-700 border-rose-200/60",
  },
  Withdrawn: {
    label: "Đã rút hồ sơ",
    dotColor: "bg-slate-400",
    badgeStyle: "bg-slate-100 text-slate-600 border-slate-200",
  },
};

export function StatusBadgeVn({ status, className = "", size = "md" }: StatusBadgeVnProps) {
  const config = STATUS_CONFIGS[status] || {
    label: status,
    dotColor: "bg-slate-400",
    badgeStyle: "bg-slate-100 text-slate-700 border-slate-200",
  };

  const sizeClasses =
    size === "sm"
      ? "px-2 py-0.5 text-[11px] gap-1.5"
      : "px-2.5 py-1 text-xs gap-2";

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border shadow-2xs transition-colors ${config.badgeStyle} ${sizeClasses} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor} animate-pulse`} />
      <span>{config.label}</span>
    </span>
  );
}
