// ============================================
// COMMON DTOs
// ============================================

export interface MessageDto {
  message: string;
}

export interface PaginationMeta {
  currentPage: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

// ============================================
// AUTH DTOs
// ============================================

export interface AuthResponseDto {
  accessToken: string;
  accessTokenExpiresAt?: string;
  refreshToken: string;
  role: "candidate" | "employer" | "admin";
  id?: string;
  email?: string;
  fullName?: string;
  user?: {
    id?: string;
    email?: string;
    fullName?: string;
  };
}

export interface LoginDto {
  email: string;
  password: string;
}

export interface RegisterCandidateDto {
  email: string;
  password: string;
  confirmPassword: string;
  fullName: string;
}

export interface RegisterEmployerDto {
  email: string;
  password: string;
  confirmPassword: string;
  fullName: string;
  gender?: string;
  phone?: string;
  companyName?: string;
  location?: string;
}

export interface ForgotPasswordDto {
  email: string;
}

export interface ResetPasswordDto {
  token: string;
  email: string;
  newPassword: string;
  confirmPassword: string;
}

export interface RefreshTokenDto {
  refreshToken: string;
}

export interface GoogleAuthDto {
  idToken: string;
}

// ============================================
// CANDIDATE DTOs
// ============================================

export interface CandidateProfileDto {
  id: string;
  userId: string;
  fullName: string;
  email: string;
  phone?: string;
  address?: string;
  dateOfBirth?: string;
  gender?: string;
  avatarUrl?: string;
  summary?: string;
  desiredPosition?: string;
  salaryMin?: number;
  salaryMax?: number;
  profileCompletionPercentage: number;
  createdAt: string;
  updatedAt: string;
}

export interface UpdateCandidateProfileDto {
  fullName?: string;
  phone?: string;
  address?: string;
  dateOfBirth?: string;
  gender?: string;
  summary?: string;
  desiredPosition?: string;
  salaryMin?: number;
  salaryMax?: number;
}

export interface CandidateCVDto {
  id: string;
  candidateId: string;
  title: string;
  fileUrl: string;
  isPrimary: boolean;
  uploadedAt: string;
}

export interface CreateCandidateCVDto {
  title: string;
  file: File;
}

export interface UpdateCandidateCVTitleDto {
  title: string;
}

export interface EducationDto {
  id: string;
  candidateId: string;
  schoolName: string;
  major?: string;
  degree?: string;
  startDate?: string;
  endDate?: string;
  description?: string;
}

export interface CreateEducationDto {
  schoolName: string;
  major?: string;
  degree?: string;
  startDate?: string;
  endDate?: string;
  description?: string;
}

export interface UpdateEducationDto extends CreateEducationDto {}

export interface ExperienceDto {
  id: string;
  candidateId: string;
  companyName: string;
  position: string;
  startDate?: string;
  endDate?: string;
  description?: string;
  isCurrent: boolean;
}

export interface CreateExperienceDto {
  companyName: string;
  position: string;
  startDate?: string;
  endDate?: string;
  description?: string;
  isCurrent?: boolean;
}

export interface UpdateExperienceDto extends CreateExperienceDto {}

export interface SkillDto {
  id: string;
  candidateId: string;
  skillName: string;
  proficiency?: string;
}

export interface CreateSkillDto {
  skillName: string;
  proficiency?: string;
}

export interface UpdateSkillDto extends CreateSkillDto {}

export interface CertificateDto {
  id: string;
  candidateId: string;
  name: string;
  issuingOrganization?: string;
  issueDate?: string;
  expiryDate?: string;
  credentialId?: string;
  credentialUrl?: string;
}

export interface CreateCertificateDto {
  name: string;
  issuingOrganization?: string;
  issueDate?: string;
  expiryDate?: string;
  credentialId?: string;
  credentialUrl?: string;
}

export interface UpdateCertificateDto extends CreateCertificateDto {}

export interface ProjectDto {
  id: string;
  candidateId: string;
  name: string;
  description?: string;
  startDate?: string;
  endDate?: string;
  projectUrl?: string;
  technologies?: string;
}

export interface CreateProjectDto {
  name: string;
  description?: string;
  startDate?: string;
  endDate?: string;
  projectUrl?: string;
  technologies?: string;
}

export interface UpdateProjectDto extends CreateProjectDto {}

// ============================================
// EMPLOYER DTOs
// ============================================

export interface EmployerProfileDto {
  id: string;
  userId: string;
  fullName: string;
  email: string;
  phone?: string;
  gender?: string;
  avatarUrl?: string;
  companyId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UpdateEmployerProfileDto {
  fullName?: string;
  phone?: string;
  gender?: string;
}

export interface CompanyDto {
  id: string;
  employerId: string;
  name: string;
  taxCode?: string;
  address?: string;
  website?: string;
  logo?: string;
  description?: string;
  industry?: string;
  companySize?: string;
  verifiedStatus: "NotVerified" | "Pending" | "Verified" | "Rejected";
  createdAt: string;
  updatedAt: string;
}

export interface CreateCompanyDto {
  name: string;
  taxCode?: string;
  address?: string;
  website?: string;
  description?: string;
  industry?: string;
  companySize?: string;
}

export interface UpdateCompanyDto extends CreateCompanyDto {}

// ============================================
// JOB DTOs
// ============================================

export interface JobDto {
  id: string;
  employerId: string;
  companyId?: string;
  title: string;
  description?: string;
  requirements?: string;
  benefits?: string;
  salaryMin?: number;
  salaryMax?: number;
  location?: string;
  jobCategoryId?: string;
  jobLevelId?: string;
  employmentTypeId?: string;
  deadline?: string;
  isActive: boolean;
  approvalStatus: "Draft" | "Pending" | "Approved" | "Rejected";
  postedAt?: string;
  createdAt: string;
  updatedAt: string;
  company?: CompanyDto;
  jobCategory?: JobCategoryDto;
  jobLevel?: JobLevelDto;
  employmentType?: EmploymentTypeDto;
  requiredSkills?: JobSkillDto[];
}

export interface CreateJobDto {
  title: string;
  description?: string;
  requirements?: string;
  benefits?: string;
  salaryMin?: number;
  salaryMax?: number;
  location?: string;
  jobCategoryId?: string;
  jobLevelId?: string;
  employmentTypeId?: string;
  deadline?: string;
  requiredSkillIds?: string[];
}

export interface UpdateJobDto extends CreateJobDto {}

export interface JobSearchParams {
  keyword?: string;
  jobCategoryId?: string;
  jobLevelId?: string;
  location?: string;
  employmentTypeId?: string;
  salaryMin?: number;
  salaryMax?: number;
  skillIds?: string[];
  page?: number;
  pageSize?: number;
}

// ============================================
// MASTER DATA DTOs
// ============================================

export interface JobCategoryDto {
  id: string;
  name: string;
  description?: string;
}

export interface JobLevelDto {
  id: string;
  name: string;
}

export interface EmploymentTypeDto {
  id: string;
  name: string;
}

export interface JobSkillDto {
  id: string;
  name: string;
  categoryId?: string;
  category?: string;
}

export interface LocationDto {
  id: string;
  name: string;
  code?: string;
}

// ============================================
// APPLICATION DTOs
// ============================================

export interface ApplicationDto {
  id: string;
  jobId: string;
  candidateId: string;
  cvId?: string;
  coverLetter?: string;
  status: "Pending" | "Reviewing" | "Shortlisted" | "Interviewed" | "Offered" | "Rejected" | "Withdrawn";
  appliedAt: string;
  updatedAt: string;
  job?: JobDto;
  candidate?: CandidateProfileDto;
}

export interface CreateApplicationDto {
  jobId: string;
  cvId?: string;
  coverLetter?: string;
}

export interface UpdateApplicationStatusDto {
  status: "Reviewing" | "Shortlisted" | "Interviewed" | "Offered" | "Rejected";
}

// ============================================
// ADMIN DTOs
// ============================================

export interface UserDto {
  id: string;
  email: string;
  fullName?: string;
  roles: string[];
  isLocked: boolean;
  createdAt: string;
  emailConfirmed: boolean;
}

export interface UserSearchParams {
  keyword?: string;
  role?: string;
  isLocked?: boolean;
  page?: number;
  pageSize?: number;
}

export interface UpdateCompanyVerificationDto {
  verifiedStatus: "Verified" | "Rejected";
  rejectionReason?: string;
}

export interface UpdateJobApprovalDto {
  approvalStatus: "Approved" | "Rejected";
  rejectionReason?: string;
}
