export interface AdminUserResponse {
  id: string;
  email: string;
  phone: string | null;
  fullName: string | null;
  roles: string[];
  isLockedOut: boolean;
  lockoutEnd: string | null;
  createdAt: string;
}

export interface LockUserRequest {
  reason: string;
}

export interface UpdateCompanyStatusRequest {
  status: string;
  note?: string;
}

export interface AuditLogResponse {
  id: string;
  userId: string | null;
  action: string;
  entityType: string | null;
  entityId: string | null;
  payloadJson: string | null;
  ipAddress: string | null;
  createdAt: string;
}

export interface UserQueryFilter {
  search?: string;
  role?: string;
  isLocked?: boolean;
  pageIndex?: number;
  pageSize?: number;
}

export interface CompanyQueryFilter {
  search?: string;
  status?: string;
  pageIndex?: number;
  pageSize?: number;
}

export interface AuditLogQueryFilter {
  userId?: string;
  action?: string;
  pageIndex?: number;
  pageSize?: number;
}

export interface PagedResult<T> {
  items: T[];
  totalCount: number;
  pageIndex: number;
  pageSize: number;
  totalPages: number;
}

export interface CompanyProfileResponse {
  id: string;
  userId: string;
  companyName: string;
  email: string;
  phoneNumber: string | null;
  website: string | null;
  address: string | null;
  companySize: string | null;
  industry: string | null;
  description: string | null;
  logoUrl: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface JobListResponse {
  id: string;
  companyId: string;
  companyName: string | null;
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
  approvalStatus: string;
  isActive: boolean;
  isExpired: boolean;
  viewCount: number;
  createdAt: string;
  requiredSkills: string[];
}

export interface AdminJobFilterRequest {
  search?: string;
  approvalStatus?: string;
  companyId?: string;
  pageIndex?: number;
  pageSize?: number;
}

export interface ApproveJobRequest {
  isApproved: boolean;
  rejectionReason?: string;
  note?: string;
}

export interface AdminUserStatsDto {
  totalUsers: number;
  totalCandidates: number;
  totalEmployers: number;
  lockedUsersCount: number;
  newUsersLast30Days: number;
}

export interface AdminCompanyStatsDto {
  totalCompanies: number;
  verifiedCompaniesCount: number;
  pendingVerificationCount: number;
  rejectedCompaniesCount: number;
}

export interface AdminJobStatsDto {
  totalJobs: number;
  activeJobsCount: number;
  pendingApprovalCount: number;
  rejectedJobsCount: number;
  bannedJobsCount: number;
  expiredJobsCount: number;
}

export interface AdminApplicationStatsDto {
  totalApplications: number;
  appliedCount: number;
  screeningCount: number;
  interviewCount: number;
  offerCount: number;
  hiredCount: number;
  rejectedCount: number;
  withdrawnCount: number;
}

export interface MonthlyTrendDto {
  month: string;
  newUsers: number;
  newJobs: number;
  newApplications: number;
}

export interface AdminDashboardStatsResponse {
  users: AdminUserStatsDto;
  companies: AdminCompanyStatsDto;
  jobs: AdminJobStatsDto;
  applications: AdminApplicationStatsDto;
  pendingReportsCount: number;
  monthlyTrends: MonthlyTrendDto[];
}
