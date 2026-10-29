/**
 * @file JobDetailCompanyCard.tsx
 * @description Thẻ thông tin công ty tuyển dụng (quy mô, lĩnh vực, địa chỉ, xác thực).
 */

import { Link } from "react-router";
import {
  IconBuilding,
  IconUsers,
  IconMapPin,
  IconCheck,
  IconExternalLink,
} from "@tabler/icons-react";
import type { Job } from "../../types";

interface JobDetailCompanyCardProps {
  job: Job;
}

export function JobDetailCompanyCard({ job }: JobDetailCompanyCardProps) {
  const companyInitial = job.company ? job.company.charAt(0).toUpperCase() : "C";

  return (
    <div className="rounded-xl border border-border-subtle bg-surface p-6 shadow-surface">
      <h3 className="text-headline-md font-bold text-navy mb-4">Thông tin công ty</h3>

      <div className="flex items-center gap-3 pb-4 border-b border-border-subtle">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-border-subtle bg-surface-low p-1.5">
          {job.companyLogo ? (
            <img
              src={job.companyLogo}
              alt={job.company}
              className="h-full w-full object-contain"
            />
          ) : (
            <span className="text-headline-sm font-bold text-navy">
              {companyInitial}
            </span>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <h4 className="truncate font-bold text-navy">{job.company}</h4>
          {job.verified && (
            <span className="mt-0.5 inline-flex items-center gap-1 text-label-sm font-medium text-emerald-600">
              <IconCheck size={14} stroke={2.5} /> Đã xác thực
            </span>
          )}
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3.5 text-body-sm">
        {job.companyIndustry && (
          <div className="flex items-start gap-2.5">
            <IconBuilding size={16} stroke={1.8} className="mt-0.5 shrink-0 text-ink-muted" />
            <div>
              <span className="text-label-sm text-ink-muted">Lĩnh vực: </span>
              <span className="font-medium text-navy">{job.companyIndustry}</span>
            </div>
          </div>
        )}

        {job.companySize && (
          <div className="flex items-start gap-2.5">
            <IconUsers size={16} stroke={1.8} className="mt-0.5 shrink-0 text-ink-muted" />
            <div>
              <span className="text-label-sm text-ink-muted">Quy mô: </span>
              <span className="font-medium text-navy">{job.companySize}</span>
            </div>
          </div>
        )}

        {(job.workAddress || job.location) && (
          <div className="flex items-start gap-2.5">
            <IconMapPin size={16} stroke={1.8} className="mt-0.5 shrink-0 text-ink-muted" />
            <div>
              <span className="text-label-sm text-ink-muted">Địa chỉ: </span>
              <span className="font-medium text-navy">{job.workAddress || job.location}</span>
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-border-subtle">
        <Link
          to={`/jobs?q=${encodeURIComponent(job.company)}`}
          className="flex items-center justify-center gap-1.5 rounded-lg border border-border-strong bg-surface py-2 text-label font-semibold text-navy transition-colors hover:border-navy hover:text-gold"
        >
          <span>Xem các việc làm khác</span>
          <IconExternalLink size={14} stroke={1.8} />
        </Link>
      </div>
    </div>
  );
}
