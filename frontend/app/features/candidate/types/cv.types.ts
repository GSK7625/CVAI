/**
 * @file cv.types.ts
 * @description TypeScript DTOs cho CV Management (FC-82).
 * Đối soát trực tiếp với StructuredCvDtos.cs và CandidateProfileController.cs.
 */

// ── CV Core Response ─────────────────────────────────────────────────────────

export interface CvResponse {
  id: string;
  candidateId: string;
  title?: string | null;
  fileUrl?: string | null;
  fileType?: string | null;
  fileSizeBytes?: number | null;
  isPrimary: boolean;
  uploadedAt: string;
  /** "Upload" | "Built" — nguồn tạo CV */
  source?: string | null;
  /** "Pending" | "Parsed" | "Failed" */
  parseStatus?: string | null;
  isVerifiedByUser?: boolean;
}

export interface UpdateCvTitleRequest {
  title: string;
}

// ── CV Analysis (Rule-based, GET /cvs/{id}/analysis) ─────────────────────────

export interface CvAnalysisResponse {
  cvId: string;
  cvScore: number;
  strengths: string[];
  weaknesses: string[];
  improvements: string[];
  missingSkills: string[];
  modelVersion: string;
  generatedAt: string;
}

// ── Structured CV Data (GET/PUT /cvs/{id}/structured-data) ───────────────────

export interface CvExperienceDto {
  companyName: string;
  position?: string | null;
  startDate: string; // DateOnly ISO: YYYY-MM-DD
  endDate?: string | null;
  isCurrent: boolean;
  description?: string | null;
}

export interface CvEducationDto {
  school: string;
  degree?: string | null;
  major?: string | null;
  startYear?: number | null;
  endYear?: number | null;
  description?: string | null;
}

export interface CvProjectDto {
  name: string;
  role?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  isCurrent: boolean;
  description?: string | null;
  technologies?: string | null;
}

export interface StructuredCvDataDto {
  fullName: string;
  email?: string | null;
  phone?: string | null;
  summary?: string | null;
  skills: string[];
  experiences: CvExperienceDto[];
  educations: CvEducationDto[];
  projects: CvProjectDto[];
}

export interface CvStructuredDataResponse {
  cvId: string;
  title?: string | null;
  fileUrl?: string | null;
  parseStatus: "Pending" | "Parsed" | "Failed" | string;
  isVerifiedByUser: boolean;
  verifiedAt?: string | null;
  data: StructuredCvDataDto;
  rawText?: string | null;
}

export interface UpdateStructuredCvDataRequest {
  data: StructuredCvDataDto;
}

// ── Badge helpers ─────────────────────────────────────────────────────────────

export type CvParseStatus = "Pending" | "Parsed" | "Failed";
