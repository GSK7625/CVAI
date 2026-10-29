import { fetcher } from "~/lib/fetcher";
import type {
  CandidateProfileDto,
  UpdateCandidateProfileDto,
  CandidateCVDto,
  CreateCandidateCVDto,
  UpdateCandidateCVTitleDto,
  EducationDto,
  CreateEducationDto,
  UpdateEducationDto,
  ExperienceDto,
  CreateExperienceDto,
  UpdateExperienceDto,
  SkillDto,
  CreateSkillDto,
  UpdateSkillDto,
  CertificateDto,
  CreateCertificateDto,
  UpdateCertificateDto,
  ProjectDto,
  CreateProjectDto,
  UpdateProjectDto,
  MessageDto,
} from "~/types/api";

// ============================================
// CANDIDATE PROFILE
// ============================================

export const candidateProfileApi = {
  getProfile: () =>
    fetcher<CandidateProfileDto>("/api/candidate/profile", { auth: true }),

  getFullProfile: () =>
    fetcher<{
      profile: CandidateProfileDto;
      educations: EducationDto[];
      experiences: ExperienceDto[];
      skills: SkillDto[];
      certificates: CertificateDto[];
      projects: ProjectDto[];
    }>("/api/candidate/profile/full", { auth: true }),

  updateProfile: (dto: UpdateCandidateProfileDto) =>
    fetcher<CandidateProfileDto>("/api/candidate/profile", {
      method: "PUT",
      body: dto,
      auth: true,
    }),

  uploadAvatar: (file: File) => {
    const formData = new FormData();
    formData.append("avatar", file);
    return fetcher<string>("/api/candidate/profile/avatar", {
      method: "POST",
      body: formData,
      auth: true,
    });
  },
};

// ============================================
// CANDIDATE CV
// ============================================

export const candidateCVApi = {
  getCVs: () =>
    fetcher<CandidateCVDto[]>("/api/candidate/cvs", { auth: true }),

  uploadCV: (dto: CreateCandidateCVDto) => {
    const formData = new FormData();
    formData.append("title", dto.title);
    formData.append("cv", dto.file);
    formData.append("file", dto.file);
    return fetcher<CandidateCVDto>(`/api/candidate/cvs?title=${encodeURIComponent(dto.title)}`, {
      method: "POST",
      body: formData,
      auth: true,
    });
  },

  updateCVTitle: (id: string, dto: UpdateCandidateCVTitleDto) =>
    fetcher<CandidateCVDto>(`/api/candidate/cvs/${id}/title`, {
      method: "PATCH",
      body: dto,
      auth: true,
    }),

  selectPrimaryCV: (id: string) =>
    fetcher<MessageDto>(`/api/candidate/cvs/${id}/select`, {
      method: "PUT",
      auth: true,
    }),

  deleteCV: (id: string) =>
    fetcher<void>(`/api/candidate/cvs/${id}`, {
      method: "DELETE",
      auth: true,
    }),
};

// ============================================
// EDUCATION
// ============================================

export const educationApi = {
  getAll: () =>
    fetcher<EducationDto[]>("/api/candidate/educations", { auth: true }),

  create: (dto: CreateEducationDto) =>
    fetcher<EducationDto>("/api/candidate/educations", {
      method: "POST",
      body: dto,
      auth: true,
    }),

  update: (id: string, dto: UpdateEducationDto) =>
    fetcher<EducationDto>(`/api/candidate/educations/${id}`, {
      method: "PUT",
      body: dto,
      auth: true,
    }),

  delete: (id: string) =>
    fetcher<void>(`/api/candidate/educations/${id}`, {
      method: "DELETE",
      auth: true,
    }),
};

// ============================================
// EXPERIENCE
// ============================================

export const experienceApi = {
  getAll: () =>
    fetcher<ExperienceDto[]>("/api/candidate/experiences", { auth: true }),

  create: (dto: CreateExperienceDto) =>
    fetcher<ExperienceDto>("/api/candidate/experiences", {
      method: "POST",
      body: dto,
      auth: true,
    }),

  update: (id: string, dto: UpdateExperienceDto) =>
    fetcher<ExperienceDto>(`/api/candidate/experiences/${id}`, {
      method: "PUT",
      body: dto,
      auth: true,
    }),

  delete: (id: string) =>
    fetcher<void>(`/api/candidate/experiences/${id}`, {
      method: "DELETE",
      auth: true,
    }),
};

// ============================================
// SKILLS
// ============================================

export const skillApi = {
  getAll: () =>
    fetcher<SkillDto[]>("/api/candidate/skills", { auth: true }),

  create: (dto: CreateSkillDto) =>
    fetcher<SkillDto>("/api/candidate/skills", {
      method: "POST",
      body: dto,
      auth: true,
    }),

  update: (id: string, dto: UpdateSkillDto) =>
    fetcher<SkillDto>(`/api/candidate/skills/${id}`, {
      method: "PUT",
      body: dto,
      auth: true,
    }),

  delete: (id: string) =>
    fetcher<void>(`/api/candidate/skills/${id}`, {
      method: "DELETE",
      auth: true,
    }),
};

// ============================================
// CERTIFICATES
// ============================================

export const certificateApi = {
  getAll: () =>
    fetcher<CertificateDto[]>("/api/candidate/certificates", { auth: true }),

  create: (dto: CreateCertificateDto) =>
    fetcher<CertificateDto>("/api/candidate/certificates", {
      method: "POST",
      body: dto,
      auth: true,
    }),

  update: (id: string, dto: UpdateCertificateDto) =>
    fetcher<CertificateDto>(`/api/candidate/certificates/${id}`, {
      method: "PUT",
      body: dto,
      auth: true,
    }),

  delete: (id: string) =>
    fetcher<void>(`/api/candidate/certificates/${id}`, {
      method: "DELETE",
      auth: true,
    }),
};

// ============================================
// PROJECTS
// ============================================

export const projectApi = {
  getAll: () =>
    fetcher<ProjectDto[]>("/api/candidate/projects", { auth: true }),

  create: (dto: CreateProjectDto) =>
    fetcher<ProjectDto>("/api/candidate/projects", {
      method: "POST",
      body: dto,
      auth: true,
    }),

  update: (id: string, dto: UpdateProjectDto) =>
    fetcher<ProjectDto>(`/api/candidate/projects/${id}`, {
      method: "PUT",
      body: dto,
      auth: true,
    }),

  delete: (id: string) =>
    fetcher<void>(`/api/candidate/projects/${id}`, {
      method: "DELETE",
      auth: true,
    }),
};
