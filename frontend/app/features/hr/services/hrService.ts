import { ApiError, fetcher } from "~/lib/fetcher";
import { buildEmployerJobsQuery, buildRecruiterApplicationsQuery } from "../contracts/hrContracts";
import type {
  CompanyProfile,
  CompanyProfileInput,
  EmployerJobFilters,
  EmployerProfile,
  EmployerProfileInput,
  HrMasterData,
  JobDetail,
  JobRequest,
  JobSummary,
  LookupOption,
  PagedResult,
  RecruiterApplicationDetail,
  RecruiterApplicationFilters,
  RecruiterApplicationSummary,
  RecruitmentPipeline,
  SkillOption,
  UpdateApplicationStatusRequest,
} from "../types";

function compactOptional(value: string): string | null {
  const normalized = value.trim();
  return normalized || null;
}

export const hrService = {
  getProfile(signal?: AbortSignal) {
    return fetcher<EmployerProfile>("/api/employer/profile", { method: "GET", auth: true, signal });
  },

  updateProfile(input: EmployerProfileInput) {
    return fetcher<EmployerProfile>("/api/employer/profile", {
      method: "PUT",
      auth: true,
      body: {
        fullName: input.fullName.trim(),
        position: compactOptional(input.position),
        gender: compactOptional(input.gender),
        phone: compactOptional(input.phone),
      },
    });
  },

  uploadAvatar(file: File) {
    const body = new FormData();
    body.append("avatar", file);
    return fetcher<string>("/api/employer/profile/avatar", { method: "POST", auth: true, body });
  },

  async getCompany(signal?: AbortSignal): Promise<CompanyProfile | null> {
    try {
      return await fetcher<CompanyProfile>("/api/employer/company", { method: "GET", auth: true, signal });
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }
  },

  createCompany(input: CompanyProfileInput) {
    return fetcher<CompanyProfile>("/api/employer/company", {
      method: "POST",
      auth: true,
      body: {
        name: input.name.trim(),
        taxCode: (input.taxCode || ("TAX_" + Date.now())).trim(),
        scale: compactOptional(input.scale),
        industry: compactOptional(input.industry),
        websiteUrl: compactOptional(input.websiteUrl),
        address: compactOptional(input.address),
        description: compactOptional(input.description),
      },
    });
  },

  updateCompany(input: CompanyProfileInput) {
    return fetcher<CompanyProfile>("/api/employer/company", {
      method: "PUT",
      auth: true,
      body: {
        name: input.name.trim(),
        scale: compactOptional(input.scale),
        industry: compactOptional(input.industry),
        websiteUrl: compactOptional(input.websiteUrl),
        address: compactOptional(input.address),
        description: compactOptional(input.description),
      },
    });
  },

  uploadCompanyLogo(file: File) {
    const body = new FormData();
    body.append("logo", file);
    return fetcher<CompanyProfile>("/api/employer/company/logo", { method: "POST", auth: true, body });
  },

  getJobs(filters: EmployerJobFilters, signal?: AbortSignal) {
    return fetcher<PagedResult<JobSummary>>(`/api/employer/jobs${buildEmployerJobsQuery(filters)}`, {
      method: "GET",
      auth: true,
      signal,
    });
  },

  getJob(id: string, signal?: AbortSignal) {
    return fetcher<JobDetail>(`/api/employer/jobs/${id}`, { method: "GET", auth: true, signal });
  },

  createJob(input: JobRequest) {
    return fetcher<JobDetail>("/api/employer/jobs", { method: "POST", auth: true, body: input });
  },

  updateJob(id: string, input: JobRequest) {
    return fetcher<JobDetail>(`/api/employer/jobs/${id}`, { method: "PUT", auth: true, body: input });
  },

  toggleJobStatus(id: string) {
    return fetcher<boolean>(`/api/employer/jobs/${id}/status`, { method: "PATCH", auth: true });
  },

  deleteJob(id: string) {
    return fetcher<boolean>(`/api/employer/jobs/${id}`, { method: "DELETE", auth: true });
  },

  async getMasterData(signal?: AbortSignal): Promise<HrMasterData> {
    const [categories, levels, employmentTypes, locations, skills] = await Promise.all([
      fetcher<LookupOption[]>("/api/jobs/categories", { method: "GET", signal }),
      fetcher<LookupOption[]>("/api/jobs/levels", { method: "GET", signal }),
      fetcher<LookupOption[]>("/api/jobs/employment-types", { method: "GET", signal }),
      fetcher<LookupOption[]>("/api/jobs/locations", { method: "GET", signal }),
      fetcher<SkillOption[]>("/api/skills", { method: "GET", signal }),
    ]);
    return { categories, levels, employmentTypes, locations, skills };
  },

  getJobApplications(jobId: string, filters: RecruiterApplicationFilters, signal?: AbortSignal) {
    return fetcher<PagedResult<RecruiterApplicationSummary>>(
      `/api/employer/jobs/${jobId}/applications${buildRecruiterApplicationsQuery(filters)}`,
      { method: "GET", auth: true, signal },
    );
  },

  getApplication(id: string, signal?: AbortSignal) {
    return fetcher<RecruiterApplicationDetail>(`/api/employer/applications/${id}`, {
      method: "GET",
      auth: true,
      signal,
    });
  },

  updateApplicationStatus(id: string, input: UpdateApplicationStatusRequest) {
    return fetcher<boolean>(`/api/employer/applications/${id}/status`, {
      method: "PATCH",
      auth: true,
      body: input,
    });
  },

  getRecruitmentPipeline(jobId: string, signal?: AbortSignal) {
    return fetcher<RecruitmentPipeline>(`/api/employer/jobs/${jobId}/pipeline`, {
      method: "GET",
      auth: true,
      signal,
    });
  },
};
