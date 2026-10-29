/**
 * @file cv-builder.tsx
 * @description Trang biên tập CV trực tuyến (CV Builder) chính của ứng viên.
 * @architecture Tối ưu hóa subscriptions bằng useShallow và ổn định callback references.
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { useParams, useSearchParams } from "react-router";
import { useShallow } from "zustand/react/shallow";
import { CV_TEMPLATES } from "~/features/candidate/data/cvTemplates";
import { useCvStore, type CvPersonalInfo } from "~/stores/useCvStore";
import { useUIStore } from "~/stores/useUIStore";
import { CvToolbar } from "~/features/candidate/components/cv-builder/CvToolbar";
import { CvEditorTabs } from "~/features/candidate/components/cv-builder/CvEditorTabs";
import { PersonalInfoForm } from "~/features/candidate/components/cv-builder/PersonalInfoForm";
import { ExperienceForm } from "~/features/candidate/components/cv-builder/ExperienceForm";
import { EducationForm } from "~/features/candidate/components/cv-builder/EducationForm";
import { SkillsForm } from "~/features/candidate/components/cv-builder/SkillsForm";
import { CvPreviewPaper } from "~/features/candidate/components/cv-builder/CvPreviewPaper";
import { generateCvPdf, sanitizePdfFilename } from "~/features/candidate/utils/cvPdfExport";

export default function CvBuilderPage() {
  const { templateId = "standard-general" } = useParams();
  const [searchParams] = useSearchParams();
  const showToast = useUIStore((s) => s.showToast);

  // ── Zustand Global CV Store Slices (Gom bằng useShallow) ───
  const cv = useCvStore(
    useShallow((s) => ({
      templateId: s.templateId,
      activeColor: s.activeColor,
      activeTab: s.activeTab,
      personalInfo: s.personalInfo,
      experiences: s.experiences,
      educations: s.educations,
      skills: s.skills,
    })),
  );

  const actions = useCvStore(
    useShallow((s) => ({
      setActiveColor: s.setActiveColor,
      setActiveTab: s.setActiveTab,
      initFromTemplate: s.initFromTemplate,
      updatePersonalInfo: s.updatePersonalInfo,
      addExperience: s.addExperience,
      updateExperience: s.updateExperience,
      removeExperience: s.removeExperience,
      addEducation: s.addEducation,
      updateEducation: s.updateEducation,
      removeEducation: s.removeEducation,
      addSkill: s.addSkill,
      removeSkill: s.removeSkill,
      resetToTemplate: s.resetToTemplate,
    })),
  );

  const selectedTemplate = useMemo(() => {
    return CV_TEMPLATES.find((t) => t.id === templateId) ?? CV_TEMPLATES[0];
  }, [templateId]);

  useEffect(() => {
    if (templateId && templateId !== cv.templateId) {
      const colorParam = searchParams.get("color");
      actions.initFromTemplate(templateId, colorParam || undefined);
    }
  }, [templateId, cv.templateId, searchParams, actions]);

  const handleUpdatePersonalInfo = useCallback(
    (data: Partial<CvPersonalInfo>) => {
      actions.updatePersonalInfo(data);
    },
    [actions],
  );

  const handleExportPDF = useCallback(async () => {
    const paperEl = document.getElementById("cv-preview-paper");
    if (!paperEl) {
      window.print();
      return;
    }

    const filename = sanitizePdfFilename(cv.personalInfo.fullName || "UngVien");

    // 1. Thử xuất PDF trực tiếp qua generateCvPdf (hỗ trợ oklch, chuẩn A4)
    try {
      showToast("Đang chuẩn bị xuất file PDF chuẩn A4...", "info");
      const { pdf } = await generateCvPdf(paperEl, { filename });
      pdf.save(filename);
      showToast("Đã tải file PDF thành công!", "success");
      return;
    } catch (err) {
      console.warn("Direct generateCvPdf error, using isolated print dialog:", err);
    }

    // 2. Fallback: Mở hộp thoại In qua Iframe cách ly (chỉ chứa duy nhất tờ CV chuẩn A4)
    const oldIframe = document.getElementById("cv-builder-print-iframe");
    if (oldIframe) {
      oldIframe.remove();
    }

    const iframe = document.createElement("iframe");
    iframe.id = "cv-builder-print-iframe";
    iframe.style.position = "fixed";
    iframe.style.right = "0";
    iframe.style.bottom = "0";
    iframe.style.width = "0";
    iframe.style.height = "0";
    iframe.style.border = "none";
    document.body.appendChild(iframe);

    const doc = iframe.contentWindow?.document;
    if (!doc) {
      window.print();
      return;
    }

    // Thu thập toàn bộ thẻ link stylesheet và style từ trang chính để đưa vào iframe
    const styleTags = Array.from(
      document.querySelectorAll('link[rel="stylesheet"], style')
    )
      .map((el) => el.outerHTML)
      .join("\n");

    doc.open();
    doc.write(`
      <!DOCTYPE html>
      <html lang="vi">
        <head>
          <meta charset="utf-8" />
          <title>${filename}</title>
          ${styleTags}
          <style>
            @page {
              size: A4 portrait;
              margin: 8mm 0;
            }
            *, *::before, *::after {
              box-sizing: border-box;
              -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important;
              color-adjust: exact !important;
            }
            html, body {
              margin: 0 !important;
              padding: 0 !important;
              background: #ffffff !important;
              -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important;
            }
            .print-paper-wrapper {
              width: 100%;
              max-width: 680px;
              margin: 0 auto;
              padding: 8mm 10mm;
              background: #ffffff;
            }
            #cv-preview-paper {
              box-shadow: none !important;
              border-left: none !important;
              border-right: none !important;
              border-bottom: none !important;
              width: 100% !important;
              max-width: 100% !important;
              padding: 0 !important;
            }
            .no-print, [data-no-print="true"] {
              display: none !important;
            }
          </style>
        </head>
        <body>
          <div class="print-paper-wrapper">
            ${paperEl.outerHTML}
          </div>
        </body>
      </html>
    `);
    doc.close();

    setTimeout(() => {
      iframe.contentWindow?.focus();
      iframe.contentWindow?.print();
      setTimeout(() => {
        iframe.remove();
      }, 2000);
    }, 300);
  }, [cv.personalInfo.fullName, showToast]);

  const handleResetData = useCallback(() => {
    if (confirm("Bạn có chắc muốn đặt lại toàn bộ nội dung theo mẫu gốc này không?")) {
      actions.resetToTemplate(selectedTemplate.id);
      showToast("Đã khôi phục nội dung mẫu ban đầu.", "info");
    }
  }, [actions, selectedTemplate.id, showToast]);

  return (
    <div className="min-h-screen bg-[#f1f5f9] pb-24 print:bg-white print:p-0 print:m-0 print:pb-0">
      {/* ── Top Floating Action Bar ─────────────────────────── */}
      <CvToolbar
        selectedTemplate={selectedTemplate}
        activeColor={cv.activeColor}
        personalInfoFullName={cv.personalInfo.fullName}
        onColorChange={actions.setActiveColor}
        onResetData={handleResetData}
        onExportPDF={handleExportPDF}
      />

      {/* ── Main Workspace: Editor Form (Left) & Realtime Preview (Right) ── */}
      <div className="mx-auto max-w-7xl px-4 pt-6 print:p-0 print:m-0 print:max-w-none print:w-full">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 print:block print:w-full print:p-0 print:m-0">
          {/* ── Left Column: Form Editor (5 cols) ─────────────── */}
          <div className="flex flex-col gap-6 lg:col-span-5 no-print print:hidden">
            <CvEditorTabs activeTab={cv.activeTab} onTabChange={actions.setActiveTab} />

            {cv.activeTab === "info" && (
              <PersonalInfoForm
                personalInfo={cv.personalInfo}
                onUpdate={handleUpdatePersonalInfo}
              />
            )}

            {cv.activeTab === "experience" && (
              <ExperienceForm
                experiences={cv.experiences}
                onAdd={actions.addExperience}
                onUpdate={actions.updateExperience}
                onRemove={actions.removeExperience}
              />
            )}

            {cv.activeTab === "education" && (
              <EducationForm
                educations={cv.educations}
                onAdd={actions.addEducation}
                onUpdate={actions.updateEducation}
                onRemove={actions.removeEducation}
              />
            )}

            {cv.activeTab === "skills" && (
              <SkillsForm
                skills={cv.skills}
                onAddSkill={actions.addSkill}
                onRemoveSkill={actions.removeSkill}
              />
            )}
          </div>

          {/* ── Right Column: Live A4-Styled CV Preview (7 cols) ──── */}
          <CvPreviewPaper
            activeColor={cv.activeColor}
            personalInfo={cv.personalInfo}
            experiences={cv.experiences}
            educations={cv.educations}
            skills={cv.skills}
          />
        </div>
      </div>
    </div>
  );
}
