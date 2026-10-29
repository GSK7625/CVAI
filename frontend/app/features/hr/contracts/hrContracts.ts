import type {
  CompanyProfileInput,
  EmployerJobFilters,
  EmployerProfileInput,
  JobFormValues,
  JobRequest,
  RecruiterApplicationFilters,
  UpdateApplicationStatusRequest,
  UpdatableApplicationStatus,
} from "../types/index.ts";

export type FieldErrors<T> = Partial<Record<keyof T, string>>;

export function buildEmployerJobsQuery(filters: EmployerJobFilters): string {
  const params = new URLSearchParams();
  if (filters.keyword?.trim()) params.set("Keyword", filters.keyword.trim());
  if (filters.approvalStatus) params.set("ApprovalStatus", filters.approvalStatus);
  if (filters.isActive !== undefined) params.set("IsActive", String(filters.isActive));
  params.set("PageIndex", String(filters.pageIndex ?? 1));
  params.set("PageSize", String(filters.pageSize ?? 10));
  return `?${params.toString()}`;
}

export function buildRecruiterApplicationsQuery(filters: RecruiterApplicationFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set("Status", filters.status);
  if (filters.keyword?.trim()) params.set("Keyword", filters.keyword.trim());
  params.set("PageIndex", String(filters.pageIndex ?? 1));
  params.set("PageSize", String(filters.pageSize ?? 10));
  return `?${params.toString()}`;
}

export function toStatusUpdateRequest(
  newStatus: UpdatableApplicationStatus,
  reason: string,
): UpdateApplicationStatusRequest {
  return { newStatus, reason: optionalText(reason) };
}

export function validateStatusReason(reason: string): string | undefined {
  return reason.trim().length > 500 ? "Lý do không được vượt quá 500 ký tự." : undefined;
}

export function toSafeDocumentUrl(value: string | null | undefined): string | null {
  const normalized = value?.trim();
  if (!normalized) return null;
  if (normalized.startsWith("/") && !normalized.startsWith("//")) return normalized;
  try {
    const url = new URL(normalized);
    return url.protocol === "http:" || url.protocol === "https:" ? normalized : null;
  } catch {
    return null;
  }
}

function optionalNumber(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

function optionalText(value: string): string | null {
  const normalized = value.trim();
  return normalized === "" ? null : normalized;
}

export function toJobRequest(values: JobFormValues): JobRequest {
  return {
    title: values.title.trim(),
    description: values.description.trim(),
    requirements: optionalText(values.requirements),
    benefits: optionalText(values.benefits),
    categoryId: optionalText(values.categoryId),
    levelId: optionalText(values.levelId),
    employmentTypeId: optionalText(values.employmentTypeId),
    locationId: optionalText(values.locationId),
    salaryMin: optionalNumber(values.salaryMin),
    salaryMax: optionalNumber(values.salaryMax),
    salaryCurrency: values.salaryCurrency.trim() || "VND",
    experienceYearsMin: optionalNumber(values.experienceYearsMin),
    experienceYearsMax: optionalNumber(values.experienceYearsMax),
    deadline: values.deadline ? `${values.deadline}T23:59:59` : null,
    positionsCount: Number(values.positionsCount),
    skills: values.skills,
  };
}

export function validateJobForm(values: JobFormValues, now = new Date()): FieldErrors<JobFormValues> {
  const errors: FieldErrors<JobFormValues> = {};
  const salaryMin = optionalNumber(values.salaryMin);
  const salaryMax = optionalNumber(values.salaryMax);
  const experienceMin = optionalNumber(values.experienceYearsMin);
  const experienceMax = optionalNumber(values.experienceYearsMax);
  const positions = Number(values.positionsCount);

  if (!values.title.trim()) errors.title = "Tiêu đề công việc là bắt buộc.";
  else if (values.title.trim().length > 300) errors.title = "Tiêu đề không được vượt quá 300 ký tự.";
  if (!values.description.trim()) errors.description = "Mô tả công việc là bắt buộc.";
  if (salaryMin !== null && salaryMin < 0) errors.salaryMin = "Mức lương không được là số âm.";
  if (salaryMax !== null && salaryMax < 0) errors.salaryMax = "Mức lương không được là số âm.";
  if (salaryMin !== null && salaryMax !== null && salaryMax < salaryMin) {
    errors.salaryMax = "Mức lương tối đa phải lớn hơn hoặc bằng mức tối thiểu.";
  }
  if (experienceMin !== null && experienceMax !== null && experienceMax < experienceMin) {
    errors.experienceYearsMax = "Kinh nghiệm tối đa phải lớn hơn hoặc bằng mức tối thiểu.";
  }
  if (!Number.isInteger(positions) || positions < 1) {
    errors.positionsCount = "Số lượng tuyển phải ít nhất là 1.";
  }
  if (values.deadline) {
    const deadline = new Date(`${values.deadline}T23:59:59`);
    if (Number.isNaN(deadline.getTime()) || deadline <= now) errors.deadline = "Hạn nộp phải ở tương lai.";
  }
  return errors;
}

export function validateEmployerProfile(values: EmployerProfileInput): FieldErrors<EmployerProfileInput> {
  const errors: FieldErrors<EmployerProfileInput> = {};
  if (!values.fullName.trim()) errors.fullName = "Họ và tên là bắt buộc.";
  else if (values.fullName.trim().length > 200) errors.fullName = "Họ và tên không được vượt quá 200 ký tự.";
  if (values.position.trim().length > 200) errors.position = "Chức danh không được vượt quá 200 ký tự.";
  if (values.gender && values.gender !== "Male" && values.gender !== "Female") {
    errors.gender = "Giới tính không hợp lệ.";
  }
  if (values.phone && !/^0\d{9}$/.test(values.phone)) {
    errors.phone = "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.";
  }
  return errors;
}

export function validateCompanyProfile(
  values: CompanyProfileInput,
  mode: "create" | "update",
): FieldErrors<CompanyProfileInput> {
  const errors: FieldErrors<CompanyProfileInput> = {};
  if (!values.name.trim()) errors.name = "Tên công ty là bắt buộc.";
  else if (values.name.trim().length > 300) errors.name = "Tên công ty không được vượt quá 300 ký tự.";
  if (values.scale.trim().length > 100) errors.scale = "Quy mô không được vượt quá 100 ký tự.";
  if (values.industry.trim().length > 100) errors.industry = "Ngành nghề không được vượt quá 100 ký tự.";
  if (values.websiteUrl.trim()) {
    try {
      new URL(values.websiteUrl.trim());
    } catch {
      errors.websiteUrl = "Website phải là một URL đầy đủ.";
    }
  }
  return errors;
}
