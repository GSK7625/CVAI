import { useMemo } from "react";
import { Link, useNavigate } from "react-router";
import {
  IconChevronRight,
  IconSparkles,
} from "@tabler/icons-react";

import {
  CV_TEMPLATES,
} from "~/features/candidate/data/cvTemplates";
import { useCvStore } from "~/stores/useCvStore";

const CATEGORY_TABS = [
  { key: "all", label: "Tất cả" },
  { key: "simple", label: "Đơn giản" },
  { key: "professional", label: "Chuyên nghiệp" },
  { key: "modern", label: "Hiện đại" },
  { key: "impressive", label: "Ấn tượng" },
  { key: "harvard", label: "Harvard" },
  { key: "ats", label: "ATS" },
];

export default function CvTemplatesPage() {
  const navigate = useNavigate();

  // ── Zustand Store ──────────────────────────────────────────
  const selectedCategory = useCvStore((s) => s.selectedCategory);
  const selectedLanguage = useCvStore((s) => s.selectedLanguage);
  const templateColors = useCvStore((s) => s.templateColors);
  const setSelectedCategory = useCvStore((s) => s.setSelectedCategory);
  const setSelectedLanguage = useCvStore((s) => s.setSelectedLanguage);
  const setTemplateColor = useCvStore((s) => s.setTemplateColor);
  const initFromTemplate = useCvStore((s) => s.initFromTemplate);

  const filteredTemplates = useMemo(() => {
    if (selectedCategory === "all") return CV_TEMPLATES;
    return CV_TEMPLATES.filter((t) => t.category === selectedCategory);
  }, [selectedCategory]);

  const handleUseTemplate = (templateId: string) => {
    const color = templateColors[templateId] || CV_TEMPLATES.find((t) => t.id === templateId)?.defaultColor;
    initFromTemplate(templateId, color);
    navigate(`/cv/builder/${templateId}?color=${encodeURIComponent(color || "#111827")}`);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] pb-20">
      {/* ── Top Announcement Banner ─────────────────────────── */}
      <div className="border-b border-gold/20 bg-gradient-to-r from-amber-50 via-amber-100/60 to-yellow-50 py-3">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 text-label-sm sm:px-6">
          <div className="flex items-center gap-2 text-navy">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-gold text-xs font-bold text-white">
              ✦
            </span>
            <span>
              Hãy tạo CV chuẩn chỉnh ngay hôm nay để nhận được gợi ý việc làm phù hợp từ AI!
            </span>
          </div>
          <Link
            to="/jobs"
            className="inline-flex items-center gap-1.5 rounded-full bg-navy px-4 py-1 text-[12px] font-bold text-white transition-all hover:bg-navy-secondary"
          >
            <span>Cập nhật nhu cầu công việc</span>
            <IconChevronRight size={13} />
          </Link>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 pt-6 sm:px-6">
        {/* ── Breadcrumb ────────────────────────────────────── */}
        <nav className="mb-4 flex items-center gap-2 text-label-sm text-ink-muted">
          <Link to="/" className="transition-colors hover:text-navy">
            Trang chủ
          </Link>
          <IconChevronRight size={14} />
          <span className="font-medium text-navy">Mẫu CV {selectedLanguage}</span>
        </nav>

        {/* ── Header Title & Subtitle ───────────────────────── */}
        <div className="relative mb-8 flex flex-col justify-between gap-4 rounded-2xl border border-border-subtle bg-white p-6 shadow-sm md:flex-row md:items-center md:p-8">
          <div className="max-w-3xl">
            <h1 className="text-2xl font-bold leading-tight text-navy md:text-3xl">
              Mẫu CV xin việc tiếng Việt, Anh, Nhật, Trung chuẩn 2026
            </h1>
            <p className="mt-2 text-body text-ink-variant">
              Tuyển chọn các mẫu CV đa dạng phong cách, chuẩn bộ lọc ATS doanh nghiệp, giúp bạn tạo dấu ấn cá nhân chuyên nghiệp và kết nối mạnh mẽ hơn với nhà tuyển dụng.
            </p>
          </div>

          <div className="hidden shrink-0 items-center justify-center md:flex">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gold/10 text-gold shadow-inner">
              <IconSparkles size={40} />
            </div>
          </div>
        </div>

        {/* ── Filter Tabs & Language Dropdown ───────────────── */}
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-border-subtle pb-4">
          {/* Category tabs */}
          <div className="flex flex-wrap items-center gap-2">
            {CATEGORY_TABS.map((tab) => {
              const isActive = selectedCategory === tab.key;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setSelectedCategory(tab.key)}
                  className={`flex items-center gap-1.5 rounded-full px-4 py-2 text-label font-semibold transition-all duration-200 ${isActive
                      ? "bg-navy text-white shadow-sm"
                      : "border border-border-subtle bg-white text-ink hover:border-navy hover:text-navy"
                    }`}
                >
                  {tab.key === "all" && <span>🔲</span>}
                  {tab.key === "simple" && <span>📦</span>}
                  {tab.key === "professional" && <span>💼</span>}
                  {tab.key === "modern" && <span>💎</span>}
                  {tab.key === "impressive" && <span>📐</span>}
                  {tab.key === "harvard" && <span>🎓</span>}
                  {tab.key === "ats" && <span>🤖</span>}
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>


        </div>

        {/* ── Templates Grid ─────────────────────────────────── */}
        <div className="grid grid-cols-1 gap-7 sm:grid-cols-2 lg:grid-cols-3">
          {filteredTemplates.map((template) => {
            const currentColor = templateColors[template.id] || template.defaultColor;

            return (
              <div
                key={template.id}
                className="group relative flex flex-col overflow-hidden rounded-2xl border border-border-subtle bg-white shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-gold hover:shadow-xl"
              >
                {/* ── Mini CV Mockup Preview ─────────────────── */}
                <div className="relative aspect-[3/4] w-full overflow-hidden bg-[#f1f5f9] p-4">
                  {/* The Simulated CV Sheet */}
                  <div
                    className="relative h-full w-full overflow-hidden rounded-lg bg-white p-4 shadow-md transition-transform duration-300 group-hover:scale-[1.02]"
                    style={{ borderTop: `4px solid ${currentColor}` }}
                  >
                    {/* Header of CV Sheet */}
                    <div className="flex items-start gap-3 border-b border-border-subtle pb-3">
                      {template.sampleCandidate.avatar ? (
                        <img
                          src={template.sampleCandidate.avatar}
                          alt={template.sampleCandidate.fullName}
                          className="h-12 w-12 rounded-full object-cover shadow-sm ring-2 ring-border-subtle"
                        />
                      ) : (
                        <div
                          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-white font-bold"
                          style={{ backgroundColor: currentColor }}
                        >
                          {template.sampleCandidate.fullName.charAt(0)}
                        </div>
                      )}
                      <div className="flex-1 overflow-hidden">
                        <div
                          className="text-[13px] font-bold leading-tight"
                          style={{ color: currentColor }}
                        >
                          {template.sampleCandidate.fullName}
                        </div>
                        <div className="text-[10px] font-semibold text-ink-muted">
                          {template.sampleCandidate.title}
                        </div>
                        <div className="mt-1 flex items-center gap-2 text-[9px] text-ink-muted">
                          <span>📍 Hà Nội</span>
                          <span>✉️ dung@topcv.vn</span>
                        </div>
                      </div>
                    </div>

                    {/* Summary snippet */}
                    <div className="my-2.5">
                      <div
                        className="mb-1 text-[9.5px] font-bold uppercase tracking-wider"
                        style={{ color: currentColor }}
                      >
                        Mục tiêu nghề nghiệp
                      </div>
                      <p className="line-clamp-2 text-[9px] leading-relaxed text-ink-variant">
                        {template.sampleCandidate.summary}
                      </p>
                    </div>

                    {/* Experience snippet */}
                    <div className="my-2.5 border-t border-border-subtle/60 pt-2">
                      <div
                        className="mb-1 text-[9.5px] font-bold uppercase tracking-wider"
                        style={{ color: currentColor }}
                      >
                        Kinh nghiệm làm việc
                      </div>
                      <div className="space-y-1 text-[9px] text-ink-variant">
                        <div className="flex justify-between font-semibold text-navy">
                          <span>Senior Executive</span>
                          <span className="text-[8px] text-ink-muted">2022 - Nay</span>
                        </div>
                        <div className="h-1.5 w-4/5 rounded bg-slate-100" />
                        <div className="h-1.5 w-3/5 rounded bg-slate-100" />
                      </div>
                    </div>

                    {/* Skills pills */}
                    <div className="my-2.5 border-t border-border-subtle/60 pt-2">
                      <div
                        className="mb-1 text-[9.5px] font-bold uppercase tracking-wider"
                        style={{ color: currentColor }}
                      >
                        Kỹ năng chính
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {template.sampleCandidate.skills.map((skill, i) => (
                          <span
                            key={i}
                            className="rounded bg-slate-100 px-1.5 py-0.5 text-[8.5px] font-medium text-ink-variant"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* ── Hover Overlay: "Dùng mẫu" Button ────────── */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-navy/40 p-6 opacity-0 backdrop-blur-[2px] transition-all duration-300 group-hover:opacity-100">
                    <button
                      type="button"
                      onClick={() => handleUseTemplate(template.id)}
                      className="inline-flex w-full max-w-[200px] transform items-center justify-center gap-2 rounded-xl bg-gold px-5 py-3 text-label font-bold text-white shadow-lg transition-all duration-200 hover:scale-105 hover:bg-[#b08233] active:scale-95"
                    >
                      <IconSparkles size={18} />
                      <span>Dùng mẫu</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleUseTemplate(template.id)}
                      className="mt-2 text-[12px] font-semibold text-white/90 underline hover:text-white"
                    >
                      Xem chi tiết & Chỉnh sửa
                    </button>
                  </div>
                </div>

                {/* ── Card Footer: Color Selector, Title & Tags ─ */}
                <div className="flex flex-1 flex-col justify-between p-5">
                  <div>
                    {/* Color palette picker */}
                    <div className="mb-3 flex items-center gap-2">
                      {template.colors.map((c) => {
                        const isSelected = currentColor === c;
                        return (
                          <button
                            key={c}
                            type="button"
                            onClick={() => setTemplateColor(template.id, c)}
                            aria-label={`Chọn màu ${c}`}
                            className={`h-5 w-5 rounded-full transition-all ${isSelected
                                ? "scale-125 ring-2 ring-navy ring-offset-2"
                                : "hover:scale-110 opacity-70 hover:opacity-100"
                              }`}
                            style={{ backgroundColor: c }}
                          />
                        );
                      })}
                    </div>

                    <h3 className="text-label-lg font-bold text-navy group-hover:text-gold transition-colors">
                      {template.name}
                    </h3>
                    <p className="mt-1 line-clamp-2 text-label-sm text-ink-muted">
                      {template.subtitle}
                    </p>
                  </div>

                  {/* Tags */}
                  <div className="mt-4 flex flex-wrap gap-1.5 border-t border-border-subtle pt-3">
                    {template.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="rounded-md bg-surface-low px-2 py-0.5 text-[11px] font-semibold text-ink-muted"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
