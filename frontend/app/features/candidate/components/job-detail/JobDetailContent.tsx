/**
 * @file JobDetailContent.tsx
 * @description Hiển thị chi tiết mô tả công việc, yêu cầu ứng viên, quyền lợi và danh sách kỹ năng.
 * @architecture Safe rendering (tránh XSS, hỗ trợ whitespace-pre-line và structured list).
 */

import {
  IconFileDescription,
  IconCircleCheck,
  IconGift,
  IconSparkles,
} from "@tabler/icons-react";
import { Badge } from "~/components/ui/Badge";
import type { Job } from "../../types";

interface JobDetailContentProps {
  job: Job;
}

export function JobDetailContent({ job }: JobDetailContentProps) {
  return (
    <div className="flex flex-col gap-6">
      {/* Mô tả công việc */}
      {job.description && (
        <section className="rounded-xl border border-border-subtle bg-surface p-6 shadow-surface">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-navy/5 text-navy">
              <IconFileDescription size={18} stroke={1.8} />
            </div>
            <h2 className="text-headline-md font-bold text-navy">Mô tả công việc</h2>
          </div>
          <div className="whitespace-pre-line text-body leading-relaxed text-ink">
            {job.description}
          </div>
        </section>
      )}

      {/* Yêu cầu ứng viên */}
      {(job.requirementsText || (job.requirements && job.requirements.length > 0)) && (
        <section className="rounded-xl border border-border-subtle bg-surface p-6 shadow-surface">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <IconCircleCheck size={18} stroke={1.8} />
            </div>
            <h2 className="text-headline-md font-bold text-navy">Yêu cầu ứng viên</h2>
          </div>

          {job.requirements && job.requirements.length > 0 ? (
            <ul className="flex flex-col gap-2.5">
              {job.requirements.map((req, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-body text-ink">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-navy" />
                  <span>{req}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="whitespace-pre-line text-body leading-relaxed text-ink">
              {job.requirementsText}
            </div>
          )}
        </section>
      )}

      {/* Quyền lợi được hưởng */}
      {(job.benefitsText || (job.benefits && job.benefits.length > 0)) && (
        <section className="rounded-xl border border-border-subtle bg-surface p-6 shadow-surface">
          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold/15 text-gold">
              <IconGift size={18} stroke={1.8} />
            </div>
            <h2 className="text-headline-md font-bold text-navy">Quyền lợi được hưởng</h2>
          </div>

          {job.benefits && job.benefits.length > 0 ? (
            <ul className="flex flex-col gap-2.5">
              {job.benefits.map((ben, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-body text-ink">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />
                  <span>{ben}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="whitespace-pre-line text-body leading-relaxed text-ink">
              {job.benefitsText}
            </div>
          )}
        </section>
      )}

      {/* Kỹ năng yêu cầu */}
      {job.skills && job.skills.length > 0 && (
        <section className="rounded-xl border border-border-subtle bg-surface p-6 shadow-surface">
          <div className="mb-3 flex items-center gap-2">
            <IconSparkles size={18} stroke={1.8} className="text-gold" />
            <h2 className="text-headline-md font-bold text-navy">Kỹ năng chuyên môn</h2>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {job.skills.map((skill, idx) => (
              <Badge key={idx} variant="neutral" className="px-3 py-1 text-label font-medium">
                {skill}
              </Badge>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
