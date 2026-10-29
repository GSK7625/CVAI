/**
 * Query keys toàn dự án. Feature cụ thể khai báo key riêng trong
 * `features/<feature>/queries/` và ghép vào đây để tổng hợp.
 */
export const queryKeys = {
  auth: ["auth"] as const,
  jobs: {
    all: ["jobs"] as const,
    list: (filters: unknown) => ["jobs", "list", filters] as const,
    detail: (id: string) => ["jobs", "detail", id] as const,
  },
  applications: {
    all: ["applications"] as const,
    mine: ["applications", "mine"] as const,
  },
  profile: ["profile"] as const,
};
