import { memo } from "react";
import { useNavigate } from "react-router";
import { IconHeart, IconHeartFilled } from "@tabler/icons-react";
import { formatSalary } from "~/utils";
import type { Job } from "~/features/candidate/types";
import { useSavedJobIds } from "~/features/candidate/hooks/useSavedJobIds";
import { useToggleSaveJob } from "~/features/candidate/hooks/useToggleSaveJob";
import { cn } from "~/lib/cn";

export interface JobCardProps {
  job: Job;
  className?: string;
  saved?: boolean;
  onToggleSave?: () => void;
}

export const JobCard = memo(function JobCard({
  job,
  className,
  saved,
  onToggleSave,
}: JobCardProps) {
  const navigate = useNavigate();
  const { data: savedJobIds } = useSavedJobIds();
  const { toggleSave, isPending } = useToggleSaveJob();

  const isSaved = saved !== undefined ? saved : (savedJobIds ? savedJobIds.has(job.id) : false);

  const handleCardClick = () => {
    navigate(`/jobs/${job.id}`);
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (onToggleSave) {
      onToggleSave();
    } else {
      toggleSave(job.id);
    }
  };

  return (
    <article
      onClick={handleCardClick}
      className={cn(
        "group relative flex h-[116px] w-full cursor-pointer items-center gap-3 rounded-xl border border-border-subtle bg-surface p-3 shadow-sm transition-all duration-200 hover:border-gold/60 hover:shadow-md",
        className,
      )}
    >
      {/* Company Logo Avatar */}
      <div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-border-subtle bg-surface-low p-1">
        {job.companyLogo ? (
          <img src={job.companyLogo} alt={job.company} className="h-full w-full object-contain" />
        ) : (
          <span className="text-base font-bold text-navy">
            {job.company.charAt(0).toUpperCase()}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="flex h-full min-w-0 flex-grow flex-col justify-between py-0.5">
        {/* Top: Badges, Title & Company */}
        <div className="min-w-0">
          <div className="flex min-h-[16px] items-center gap-1.5 flex-wrap">
            {job.hot && (
              <span className="rounded bg-danger/10 px-1.5 py-0.2 text-[10px] font-bold text-danger">
                HOT
              </span>
            )}
            {job.salaryMin && job.salaryMin >= 20 ? (
              <span className="rounded bg-success/15 px-1.5 py-0.2 text-[10px] font-bold text-success">
                TOP
              </span>
            ) : null}
          </div>

          <h3 className="line-clamp-1 text-label font-semibold text-navy transition-colors group-hover:text-gold mt-0.5">
            {job.title}
          </h3>

          <p className="line-clamp-1 text-[12px] text-ink-muted">
            {job.company}
          </p>
        </div>

        {/* Bottom: Tags & Save Button */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="rounded bg-surface-low px-2 py-0.5 text-[11px] font-semibold text-ink">
              {formatSalary(job.salaryMin, job.salaryMax)}
            </span>
            <span className="rounded bg-surface-low px-2 py-0.5 text-[11px] text-ink-muted">
              {job.location}
            </span>
          </div>

          <button
            type="button"
            aria-label={isSaved ? "Bỏ lưu việc làm" : "Lưu việc làm"}
            onClick={handleToggle}
            disabled={isPending}
            className="text-ink-muted transition-colors hover:text-danger p-0.5 disabled:opacity-50"
          >
            {isSaved ? (
              <IconHeartFilled size={16} className="text-danger" />
            ) : (
              <IconHeart size={16} stroke={1.6} />
            )}
          </button>
        </div>
      </div>
    </article>
  );
});
