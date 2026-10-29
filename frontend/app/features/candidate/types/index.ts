/**
 * @file index.ts
 * @description Candidate Domain Types & Backend API DTOs.
 */

export interface ApiPaged<T> {
  items: T[];
  totalCount: number;
  pageIndex: number;
  pageSize: number;
  totalPages: number;
  hasPreviousPage: boolean;
  hasNextPage: boolean;
}

export interface ApiJobListItem {
  id: string;
  companyId: string;
  companyName: string;
  companyLogoUrl?: string | null;
  title: string;
  categoryName?: string | null;
  levelName?: string | null;
  employmentTypeName?: string | null;
  locationName?: string | null;
  salaryMin: number | null;
  salaryMax: number | null;
  experienceYearsMin: number | null;
  experienceYearsMax: number | null;
  deadline: string | null;
  positionsCount: number;
  approvalStatus: string;
  isActive: boolean;
  isExpired: boolean;
  viewCount: number;
  createdAt: string;
  requiredSkills: string[];
}

export interface ApiJobCompany {
  id: string;
  name: string;
  logoUrl?: string | null;
  address?: string | null;
  industry?: string | null;
  scale?: string | null;
  verifiedStatus: string;
}

export interface ApiJobSkill {
  skillId: string;
  skillName: string;
  category?: string | null;
  isRequired: boolean;
}

export interface ApiJobDetail {
  id: string;
  companyId: string;
  company: ApiJobCompany;
  postedById: string;
  title: string;
  description: string;
  requirements?: string | null;
  benefits?: string | null;
  categoryId?: string | null;
  categoryName?: string | null;
  levelId?: string | null;
  levelName?: string | null;
  employmentTypeId?: string | null;
  employmentTypeName?: string | null;
  locationId?: string | null;
  locationName?: string | null;
  salaryMin: number | null;
  salaryMax: number | null;
  salaryCurrency: string;
  experienceYearsMin: number | null;
  experienceYearsMax: number | null;
  deadline: string | null;
  positionsCount: number;
  approvalStatus: string;
  isActive: boolean;
  isExpired: boolean;
  viewCount: number;
  createdAt: string;
  updatedAt?: string | null;
  skills: ApiJobSkill[];
}

export interface LookupOption {
  id: string;
  name: string;
}

export interface JobMasterData {
  categories: LookupOption[];
  levels: LookupOption[];
  employmentTypes: LookupOption[];
  locations: LookupOption[];
  isDemoFallback?: boolean;
}

export interface Job {
  id: string;
  companyId?: string;
  title: string;
  company: string;
  companyLogo?: string;
  location: string;
  locationId?: string;
  salaryMin?: number | null; // In Millions VND for UI presentation
  salaryMax?: number | null; // In Millions VND for UI presentation
  salaryRawMin?: number | null; // In raw VND
  salaryRawMax?: number | null; // In raw VND
  salaryText?: string;
  salaryCurrency?: string;
  jobType: string;
  employmentTypeId?: string;
  experience: string;
  experienceYearsMin?: number | null;
  experienceYearsMax?: number | null;
  categories: string[];
  categoryId?: string;
  categoryName?: string;
  level?: string;
  levelId?: string;
  postedAt: string;
  hot?: boolean;
  verified?: boolean;
  deadline?: string;
  quantity?: string;
  gender?: string;
  workAddress?: string;
  companyWebsite?: string;
  companySize?: string;
  companyIndustry?: string;
  matchRate?: number;
  description?: string;
  descriptionList?: string[];
  requirements?: string[];
  requirementsText?: string;
  benefits?: string[];
  benefitsText?: string;
  skills?: string[];
  viewCount?: number;
  isDemoFallback?: boolean;
}

export interface JobFilters {
  keyword?: string;
  categoryId?: string;
  levelId?: string;
  employmentTypeId?: string;
  locationId?: string;
  salaryMin?: number; // Raw VND or mapped when building params
  salaryMax?: number; // Raw VND
  sortBy?: "newest" | "salary_desc" | "deadline" | string;
  page?: number;
  pageSize?: number;
}

export interface JobListResult {
  items: Job[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  isDemoFallback?: boolean;
}

export interface ApplicationDto {
  jobId: string;
  fullName: string;
  email: string;
  phone: string;
  coverLetter?: string;
  cvFileName?: string;
}

// -----------------------------------------------------------------------------
// Saved Jobs (P3-UC04) — map SavedJobResponse từ /api/candidate/saved-jobs
// -----------------------------------------------------------------------------

export interface ApiSavedJob {
  jobId: string;
  title: string;
  companyId: string;
  companyName: string;
  companyLogoUrl?: string | null;
  locationName?: string | null;
  salaryMin: number | null;
  salaryMax: number | null;
  salaryCurrency: string;
  deadline?: string | null;
  isActive: boolean;
  isExpired: boolean;
  savedAt: string;
}

/**
 * Model hiển thị cho hàng "Việc làm đã lưu".
 * salaryMin/salaryMax đã quy đổi sang TRIỆU ( khớp Job để dùng lại formatSalary).
 */
export interface SavedJob {
  jobId: string;
  title: string;
  company: string;
  companyLogo?: string;
  location: string;
  salaryMin?: number | null;
  salaryMax?: number | null;
  deadline?: string;
  isActive: boolean;
  isExpired: boolean;
  savedAt: string;
}

export interface SavedJobsResult {
  items: SavedJob[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasPreviousPage: boolean;
  hasNextPage: boolean;
}

// -----------------------------------------------------------------------------
// Candidate CV (P3-UC01, P3-UC05) — Re-export toàn bộ CV DTOs từ cv.types.ts
// -----------------------------------------------------------------------------
export * from "./cv.types";

// -----------------------------------------------------------------------------
// Candidate Applications & Match Preview (P3-UC05, P3-UC06, P3-UC07, P4-UC01)
// -----------------------------------------------------------------------------

export type CandidateApplicationStatus =
  | "Applied"
  | "Screening"
  | "Interview"
  | "Offer"
  | "Hired"
  | "Rejected"
  | "Withdrawn";

export const CAN_WITHDRAW_STATUSES = ["Applied", "Screening"] as const;

export interface ApplyJobRequest {
  cvId: string;
  coverLetter?: string | null;
}

export interface ApplyJobResponse {
  applicationId: string;
  jobId: string;
  jobTitle: string;
  status: string;
  matchScore: number | null;
  appliedAt: string;
}

export interface MatchStrengthItem {
  item: string;
  statement: string;
  evidence_source: "cv.skills" | "cv.technologies" | "cv.projects";
  evidence_text?: string | null;
}

export interface MatchGapItem {
  requirement: string;
  statement: string;
}

export interface MatchExplanationDetails {
  summary: string;
  strengths?: MatchStrengthItem[];
  gaps?: MatchGapItem[];
  recommendations?: string[];
}

export interface JobMatchPreviewResponse {
  jobId: string;
  jobTitle: string;
  cvId: string;
  cvTitle: string;
  matchScore: number;
  matchedSkills: string[];
  missingSkills: string[];
  explanation: string;
  locationMatched: boolean;
  salaryMatched: boolean;
  experienceComparison?: string | null;
  educationComparison?: string | null;
  projectDomainRelevance?: string | null;
  isAiPreview?: boolean | null;
  matchSource?: string | null;
  explanationDetails?: MatchExplanationDetails | null;
}


export interface ApiTimelineItem {
  fromStatus: string | null;
  toStatus: string;
  reason?: string | null;
  changedAt: string;
}

export interface ApiApplicationListItem {
  id: string;
  jobId: string;
  jobTitle: string;
  companyId: string;
  companyName: string;
  companyLogoUrl?: string | null;
  locationName?: string | null;
  salaryMin: number | null;
  salaryMax: number | null;
  salaryCurrency: string;
  status: CandidateApplicationStatus | string;
  matchScore: number | null;
  appliedAt: string;
  updatedAt?: string | null;
}

export interface ApplicationListItem {
  id: string;
  jobId: string;
  jobTitle: string;
  companyId: string;
  companyName: string;
  companyLogo?: string;
  location: string;
  salaryMin?: number | null;
  salaryMax?: number | null;
  status: CandidateApplicationStatus | string;
  matchScore?: number | null;
  appliedAt: string;
  updatedAt?: string | null;
}

export interface ApiApplicationDetail {
  id: string;
  jobId: string;
  jobTitle: string;
  companyId: string;
  companyName: string;
  companyLogoUrl?: string | null;
  cvId: string;
  cvTitle?: string | null;
  cvFileUrl?: string | null;
  coverLetter?: string | null;
  status: CandidateApplicationStatus | string;
  matchScore?: number | null;
  matchExplanation?: string | null;
  matchedSkills: string[];
  missingSkills: string[];
  appliedAt: string;
  timeline: ApiTimelineItem[];
}

export interface ApplicationFilters {
  status?: string;
  page?: number;
  pageSize?: number;
}

export interface ApplicationListResult {
  items: ApplicationListItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasPreviousPage: boolean;
  hasNextPage: boolean;
}

