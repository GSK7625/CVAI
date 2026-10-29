/**
 * @file CvPreviewPaper.tsx
 * @description Bản xem trước CV thời gian thực mô phỏng chuẩn trang in A4. Bọc React.memo để ngăn re-render khi tab hoặc các state UI khác đổi.
 */

import { memo } from "react";
import { IconEye } from "@tabler/icons-react";

import type {
  CvPersonalInfo,
  CvExperience,
  CvEducation,
} from "~/stores/useCvStore";

export interface CvProjectPreviewItem {
  id: string;
  name: string;
  role?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  description?: string | null;
  technologies?: string | null;
}

export interface CvPreviewPaperProps {
  activeColor: string;
  personalInfo: CvPersonalInfo;
  experiences: CvExperience[];
  educations: CvEducation[];
  skills: string[];
  projects?: CvProjectPreviewItem[];
  className?: string;
  paperId?: string;
}

export const CvPreviewPaper = memo(function CvPreviewPaper({
  activeColor,
  personalInfo,
  experiences,
  educations,
  skills,
  projects,
  className,
  paperId = "cv-preview-paper",
}: CvPreviewPaperProps) {
  return (
    <div className={className ?? "flex flex-col items-center lg:col-span-7"}>
      <div className="mb-3 flex w-full items-center justify-between px-2 text-label-sm text-ink-muted no-print print:hidden">
        <span className="flex items-center gap-1.5 font-semibold text-navy">
          <IconEye size={16} /> Xem trước thời gian thực (Trang A4)
        </span>
        <span>Tỉ lệ chuẩn in ấn PDF</span>
      </div>

      {/* ── The Rendered A4 Sheet ───────────────────────── */}
      <div
        id={paperId}
        className="w-full max-w-[680px] rounded-xl border border-border-subtle bg-white p-8 shadow-2xl transition-all duration-300 md:p-12"
        style={{
          borderTop: `8px solid ${activeColor}`,
          printColorAdjust: "exact",
          WebkitPrintColorAdjust: "exact",
        }}
      >
        {/* Header Section */}
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between border-b border-border-subtle pb-6">
          <div className="flex-1">
            <h1
              className="text-2xl font-black tracking-tight"
              style={{
                color: activeColor,
                printColorAdjust: "exact",
                WebkitPrintColorAdjust: "exact",
              }}
            >
              {personalInfo.fullName || "HỌ VÀ TÊN"}
            </h1>
            <h2 className="mt-1 text-label-lg font-bold text-ink-muted">
              {personalInfo.title || "VỊ TRÍ ỨNG TUYỂN"}
            </h2>

            <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-label-sm text-ink-variant">
              {personalInfo.email && <span>✉️ {personalInfo.email}</span>}
              {personalInfo.phone && <span>📞 {personalInfo.phone}</span>}
              {personalInfo.location && <span>📍 {personalInfo.location}</span>}
              {personalInfo.website && <span>🌐 {personalInfo.website}</span>}
            </div>
          </div>

          {personalInfo.avatar && (
            <div className="shrink-0">
              <img
                src={personalInfo.avatar}
                alt={personalInfo.fullName}
                className="h-24 w-24 rounded-full object-cover shadow-md ring-4 ring-slate-100"
              />
            </div>
          )}
        </div>

        {/* 1. Summary / Objective */}
        {personalInfo.summary && (
          <div className="my-6">
            <h3
              className="mb-2 text-label font-bold uppercase tracking-wider"
              style={{
                color: activeColor,
                printColorAdjust: "exact",
                WebkitPrintColorAdjust: "exact",
              }}
            >
              Mục tiêu nghề nghiệp
            </h3>
            <p className="whitespace-pre-line text-body-sm leading-relaxed text-ink-variant">
              {personalInfo.summary}
            </p>
          </div>
        )}

        {/* 2. Work Experience */}
        {experiences.length > 0 && (
          <div className="my-6">
            <h3
              className="mb-3 text-label font-bold uppercase tracking-wider"
              style={{
                color: activeColor,
                printColorAdjust: "exact",
                WebkitPrintColorAdjust: "exact",
              }}
            >
              Kinh nghiệm làm việc
            </h3>
            <div className="flex flex-col gap-4">
              {experiences.map((exp) => (
                <div
                  key={exp.id}
                  className="relative pl-3 border-l-2"
                  style={{
                    borderColor: activeColor,
                    borderLeftWidth: "2px",
                    borderLeftStyle: "solid",
                    printColorAdjust: "exact",
                    WebkitPrintColorAdjust: "exact",
                  }}
                >
                  <div className="flex flex-wrap items-center justify-between text-body-sm">
                    <strong className="text-navy" style={{ color: "#0b132b" }}>{exp.role}</strong>
                    <span className="text-[12px] font-semibold text-ink-muted">
                      {exp.startDate} - {exp.endDate}
                    </span>
                  </div>
                  <div
                    className="text-[13px] font-medium text-gold"
                    style={{
                      color: activeColor === "#B45309" ? "#B45309" : "#c8963e",
                      printColorAdjust: "exact",
                      WebkitPrintColorAdjust: "exact",
                    }}
                  >
                    {exp.company}
                  </div>
                  <p className="mt-1.5 whitespace-pre-line text-[12.5px] leading-relaxed text-ink-variant">
                    {exp.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3. Education */}
        {educations.length > 0 && (
          <div className="my-6">
            <h3
              className="mb-3 text-label font-bold uppercase tracking-wider"
              style={{
                color: activeColor,
                printColorAdjust: "exact",
                WebkitPrintColorAdjust: "exact",
              }}
            >
              Học vấn & Trình độ
            </h3>
            <div className="flex flex-col gap-3">
              {educations.map((edu) => (
                <div
                  key={edu.id}
                  className="flex flex-wrap items-start justify-between text-body-sm"
                >
                  <div>
                    <strong className="text-navy" style={{ color: "#0b132b" }}>{edu.degree}</strong>
                    <div className="text-[13px] text-ink-variant">{edu.school}</div>
                    {edu.gpa && <div className="text-[12px] text-ink-muted">{edu.gpa}</div>}
                  </div>
                  <span className="text-[12px] font-semibold text-ink-muted">
                    {edu.startDate} - {edu.endDate}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 4. Skills */}
        {skills.length > 0 && (
          <div className="my-6">
            <h3
              className="mb-3 text-label font-bold uppercase tracking-wider"
              style={{
                color: activeColor,
                printColorAdjust: "exact",
                WebkitPrintColorAdjust: "exact",
              }}
            >
              Kỹ năng chuyên môn
            </h3>
            <div className="flex flex-wrap gap-2">
              {skills.map((skill, i) => (
                <span
                  key={i}
                  className="rounded-lg px-3 py-1 text-label-sm font-semibold"
                  style={{
                    backgroundColor: "#f1f5f9",
                    color: "#0b132b",
                    border: "1px solid #e2e8f0",
                    printColorAdjust: "exact",
                    WebkitPrintColorAdjust: "exact",
                  }}
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 5. Projects */}
        {projects && projects.length > 0 && (
          <div className="my-6">
            <h3
              className="mb-3 text-label font-bold uppercase tracking-wider"
              style={{
                color: activeColor,
                printColorAdjust: "exact",
                WebkitPrintColorAdjust: "exact",
              }}
            >
              Dự án tiêu biểu
            </h3>
            <div className="flex flex-col gap-4">
              {projects.map((proj) => (
                <div
                  key={proj.id}
                  className="relative pl-3 border-l-2"
                  style={{
                    borderColor: activeColor,
                    borderLeftWidth: "2px",
                    borderLeftStyle: "solid",
                    printColorAdjust: "exact",
                    WebkitPrintColorAdjust: "exact",
                  }}
                >
                  <div className="flex flex-wrap items-center justify-between text-body-sm">
                    <strong className="text-navy" style={{ color: "#0b132b" }}>{proj.name}</strong>
                    {(proj.startDate || proj.endDate) && (
                      <span className="text-[12px] font-semibold text-ink-muted">
                        {proj.startDate || ""} {proj.endDate ? `- ${proj.endDate}` : ""}
                      </span>
                    )}
                  </div>
                  {proj.role && (
                    <div
                      className="text-[13px] font-medium text-gold"
                      style={{
                        color: activeColor === "#B45309" ? "#B45309" : "#c8963e",
                        printColorAdjust: "exact",
                        WebkitPrintColorAdjust: "exact",
                      }}
                    >
                      {proj.role}
                    </div>
                  )}
                  {proj.technologies && (
                    <div className="text-[12px] text-ink-muted italic">
                      Công nghệ: {proj.technologies}
                    </div>
                  )}
                  {proj.description && (
                    <p className="mt-1 whitespace-pre-line text-[12.5px] leading-relaxed text-ink-variant">
                      {proj.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
});
