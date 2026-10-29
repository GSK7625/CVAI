/**
 * @file JobDetailSimilarJobs.tsx
 * @description Danh sách gợi ý việc làm tương tự theo ngành nghề (CategoryId).
 */

import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { IconMapPin, IconSparkles } from "@tabler/icons-react";
import { jobService } from "../../services/jobService";
import { Badge } from "~/components/ui/Badge";
import { formatSalary } from "~/utils";

interface JobDetailSimilarJobsProps {
  jobId: string;
  categoryId?: string;
}

export function JobDetailSimilarJobs({ jobId, categoryId }: JobDetailSimilarJobsProps) {
  const { data: similarJobs, isLoading } = useQuery({
    queryKey: ["candidate", "jobs", "similar", jobId, categoryId],
    queryFn: ({ signal }) => jobService().similar(jobId, categoryId, signal),
  });

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border-subtle bg-surface p-6 shadow-surface">
        <h3 className="text-headline-md font-bold text-navy mb-4">Việc làm tương tự</h3>
        <div className="flex flex-col gap-3">
          <div className="h-16 rounded bg-surface-low animate-pulse" />
          <div className="h-16 rounded bg-surface-low animate-pulse" />
        </div>
      </div>
    );
  }

  if (!similarJobs || similarJobs.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-border-subtle bg-surface p-6 shadow-surface">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <IconSparkles size={18} stroke={1.8} className="text-gold" />
          <h3 className="text-headline-md font-bold text-navy">Việc làm tương tự</h3>
        </div>
      </div>

      <div className="flex flex-col gap-3.5">
        {similarJobs.map((item) => (
          <article
            key={item.id}
            className="group rounded-lg border border-border-subtle p-3.5 transition-all hover:border-navy hover:bg-surface-low"
          >
            <h4 className="line-clamp-1 font-semibold text-navy transition-colors group-hover:text-gold">
              <Link to={`/jobs/${item.id}`}>{item.title}</Link>
            </h4>
            <p className="mt-1 line-clamp-1 text-label-sm font-medium uppercase tracking-wider text-ink-muted">
              {item.company}
            </p>
            <div className="mt-2.5 flex items-center justify-between gap-2">
              <Badge variant="gold" className="text-label-sm font-bold">
                {formatSalary(item.salaryMin, item.salaryMax)}
              </Badge>
              <span className="flex items-center gap-1 text-label-sm text-ink-muted truncate">
                <IconMapPin size={13} stroke={1.6} />
                {item.location}
              </span>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
