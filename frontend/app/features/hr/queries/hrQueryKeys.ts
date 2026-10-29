import type { EmployerJobFilters, RecruiterApplicationFilters } from "../types";

export const hrQueryKeys = {
  all: ["hr"] as const,
  profile: () => [...hrQueryKeys.all, "profile"] as const,
  company: () => [...hrQueryKeys.all, "company"] as const,
  jobs: {
    all: () => [...hrQueryKeys.all, "jobs"] as const,
    list: (filters: EmployerJobFilters) => [...hrQueryKeys.jobs.all(), "list", filters] as const,
    detail: (id: string) => [...hrQueryKeys.jobs.all(), "detail", id] as const,
  },
  applications: {
    all: () => [...hrQueryKeys.all, "applications"] as const,
    list: (jobId: string, filters: RecruiterApplicationFilters) =>
      [...hrQueryKeys.applications.all(), "list", jobId, filters] as const,
    detail: (id: string) => [...hrQueryKeys.applications.all(), "detail", id] as const,
    pipeline: (jobId: string) => [...hrQueryKeys.applications.all(), "pipeline", jobId] as const,
  },
  masterData: () => [...hrQueryKeys.all, "master-data"] as const,
};
