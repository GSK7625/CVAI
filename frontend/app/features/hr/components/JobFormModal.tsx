import { useEffect, useState, type FormEvent } from "react";
import { IconCheck, IconX } from "@tabler/icons-react";
import { Button, Field, Input, Modal } from "~/components/ui";
import { useUIStore } from "~/stores/useUIStore";
import { toJobRequest, validateJobForm, type FieldErrors } from "../contracts/hrContracts";
import { useCreateEmployerJob, useHrMasterData, useUpdateEmployerJob } from "../hooks/useEmployerJobs";
import type { JobDetail, JobFormValues, JobSkillInput } from "../types";

const emptyJob: JobFormValues = {
  title: "",
  description: "",
  requirements: "",
  benefits: "",
  categoryId: "",
  levelId: "",
  employmentTypeId: "",
  locationId: "",
  salaryMin: "",
  salaryMax: "",
  salaryCurrency: "VND",
  experienceYearsMin: "",
  experienceYearsMax: "",
  deadline: "",
  positionsCount: "1",
  skills: [],
};

function valuesFromJob(job?: JobDetail | null): JobFormValues {
  if (!job) return emptyJob;
  return {
    title: job.title,
    description: job.description,
    requirements: job.requirements ?? "",
    benefits: job.benefits ?? "",
    categoryId: job.categoryId ?? "",
    levelId: job.levelId ?? "",
    employmentTypeId: job.employmentTypeId ?? "",
    locationId: job.locationId ?? "",
    salaryMin: job.salaryMin?.toString() ?? "",
    salaryMax: job.salaryMax?.toString() ?? "",
    salaryCurrency: job.salaryCurrency || "VND",
    experienceYearsMin: job.experienceYearsMin?.toString() ?? "",
    experienceYearsMax: job.experienceYearsMax?.toString() ?? "",
    deadline: job.deadline?.slice(0, 10) ?? "",
    positionsCount: job.positionsCount?.toString() || "1",
    skills: job.skills.map(({ skillId, isRequired }) => ({ skillId, isRequired })),
  };
}

export function JobFormModal({ open, onClose, job }: { open: boolean; onClose: () => void; job?: JobDetail | null }) {
  const [values, setValues] = useState<JobFormValues>(() => valuesFromJob(job));
  const [errors, setErrors] = useState<FieldErrors<JobFormValues>>({});
  const [contentTab, setContentTab] = useState<"description" | "requirements" | "benefits">("description");
  const masterData = useHrMasterData();
  const createJob = useCreateEmployerJob();
  const updateJob = useUpdateEmployerJob();
  const showToast = useUIStore((state) => state.showToast);
  const mutation = job ? updateJob : createJob;

  useEffect(() => {
    if (open) {
      setValues(valuesFromJob(job));
      setErrors({});
      setContentTab("description");
    }
  }, [open, job]);

  const setField = (field: keyof JobFormValues, value: string) => {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  };

  const addSkill = (skillId: string) => {
    if (!skillId || values.skills.some((skill) => skill.skillId === skillId)) return;
    setValues((current) => ({ ...current, skills: [...current.skills, { skillId, isRequired: true }] }));
  };

  const updateSkill = (skillId: string, patch: Partial<JobSkillInput>) => {
    setValues((current) => ({
      ...current,
      skills: current.skills.map((skill) => (skill.skillId === skillId ? { ...skill, ...patch } : skill)),
    }));
  };

  const removeSkill = (skillId: string) => {
    setValues((current) => ({ ...current, skills: current.skills.filter((skill) => skill.skillId !== skillId) }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const nextErrors = validateJobForm(values);
    setErrors(nextErrors);
    if (nextErrors.description) setContentTab("description");
    if (Object.keys(nextErrors).length) return;
    try {
      const input = toJobRequest(values);
      if (job) await updateJob.mutateAsync({ id: job.id, input });
      else await createJob.mutateAsync(input);
      onClose();
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Không thể lưu tin tuyển dụng", "error");
    }
  };

  const availableSkills =
    masterData.data?.skills.filter((option) => !values.skills.some((skill) => skill.skillId === option.id)) ?? [];

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={job ? "Chỉnh sửa tin tuyển dụng" : "Tạo tin tuyển dụng"}
      className="max-h-[94dvh] max-w-3xl overflow-y-auto"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={mutation.isPending}>Hủy</Button>
          <Button type="submit" form="job-form" disabled={mutation.isPending || masterData.isLoading}>
            <IconCheck size={18} aria-hidden="true" />
            {mutation.isPending ? "Đang lưu..." : job ? "Lưu thay đổi" : "Tạo tin"}
          </Button>
        </>
      }
    >
      <form id="job-form" className="space-y-4" onSubmit={handleSubmit} noValidate>
        <Field label="Tiêu đề công việc" htmlFor="job-title" required error={errors.title}>
          <Input id="job-title" placeholder="Ví dụ: Lập trình viên React Frontend" value={values.title} onChange={(event) => setField("title", event.target.value)} error={errors.title} />
        </Field>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <SelectField id="job-category" label="Ngành nghề" value={values.categoryId} onChange={(value) => setField("categoryId", value)} options={masterData.data?.categories ?? []} />
          <SelectField id="job-level" label="Cấp bậc" value={values.levelId} onChange={(value) => setField("levelId", value)} options={masterData.data?.levels ?? []} />
          <SelectField id="job-employment" label="Loại hình" value={values.employmentTypeId} onChange={(value) => setField("employmentTypeId", value)} options={masterData.data?.employmentTypes ?? []} />
          <SelectField id="job-location" label="Địa điểm" value={values.locationId} onChange={(value) => setField("locationId", value)} options={masterData.data?.locations ?? []} />
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Khoảng lương (VNĐ)" htmlFor="job-salary-min" error={errors.salaryMin || errors.salaryMax}>
            <div className="flex items-center gap-2">
              <Input id="job-salary-min" type="number" min="0" placeholder="Tối thiểu" value={values.salaryMin} onChange={(event) => setField("salaryMin", event.target.value)} error={errors.salaryMin} />
              <span className="text-ink-muted shrink-0">—</span>
              <Input id="job-salary-max" type="number" min="0" placeholder="Tối đa" value={values.salaryMax} onChange={(event) => setField("salaryMax", event.target.value)} error={errors.salaryMax} />
            </div>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Số lượng tuyển" htmlFor="job-positions" required error={errors.positionsCount}>
              <Input id="job-positions" type="number" min="1" step="1" value={values.positionsCount} onChange={(event) => setField("positionsCount", event.target.value)} error={errors.positionsCount} />
            </Field>
            <Field label="Hạn nộp hồ sơ" htmlFor="job-deadline" error={errors.deadline}>
              <Input id="job-deadline" type="date" value={values.deadline} onChange={(event) => setField("deadline", event.target.value)} error={errors.deadline} />
            </Field>
          </div>
        </div>

        <div>
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <label className="text-label font-semibold text-ink">
              Nội dung tuyển dụng <span className="text-danger">*</span>
            </label>
            <div className="inline-flex rounded-default border border-border-strong bg-surface-low p-0.5 text-label-sm">
              <button
                type="button"
                onClick={() => setContentTab("description")}
                className={`rounded-default px-3 py-1 font-medium transition-colors ${
                  contentTab === "description" ? "bg-navy text-white shadow-xs" : "text-ink-variant hover:text-navy"
                }`}
              >
                Mô tả công việc *
              </button>
              <button
                type="button"
                onClick={() => setContentTab("requirements")}
                className={`rounded-default px-3 py-1 font-medium transition-colors ${
                  contentTab === "requirements" ? "bg-navy text-white shadow-xs" : "text-ink-variant hover:text-navy"
                }`}
              >
                Yêu cầu {values.requirements.trim() ? "•" : ""}
              </button>
              <button
                type="button"
                onClick={() => setContentTab("benefits")}
                className={`rounded-default px-3 py-1 font-medium transition-colors ${
                  contentTab === "benefits" ? "bg-navy text-white shadow-xs" : "text-ink-variant hover:text-navy"
                }`}
              >
                Quyền lợi {values.benefits.trim() ? "•" : ""}
              </button>
            </div>
          </div>

          {contentTab === "description" && (
            <div>
              <textarea
                id="job-description"
                rows={4}
                placeholder="Mô tả chi tiết nhiệm vụ và trách nhiệm chính của vị trí..."
                value={values.description}
                onChange={(event) => setField("description", event.target.value)}
                className="w-full rounded-default border border-border-strong bg-white px-3.5 py-2.5 text-ink focus:border-gold focus:ring-2 focus:ring-gold/20"
              />
              {errors.description && <p className="mt-1 text-label-sm text-danger">{errors.description}</p>}
            </div>
          )}

          {contentTab === "requirements" && (
            <textarea
              id="job-requirements"
              rows={4}
              placeholder="Yêu cầu về kỹ năng chuyên môn, kinh nghiệm thực tế..."
              value={values.requirements}
              onChange={(event) => setField("requirements", event.target.value)}
              className="w-full rounded-default border border-border-strong bg-white px-3.5 py-2.5 text-ink focus:border-gold focus:ring-2 focus:ring-gold/20"
            />
          )}

          {contentTab === "benefits" && (
            <textarea
              id="job-benefits"
              rows={4}
              placeholder="Chế độ đãi ngộ, bảo hiểm, thưởng, phúc lợi công ty..."
              value={values.benefits}
              onChange={(event) => setField("benefits", event.target.value)}
              className="w-full rounded-default border border-border-strong bg-white px-3.5 py-2.5 text-ink focus:border-gold focus:ring-2 focus:ring-gold/20"
            />
          )}
        </div>

        <Field label="Kỹ năng yêu cầu" htmlFor="job-skill-add" hint="Chọn kỹ năng để tối ưu kết quả gợi ý ứng viên phù hợp.">
          <div className="flex gap-2">
            <select
              id="job-skill-add"
              defaultValue=""
              onChange={(event) => { addSkill(event.target.value); event.target.value = ""; }}
              className="h-10 min-w-0 flex-1 rounded-default border border-border-strong bg-white px-3 text-label focus:border-gold"
            >
              <option value="">+ Thêm kỹ năng vào tin tuyển dụng</option>
              {availableSkills.map((skill) => <option key={skill.id} value={skill.id}>{skill.name}</option>)}
            </select>
          </div>
          {values.skills.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-2">
              {values.skills.map((skill) => {
                const option = masterData.data?.skills.find((item) => item.id === skill.skillId);
                return (
                  <span
                    key={skill.skillId}
                    className="inline-flex items-center gap-1.5 rounded-default border border-border-subtle bg-surface-low px-2.5 py-1 text-label-sm"
                  >
                    <span className="font-semibold text-navy">{option?.name ?? skill.skillId}</span>
                    <button
                      type="button"
                      onClick={() => updateSkill(skill.skillId, { isRequired: !skill.isRequired })}
                      className={`cursor-pointer rounded-tag px-1.5 py-0.5 text-label-xs font-semibold transition-colors ${
                        skill.isRequired ? "bg-navy text-white" : "bg-border-subtle text-ink-variant hover:bg-border-strong"
                      }`}
                      title="Bấm để đổi Bắt buộc / Ưu tiên"
                    >
                      {skill.isRequired ? "Bắt buộc" : "Ưu tiên"}
                    </button>
                    <button
                      type="button"
                      aria-label={`Xóa kỹ năng ${option?.name ?? ""}`}
                      onClick={() => removeSkill(skill.skillId)}
                      className="ml-0.5 text-ink-muted hover:text-danger"
                    >
                      <IconX size={15} aria-hidden="true" />
                    </button>
                  </span>
                );
              })}
            </div>
          )}
        </Field>
      </form>
    </Modal>
  );
}

function SelectField({ id, label, value, onChange, options }: { id: string; label: string; value: string; onChange: (value: string) => void; options: { id: string; name: string }[] }) {
  return (
    <Field label={label} htmlFor={id}>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)} className="h-10 rounded-default border border-border-strong bg-white px-3 text-label text-ink focus:border-gold focus:ring-2 focus:ring-gold/20">
        <option value="">Chưa chọn</option>
        {options.map((option) => <option key={option.id} value={option.id}>{option.name}</option>)}
      </select>
    </Field>
  );
}
