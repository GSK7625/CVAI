export const candidateQueryKeys = {
  jobs: {
    all: ["candidate", "jobs"] as const,
    list: (filters: unknown) => ["candidate", "jobs", "list", filters] as const,
    detail: (id: string) => ["candidate", "jobs", "detail", id] as const,
    masterData: ["candidate", "jobs", "master-data"] as const,
  },
  savedJobs: {
    all: ["candidate", "saved-jobs"] as const,
    list: (page: number) => ["candidate", "saved-jobs", "list", page] as const,
  },
  cvs: {
    all: ["candidate", "cvs"] as const,
    detail: (id: string) => ["candidate", "cvs", "detail", id] as const,
    analysis: (id: string) => ["candidate", "cvs", "analysis", id] as const,
  },
  applications: {
    all: ["candidate", "applications"] as const,
    list: (filters: unknown) => ["candidate", "applications", "list", filters] as const,
    detail: (id: string) => ["candidate", "applications", "detail", id] as const,
  },
  previewMatch: (jobId: string, cvId?: string | null) =>
    ["candidate", "jobs", "preview-match", jobId, cvId ?? "latest"] as const,
  profile: ["candidate", "profile"] as const,
};
