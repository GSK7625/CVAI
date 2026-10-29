/**
 * @file JobDetailOverview.tsx
 * @description Bảng tóm tắt các thông số chính của công việc (lương, kinh nghiệm, cấp bậc, hình thức, số lượng).
 */

import {
  IconCoin,
  IconMapPin,
  IconBriefcase,
  IconAward,
  IconClock,
  IconUsers,
} from "@tabler/icons-react";
import { formatSalary } from "~/utils";
import type { Job } from "../../types";

interface JobDetailOverviewProps {
  job: Job;
}

export function JobDetailOverview({ job }: JobDetailOverviewProps) {
  const items = [
    {
      icon: IconCoin,
      label: "Mức lương",
      value: formatSalary(job.salaryMin, job.salaryMax),
      highlight: true,
    },
    {
      icon: IconMapPin,
      label: "Địa điểm",
      value: job.location,
    },
    {
      icon: IconBriefcase,
      label: "Kinh nghiệm",
      value: job.experience,
    },
    {
      icon: IconAward,
      label: "Cấp bậc",
      value: job.level || "Tất cả cấp bậc",
    },
    {
      icon: IconClock,
      label: "Hình thức làm việc",
      value: job.jobType || "Toàn thời gian",
    },
    {
      icon: IconUsers,
      label: "Số lượng tuyển",
      value: job.quantity || "Chưa xác định",
    },
  ];

  return (
    <div className="rounded-xl border border-border-subtle bg-surface p-6 shadow-surface">
      <h2 className="text-headline-md font-bold text-navy mb-4">Thông tin chung</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="flex items-start gap-3 rounded-lg border border-border-subtle bg-surface-low p-3.5"
          >
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                item.highlight
                  ? "bg-gold/15 text-gold"
                  : "bg-surface text-navy"
              }`}
            >
              <item.icon size={20} stroke={1.8} />
            </div>
            <div className="min-w-0">
              <span className="text-label-sm text-ink-muted">{item.label}</span>
              <p
                className={`mt-0.5 truncate text-body-sm font-semibold ${
                  item.highlight ? "text-gold" : "text-navy"
                }`}
              >
                {item.value}
              </p>
            </div>
          </div>
        ))}
      </div>

      {job.skills && job.skills.length > 0 && (
        <div className="mt-5 border-t border-border-subtle pt-4">
          <span className="text-label-sm font-semibold text-ink-muted">
            Kỹ năng yêu cầu:
          </span>
          <div className="mt-2 flex flex-wrap gap-2">
            {job.skills.map((skill, idx) => (
              <span
                key={idx}
                className="inline-flex items-center rounded-default border border-border-subtle bg-surface-low px-2.5 py-1 text-label-sm font-medium text-navy"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
