export type ApprovalStatus = "Pending" | "Approved" | "Rejected";
export type ApplicationStatus = "Applied" | "Screening" | "Interview" | "Offer" | "Hired" | "Rejected" | "Withdrawn";
export type UpdatableApplicationStatus = Exclude<ApplicationStatus, "Withdrawn">;

export interface PagedResult<T> {
  items: T[];
  totalCount: number;
  pageIndex: number;
  pageSize: number;
  totalPages: number;
  hasPreviousPage: boolean;
  hasNextPage: boolean;
}

export interface EmployerProfile {
  id: string;
  userId: string;
  fullName: string;
  position: string | null;
  gender: string | null;
  phone: string | null;
  avatarUrl: string | null;
  companyId: string;
  createdAt: string;
}

export interface EmployerProfileInput {
  fullName: string;
  position: string;
  gender: string;
  phone: string;
}

export interface CompanyProfile {
  id: string;
  name: string;
  taxCode: string;
  logoUrl: string | null;
  scale: string | null;
  industry: string | null;
  websiteUrl: string | null;
  address: string | null;
  description: string | null;
  verifiedStatus: string;
  verifiedAt: string | null;
  createdAt: string;
}

export interface CompanyProfileInput {
  name: string;
  taxCode?: string;
  scale: string;
  industry: string;
  websiteUrl: string;
  address: string;
  description: string;
}

export interface LookupOption {
  id: string;
  name: string;
  parentId?: string | null;
}

export interface SkillOption {
  id: string;
  name: string;
  category: string | null;
}

export interface JobSkillInput {
  skillId: string;
  isRequired: boolean;
}

export interface JobSkill extends JobSkillInput {
  skillName: string;
  category: string | null;
}

export interface JobCompany {
  id: string;
  name: string;
  logoUrl: string | null;
  address: string | null;
  industry: string | null;
  scale: string | null;
  verifiedStatus: string;
}

export interface JobSummary {
  id: string;
  companyId: string;
  companyName: string;
  companyLogoUrl: string | null;
  title: string;
  categoryName: string | null;
  levelName: string | null;
  employmentTypeName: string | null;
  locationName: string | null;
  salaryMin: number | null;
  salaryMax: number | null;
  salaryCurrency: string;
  experienceYearsMin: number | null;
  experienceYearsMax: number | null;
  deadline: string | null;
  positionsCount: number;
  approvalStatus: ApprovalStatus;
  isActive: boolean;
  isExpired: boolean;
  viewCount: number;
  createdAt: string;
  requiredSkills: string[];
}

export interface JobDetail extends Omit<JobSummary, "companyName" | "companyLogoUrl" | "requiredSkills"> {
  company: JobCompany;
  postedById: string;
  description: string;
  requirements: string | null;
  benefits: string | null;
  categoryId: string | null;
  levelId: string | null;
  employmentTypeId: string | null;
  locationId: string | null;
  updatedAt: string | null;
  skills: JobSkill[];
}

export interface EmployerJobFilters {
  keyword?: string;
  approvalStatus?: ApprovalStatus | "";
  isActive?: boolean;
  pageIndex?: number;
  pageSize?: number;
}

export interface JobRequest {
  title: string;
  description: string;
  requirements: string | null;
  benefits: string | null;
  categoryId: string | null;
  levelId: string | null;
  employmentTypeId: string | null;
  locationId: string | null;
  salaryMin: number | null;
  salaryMax: number | null;
  salaryCurrency: string;
  experienceYearsMin: number | null;
  experienceYearsMax: number | null;
  deadline: string | null;
  positionsCount: number;
  skills: JobSkillInput[];
}

export interface JobFormValues {
  title: string;
  description: string;
  requirements: string;
  benefits: string;
  categoryId: string;
  levelId: string;
  employmentTypeId: string;
  locationId: string;
  salaryMin: string;
  salaryMax: string;
  salaryCurrency: string;
  experienceYearsMin: string;
  experienceYearsMax: string;
  deadline: string;
  positionsCount: string;
  skills: JobSkillInput[];
}

export interface HrMasterData {
  categories: LookupOption[];
  levels: LookupOption[];
  employmentTypes: LookupOption[];
  locations: LookupOption[];
  skills: SkillOption[];
}

export interface RecruiterApplicationFilters {
  status?: ApplicationStatus | "";
  minRating?: number;
  keyword?: string;
  pageIndex?: number;
  pageSize?: number;
}

export interface RecruiterApplicationSummary {
  id: string;
  candidateId: string;
  candidateFullName: string;
  candidateAvatarUrl: string | null;
  candidatePhone: string | null;
  candidateEmail: string | null;
  cvId: string;
  cvTitle: string | null;
  cvFileUrl: string | null;
  status: ApplicationStatus;
  rating: number | null;
  evaluationLabel: string | null;
  matchScore: number | null;
  appliedAt: string;
}

export interface ApplicationTimelineItem {
  fromStatus: ApplicationStatus | null;
  toStatus: ApplicationStatus;
  reason: string | null;
  changedAt: string;
}

export interface RecruiterApplicationDetail extends RecruiterApplicationSummary {
  jobId: string;
  jobTitle: string;
  candidateAddress: string | null;
  coverLetter: string | null;
  privateNotes: string | null;
  matchExplanation: string | null;
  matchedSkills: string[];
  missingSkills: string[];
  timeline: ApplicationTimelineItem[];
}

export interface UpdateApplicationStatusRequest {
  newStatus: UpdatableApplicationStatus;
  reason: string | null;
}

export interface PipelineCandidate {
  applicationId: string;
  candidateId: string;
  candidateFullName: string;
  candidateAvatarUrl: string | null;
  rating: number | null;
  evaluationLabel: string | null;
  matchScore: number | null;
  appliedAt: string;
  cvFileUrl: string | null;
  daysInStage?: number;
  stageAlert?: "Normal" | "Warning" | "Critical";
  lastStatusChangedAt?: string | null;
}

export interface PipelineStage {
  stage: UpdatableApplicationStatus;
  count: number;
  candidates: PipelineCandidate[];
}

export interface RecruitmentPipeline {
  jobId: string;
  jobTitle: string;
  totalCandidates: number;
  stages: PipelineStage[];
}
