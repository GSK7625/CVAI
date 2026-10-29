import assert from "node:assert/strict";
import test from "node:test";
import {
  buildEmployerJobsQuery,
  buildRecruiterApplicationsQuery,
  toSafeDocumentUrl,
  toStatusUpdateRequest,
  toJobRequest,
  validateCompanyProfile,
  validateEmployerProfile,
  validateJobForm,
  validateStatusReason,
} from "./hrContracts.ts";
import type { JobFormValues } from "../types/index.ts";

const validJob: JobFormValues = {
  title: "Frontend Developer",
  description: "Xây dựng giao diện FutureCV",
  requirements: "React",
  benefits: "Bảo hiểm",
  categoryId: "",
  levelId: "",
  employmentTypeId: "",
  locationId: "",
  salaryMin: "10000000",
  salaryMax: "20000000",
  salaryCurrency: "VND",
  experienceYearsMin: "1",
  experienceYearsMax: "3",
  deadline: "2026-10-01",
  positionsCount: "2",
  skills: [{ skillId: "skill-1", isRequired: true }],
};

test("builds employer job filters with backend parameter names", () => {
  assert.equal(
    buildEmployerJobsQuery({
      keyword: "React dev",
      approvalStatus: "Approved",
      isActive: false,
      pageIndex: 2,
      pageSize: 10,
    }),
    "?Keyword=React+dev&ApprovalStatus=Approved&IsActive=false&PageIndex=2&PageSize=10",
  );
});

test("rejects invalid salary range, experience range, deadline, and positions", () => {
  const errors = validateJobForm(
    {
      ...validJob,
      salaryMin: "20",
      salaryMax: "10",
      experienceYearsMin: "4",
      experienceYearsMax: "2",
      deadline: "2026-09-07",
      positionsCount: "0",
    },
    new Date("2026-09-08T00:00:00Z"),
  );

  assert.equal(errors.salaryMax, "Mức lương tối đa phải lớn hơn hoặc bằng mức tối thiểu.");
  assert.equal(errors.experienceYearsMax, "Kinh nghiệm tối đa phải lớn hơn hoặc bằng mức tối thiểu.");
  assert.equal(errors.deadline, "Hạn nộp phải ở tương lai.");
  assert.equal(errors.positionsCount, "Số lượng tuyển phải ít nhất là 1.");
});

test("maps optional numeric and identifier fields to the backend DTO", () => {
  assert.deepEqual(toJobRequest({ ...validJob, salaryMax: "", levelId: "" }), {
    title: "Frontend Developer",
    description: "Xây dựng giao diện FutureCV",
    requirements: "React",
    benefits: "Bảo hiểm",
    categoryId: null,
    levelId: null,
    employmentTypeId: null,
    locationId: null,
    salaryMin: 10000000,
    salaryMax: null,
    salaryCurrency: "VND",
    experienceYearsMin: 1,
    experienceYearsMax: 3,
    deadline: "2026-10-01T23:59:59",
    positionsCount: 2,
    skills: [{ skillId: "skill-1", isRequired: true }],
  });
});

test("validates recruiter fields exactly as the backend validator", () => {
  assert.deepEqual(
    validateEmployerProfile({ fullName: "", position: "HR", gender: "Other", phone: "123" }),
    {
      fullName: "Họ và tên là bắt buộc.",
      gender: "Giới tính không hợp lệ.",
      phone: "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0.",
    },
  );
});

test("validates company profile fields and website URLs", () => {
  assert.deepEqual(
    validateCompanyProfile(
      { name: "FutureCV", scale: "", industry: "", websiteUrl: "futurecv", address: "", description: "" },
      "create",
    ),
    {
      websiteUrl: "Website phải là một URL đầy đủ.",
    },
  );
});

test("builds recruiter application filters with backend parameter names", () => {
  assert.equal(
    buildRecruiterApplicationsQuery({
      keyword: " Nguyen Van A ",
      status: "Screening",
      pageIndex: 2,
      pageSize: 20,
    }),
    "?Status=Screening&Keyword=Nguyen+Van+A&PageIndex=2&PageSize=20",
  );
});

test("normalizes application status update payload", () => {
  assert.deepEqual(toStatusUpdateRequest("Interview", " Đã qua vòng lọc "), {
    newStatus: "Interview",
    reason: "Đã qua vòng lọc",
  });
  assert.deepEqual(toStatusUpdateRequest("Rejected", "  "), {
    newStatus: "Rejected",
    reason: null,
  });
});

test("validates status reason with backend limits", () => {
  assert.equal(validateStatusReason("x".repeat(501)), "Lý do không được vượt quá 500 ký tự.");
});

test("allows only http URLs and application-relative CV paths", () => {
  assert.equal(toSafeDocumentUrl("/uploads/cv.pdf"), "/uploads/cv.pdf");
  assert.equal(toSafeDocumentUrl("https://files.futurecv.vn/cv.pdf"), "https://files.futurecv.vn/cv.pdf");
  assert.equal(toSafeDocumentUrl("javascript:alert(1)"), null);
  assert.equal(toSafeDocumentUrl("//evil.example/cv.pdf"), null);
});
