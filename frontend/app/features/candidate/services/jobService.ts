/**
 * @file jobService.ts
 * @description Candidate Job Service: Giao tiếp API việc làm cho ứng viên (list, detail, master data, similar).
 * @architecture Tuân thủ ISP (IJobService) & DIP (fallback adapter có điều kiện cho dev).
 */

import { fetcher } from "~/lib/fetcher";
import type {
  ApiJobDetail,
  ApiJobListItem,
  ApiPaged,
  ApplyJobRequest,
  ApplyJobResponse,
  JobMatchPreviewResponse,
  Job,
  JobFilters,
  JobListResult,
  JobMasterData,
  LookupOption,
} from "../types";
import { DEMO_JOBS, filterDemoJobs, DEMO_MASTER_DATA } from "../mocks/jobs.mock";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export { DEMO_JOBS, DEMO_MASTER_DATA };

export interface IJobService {
  list(filters: JobFilters, signal?: AbortSignal): Promise<JobListResult>;
  detail(id: string, signal?: AbortSignal): Promise<Job>;
  apply(jobId: string, req: ApplyJobRequest): Promise<ApplyJobResponse>;
  previewMatch(jobId: string, cvId?: string, signal?: AbortSignal): Promise<JobMatchPreviewResponse>;
  similar(id: string, categoryId?: string, signal?: AbortSignal): Promise<Job[]>;
  getMasterData(signal?: AbortSignal): Promise<JobMasterData>;
}

/**
 * Điều hướng mock chủ động qua biến môi trường VITE_USE_MOCK:
 * - VITE_USE_MOCK=true: trả mock data ngay lập tức
 * - VITE_USE_MOCK=false hoặc thiếu: gọi API thật, lỗi hiển thị nguyên vẹn
 */
async function withDevFallback<T>(
  apiCall: () => Promise<T>,
  fallback: () => T | Promise<T>,
): Promise<T> {
  return USE_MOCK ? fallback() : apiCall();
}

const toMillions = (vnd: number) => Math.round((vnd / 1_000_000) * 10) / 10;

const expLabel = (min: number | null, max: number | null) => {
  if (min == null && max == null) return "Không yêu cầu";
  if (min != null && max != null) return `${min} - ${max} năm`;
  if (min != null) return `${min}+ năm`;
  return `Dưới ${max} năm`;
};

const isRecent = (dateStr: string, days = 3) => {
  const diff = Date.now() - new Date(dateStr).getTime();
  return diff >= 0 && diff <= days * 24 * 60 * 60 * 1000;
};

export function mapJobListItem(j: ApiJobListItem): Job {
  return {
    id: j.id,
    companyId: j.companyId,
    title: j.title,
    company: j.companyName,
    companyLogo: j.companyLogoUrl ?? undefined,
    location: j.locationName ?? "Toàn quốc",
    salaryMin: j.salaryMin != null ? toMillions(j.salaryMin) : null,
    salaryMax: j.salaryMax != null ? toMillions(j.salaryMax) : null,
    salaryRawMin: j.salaryMin,
    salaryRawMax: j.salaryMax,
    jobType: j.employmentTypeName ?? "",
    experience: expLabel(j.experienceYearsMin, j.experienceYearsMax),
    experienceYearsMin: j.experienceYearsMin,
    experienceYearsMax: j.experienceYearsMax,
    categories: j.categoryName ? [j.categoryName] : [],
    categoryName: j.categoryName ?? undefined,
    level: j.levelName ?? undefined,
    postedAt: j.createdAt,
    deadline: j.deadline ?? undefined,
    quantity: j.positionsCount ? `${j.positionsCount} người` : undefined,
    hot: isRecent(j.createdAt, 3),
    skills: j.requiredSkills ?? [],
    viewCount: j.viewCount,
  };
}

export function mapJobDetail(j: ApiJobDetail): Job {
  const reqList = j.requirements
    ? j.requirements
        .split(/\r?\n/)
        .map((s) => s.trim().replace(/^[-*•]\s*/, ""))
        .filter(Boolean)
    : [];

  const benList = j.benefits
    ? j.benefits
        .split(/\r?\n/)
        .map((s) => s.trim().replace(/^[-*•]\s*/, ""))
        .filter(Boolean)
    : [];

  const descList = j.description
    ? j.description
        .split(/\r?\n/)
        .map((s) => s.trim().replace(/^[-*•]\s*/, ""))
        .filter(Boolean)
    : [];

  return {
    id: j.id,
    companyId: j.companyId,
    title: j.title,
    company: j.company?.name ?? "",
    companyLogo: j.company?.logoUrl ?? undefined,
    companyIndustry: j.company?.industry ?? undefined,
    companySize: j.company?.scale ?? undefined,
    workAddress: j.company?.address ?? undefined,
    verified: j.company?.verifiedStatus?.toLowerCase() === "verified",
    location: j.locationName ?? "Toàn quốc",
    locationId: j.locationId ?? undefined,
    salaryMin: j.salaryMin != null ? toMillions(j.salaryMin) : null,
    salaryMax: j.salaryMax != null ? toMillions(j.salaryMax) : null,
    salaryRawMin: j.salaryMin,
    salaryRawMax: j.salaryMax,
    salaryCurrency: j.salaryCurrency ?? "VND",
    jobType: j.employmentTypeName ?? "",
    employmentTypeId: j.employmentTypeId ?? undefined,
    experience: expLabel(j.experienceYearsMin, j.experienceYearsMax),
    experienceYearsMin: j.experienceYearsMin,
    experienceYearsMax: j.experienceYearsMax,
    categories: j.categoryName ? [j.categoryName] : [],
    categoryId: j.categoryId ?? undefined,
    categoryName: j.categoryName ?? undefined,
    level: j.levelName ?? undefined,
    levelId: j.levelId ?? undefined,
    postedAt: j.createdAt,
    deadline: j.deadline ?? undefined,
    quantity: j.positionsCount ? `${j.positionsCount} người` : undefined,
    hot: isRecent(j.createdAt, 3),
    description: j.description,
    descriptionList: descList,
    requirements: reqList,
    requirementsText: j.requirements ?? "",
    benefits: benList,
    benefitsText: j.benefits ?? "",
    skills: j.skills?.map((s) => s.skillName) ?? [],
    viewCount: j.viewCount,
  };
}

function buildJobQueryParams(filters: JobFilters): string {
  const params = new URLSearchParams();

  if (filters.keyword?.trim()) {
    params.set("keyword", filters.keyword.trim());
  }
  if (filters.categoryId) {
    params.set("categoryId", filters.categoryId);
  }
  if (filters.levelId) {
    params.set("levelId", filters.levelId);
  }
  if (filters.employmentTypeId) {
    params.set("employmentTypeId", filters.employmentTypeId);
  }
  if (filters.locationId) {
    params.set("locationId", filters.locationId);
  }
  if (filters.salaryMin != null) {
    params.set("salaryMin", String(filters.salaryMin));
  }
  if (filters.salaryMax != null) {
    params.set("salaryMax", String(filters.salaryMax));
  }
  if (filters.sortBy) {
    params.set("sortBy", filters.sortBy);
  }
  if (filters.page != null) {
    params.set("pageIndex", String(filters.page));
  }
  if (filters.pageSize != null) {
    params.set("pageSize", String(filters.pageSize));
  }

  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function jobService(): IJobService {
  return {
    list: async (filters, signal) => {
      const queryStr = buildJobQueryParams(filters);
      return withDevFallback<JobListResult>(
        async () => {
          const res = await fetcher<ApiPaged<ApiJobListItem>>(`/api/jobs${queryStr}`, {
            method: "GET",
            signal,
          });
          return {
            items: res.items.map(mapJobListItem),
            total: res.totalCount,
            page: res.pageIndex,
            pageSize: res.pageSize,
            totalPages: res.totalPages,
            hasPreviousPage: res.hasPreviousPage,
            hasNextPage: res.hasNextPage,
            isDemoFallback: false,
          };
        },
        () => {
          const fallbackRes = filterDemoJobs(filters);
          return {
            ...fallbackRes,
            isDemoFallback: true,
          };
        },
      );
    },

    detail: (id, signal) =>
      withDevFallback<Job>(
        async () => {
          const res = await fetcher<ApiJobDetail>(`/api/jobs/${id}`, {
            method: "GET",
            signal,
          });
          return { ...mapJobDetail(res), isDemoFallback: false };
        },
        () => {
          const found = DEMO_JOBS.find((j) => String(j.id) === String(id));
          return { ...(found ?? DEMO_JOBS[0]), isDemoFallback: true };
        },
      ),

    // ❌ KHÔNG fallback cho mutation ghi dữ liệu — thất bại phải báo lỗi thật.
    apply: (jobId, req) =>
      fetcher<ApplyJobResponse>(`/api/candidate/jobs/${jobId}/apply`, {
        method: "POST",
        body: req,
        auth: true,
      }),

    previewMatch: (jobId, cvId, signal) =>
      fetcher<JobMatchPreviewResponse>(`/api/candidate/jobs/${jobId}/preview-match`, {
        method: "POST",
        body: { cvId: cvId || null },
        auth: true,
        signal,
      }),

    similar: async (id, categoryId, signal) =>
      withDevFallback(
        async () => {
          const params = new URLSearchParams();
          if (categoryId) params.set("categoryId", categoryId);
          params.set("pageSize", "4");
          const res = await fetcher<ApiPaged<ApiJobListItem>>(`/api/jobs?${params}`, {
            method: "GET",
            signal,
          });
          return res.items
            .filter((j) => String(j.id) !== String(id))
            .slice(0, 3)
            .map(mapJobListItem);
        },
        () =>
          DEMO_JOBS.filter((j) => String(j.id) !== String(id))
            .slice(0, 3)
            .map((j) => ({ ...j, isDemoFallback: true })),
      ),

    getMasterData: (signal) =>
      withDevFallback<JobMasterData>(
        async () => {
          const [categories, levels, employmentTypes, locations] = await Promise.all([
            fetcher<LookupOption[]>("/api/jobs/categories", { method: "GET", signal }),
            fetcher<LookupOption[]>("/api/jobs/levels", { method: "GET", signal }),
            fetcher<LookupOption[]>("/api/jobs/employment-types", { method: "GET", signal }),
            fetcher<LookupOption[]>("/api/jobs/locations", { method: "GET", signal }),
          ]);
          return { categories, levels, employmentTypes, locations, isDemoFallback: false };
        },
        () => ({ ...DEMO_MASTER_DATA, isDemoFallback: true }),
      ),
  };
}
