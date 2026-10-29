/**
 * @file JobDetailHeader.tsx
 * @description Banner thông tin chính của công việc (tiêu đề, công ty, lương, nút ứng tuyển/lưu).
 */

import { Link } from "react-router";
import {
  IconMapPin,
  IconCalendar,
  IconBriefcase,
  IconCheck,
  IconHeart,
  IconHeartFilled,
  IconShare,
} from "@tabler/icons-react";
import { formatSalary } from "~/utils";
import type { Job } from "../../types";

interface JobDetailHeaderProps {
  job: Job;
  saved: boolean;
  onToggleSave: () => void;
  onShare: () => void;
}

export function JobDetailHeader({
  job,
  saved,
  onToggleSave,
  onShare,
}: JobDetailHeaderProps) {
  const companyInitial = job.company ? job.company.charAt(0).toUpperCase() : "J";

  return (
    <div className="relative overflow-hidden rounded-xl border border-border-subtle bg-surface p-6 shadow-surface sm:p-8">
      {/* Decorative gold ambient glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute -right-12 -top-12 h-64 w-64 rounded-full bg-gold/5 blur-2xl"
      />

      <div className="relative z-10 flex flex-col justify-between gap-6 lg:flex-row lg:items-center">
        {/* Left: Logo & Job Info */}
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
          <div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-border-subtle bg-surface-low p-2">
            {job.companyLogo ? (
              <img
                src={job.companyLogo}
                alt={job.company}
                className="h-full w-full object-contain"
              />
            ) : (
              <span className="text-2xl font-bold text-navy">
                {companyInitial}
              </span>
            )}
          </div>

          <div className="flex flex-col">
            <div className="mb-1 flex items-center gap-2 flex-wrap">
              <span className="text-label-sm font-semibold uppercase tracking-wider text-ink-muted">
                {job.company}
              </span>
              {job.verified && (
                <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                  <IconCheck size={12} stroke={2.5} /> Đã xác thực
                </span>
              )}
              {import.meta.env.DEV && job.isDemoFallback && (
                <span className="flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] font-semibold text-amber-700">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" />
                  Dữ liệu Demo (Backend offline)
                </span>
              )}
            </div>

            <h1 className="text-xl font-bold leading-snug text-navy sm:text-2xl lg:text-3xl">
              {job.title}
            </h1>

            {/* Metadata Pills */}
            <div className="mt-4 flex flex-wrap items-center gap-2.5">
              <span className="flex items-center gap-1.5 rounded-lg border border-gold/40 bg-gold/10 px-3 py-1.5 text-label-sm font-bold text-gold">
                {formatSalary(job.salaryMin, job.salaryMax)}
              </span>
              <span className="flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-low px-3 py-1.5 text-label-sm font-medium text-ink-variant">
                <IconMapPin size={15} stroke={1.8} className="text-ink-muted" />
                {job.location}
              </span>
              <span className="flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-low px-3 py-1.5 text-label-sm font-medium text-ink-variant">
                <IconBriefcase size={15} stroke={1.8} className="text-ink-muted" />
                {job.experience}
              </span>
              {job.deadline && (
                <span className="flex items-center gap-1.5 rounded-lg border border-border-subtle bg-surface-low px-3 py-1.5 text-label-sm font-medium text-ink-variant">
                  <IconCalendar size={15} stroke={1.8} className="text-ink-muted" />
                  Hạn nộp: {new Date(job.deadline).toLocaleDateString("vi-VN")}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right: Action buttons */}
        <div className="flex items-center gap-3 self-stretch sm:self-auto lg:shrink-0">
          <Link
            to={`/jobs/${job.id}/apply`}
            className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gold px-6 py-3 text-label font-bold text-white shadow-sm transition-all hover:bg-[#b08233] active:scale-[0.98] sm:flex-initial"
          >
            Ứng tuyển ngay
          </Link>
          <button
            type="button"
            onClick={onToggleSave}
            aria-label={saved ? "Bỏ lưu việc làm" : "Lưu việc làm"}
            className={`flex h-11 w-11 items-center justify-center rounded-xl border transition-all ${
              saved
                ? "border-red-200 bg-red-50 text-red-500 shadow-sm"
                : "border-border-subtle bg-surface text-ink-muted hover:border-navy hover:text-navy"
            }`}
          >
            {saved ? (
              <IconHeartFilled size={20} className="text-red-500" />
            ) : (
              <IconHeart size={20} stroke={1.8} />
            )}
          </button>
          <button
            type="button"
            onClick={onShare}
            aria-label="Chia sẻ liên kết việc làm"
            className="flex h-11 w-11 items-center justify-center rounded-xl border border-border-subtle bg-surface text-ink-muted transition-all hover:border-navy hover:text-navy"
          >
            <IconShare size={20} stroke={1.8} />
          </button>
        </div>
      </div>
    </div>
  );
}
