import { memo, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router";
import { motion, useReducedMotion } from "motion/react";
import {
  IconBriefcase,
  IconDeviceDesktop,
  IconCode,
  IconCalculator,
  IconTool,
  IconSpeakerphone,
  IconUsers,
  IconHeartbeat,
  IconPalette,
  IconPhone,
  IconMail,
  IconSparkles,
  IconChevronLeft,
  IconChevronRight,
  IconX,
} from "@tabler/icons-react";
import { JobCard } from "~/components/shared/JobCard";
import { useJobList } from "~/features/candidate/hooks/useJobList";
import { useJobMasterData } from "~/features/candidate/hooks/useJobMasterData";
import { JobSearchBar } from "~/features/candidate/components/job-list/JobSearchBar";
import { formatNumber } from "~/utils";
import type { Job } from "~/features/candidate/types";

const industries = [
  { icon: IconCode, label: "IT / Phần mềm", count: 1245 },
  { icon: IconSpeakerphone, label: "Marketing / PR", count: 856 },
  { icon: IconCalculator, label: "Tài chính / Kế toán", count: 642 },
  { icon: IconBriefcase, label: "Kinh doanh / Bán hàng", count: 1890 },
  { icon: IconUsers, label: "Nhân sự (HR)", count: 420 },
  { icon: IconTool, label: "Kỹ thuật", count: 512 },
  { icon: IconHeartbeat, label: "Y tế / Sức khỏe", count: 325 },
  { icon: IconPalette, label: "Thiết kế / Nghệ thuật", count: 280 },
];

const popularCategories = [
  { icon: IconBriefcase, label: "Kinh doanh / Bán hàng" },
  { icon: IconSpeakerphone, label: "Marketing / PR" },
  { icon: IconCode, label: "IT Phần mềm" },
  { icon: IconCalculator, label: "Kế toán / Kiểm toán" },
  { icon: IconTool, label: "Kỹ thuật" },
  { icon: IconUsers, label: "Nhân sự (HR)" },
];

const featuredCompanies = [
  { name: "Techcom Solutions VN", industry: "Công nghệ thông tin / Phần mềm", jobs: 15 },
  { name: "Global Commerce", industry: "Thương mại điện tử / Bán lẻ", jobs: 8 },
  { name: "Vietnam Healthcare", industry: "Y tế / Chăm sóc sức khỏe", jobs: 24 },
  { name: "EduTech VN", industry: "Giáo dục / Đào tạo", jobs: 12 },
];

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

const sharedViewport = { once: true, margin: "-64px" } as const;



const AnimatedJobCard = memo(function AnimatedJobCard({
  job,
  index,
}: {
  job: Job;
  index: number;
}) {
  const reduceMotion = useReducedMotion();
  if (reduceMotion) return <JobCard job={job} />;
  return (
    <motion.div
      variants={fadeUp}
      custom={index}
      initial="hidden"
      whileInView="visible"
      viewport={sharedViewport}
    >
      <JobCard job={job} />
    </motion.div>
  );
});

export default function HomePage() {
  const navigate = useNavigate();
  const reduceMotion = useReducedMotion();
  const { data: masterData, isLoading: loadingMasterData } = useJobMasterData();
  const [activeChip, setActiveChip] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [showHint, setShowHint] = useState(true);
  const hotlineRef = useRef<HTMLDivElement>(null);

  const resolveCategoryHref = (label: string) => {
    if (masterData?.categories && masterData.categories.length > 0) {
      const normalize = (s: string) => s.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
      const targetNorm = normalize(label);

      // 1. So khớp tuyệt đối hoặc so sánh không phân biệt hoa thường
      const exact = masterData.categories.find(
        (c) => normalize(c.name) === targetNorm || c.name.toLowerCase() === label.toLowerCase(),
      );
      if (exact) return `/jobs?categoryId=${encodeURIComponent(exact.id)}`;

      // 2. So khớp chuỗi con
      const substr = masterData.categories.find((c) => {
        const cNorm = normalize(c.name);
        return cNorm.includes(targetNorm) || targetNorm.includes(cNorm);
      });
      if (substr) return `/jobs?categoryId=${encodeURIComponent(substr.id)}`;

      // 3. So khớp theo cụm từ phụ (cắt theo ký tự /, -)
      const parts = label
        .toLowerCase()
        .split(/[/,-]+/)
        .map((p) => p.trim())
        .filter((p) => p.length > 1);

      const phraseMatch = masterData.categories.find((c) => {
        const cLower = c.name.toLowerCase();
        return parts.some((p) => cLower.includes(p) || normalize(cLower).includes(normalize(p)));
      });
      if (phraseMatch) return `/jobs?categoryId=${encodeURIComponent(phraseMatch.id)}`;
    }

    // Fallback: nếu chưa tải xong master data hoặc không khớp danh mục nào, dùng từ khóa ?q=
    return `/jobs?q=${encodeURIComponent(label)}`;
  };

  const activeLocationId = useMemo(() => {
    if (!activeChip || !masterData?.locations) return undefined;
    const found = masterData.locations.find(
      (l) =>
        l.name.toLowerCase() === activeChip.toLowerCase() ||
        l.name.toLowerCase().includes(activeChip.toLowerCase()),
    );
    return found?.id;
  }, [activeChip, masterData]);

  const { data: featuredJobs } = useJobList({
    locationId: activeLocationId,
    page,
    pageSize: 8,
  });

  return (
    <div>
      {/* ── Hero: navy, search-centric ─────────────────────── */}
      <section className="w-full bg-navy px-margin-mobile pb-14 pt-16 text-white md:px-margin-desktop">
        <div className="container-page mx-auto flex flex-col items-center">
          <motion.h1
            {...(reduceMotion
              ? {}
              : {
                  initial: { opacity: 0, y: 20 },
                  animate: { opacity: 1, y: 0 },
                  transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] as const },
                })}
            className="max-w-4xl text-center text-display leading-tight md:text-display"
          >
            Tạo CV, Tìm việc làm, Tuyển dụng hiệu quả
          </motion.h1>
          <p className="mt-4 text-body-lg text-white/70">
            Hàng nghìn cơ hội việc làm từ các doanh nghiệp uy tín trên toàn quốc.
          </p>

          {/* Search bar độc lập state */}
          <JobSearchBar
            keyword=""
            locations={masterData?.locations ?? []}
            loadingLocations={loadingMasterData}
            className="mt-10 max-w-4xl"
            onSubmit={(v) => {
              const params = new URLSearchParams();
              if (v.keyword) params.set("q", v.keyword);
              if (v.locationId) params.set("locationId", v.locationId);
              navigate(`/jobs${params.size ? `?${params}` : ""}`);
            }}
          />

          {/* Categories + Banner 1 */}
          <div className="mt-10 grid w-full max-w-4xl grid-cols-1 gap-6 md:grid-cols-3">
            <div className="flex flex-col justify-between rounded-xl border border-white/20 bg-white/10 p-6 backdrop-blur-md">
              <h3 className="mb-4 font-semibold text-white">Ngành nghề phổ biến</h3>
              <ul className="flex flex-col gap-3">
                {popularCategories.map((cat) => (
                  <li key={cat.label}>
                    <Link
                      to={resolveCategoryHref(cat.label)}
                      className="flex items-center gap-3 text-white/90 transition-all hover:translate-x-1 hover:text-white"
                    >
                      <cat.icon size={18} stroke={1.6} />
                      {cat.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <Link
              to="/jobs"
              className="relative flex max-h-[290px] w-full items-center justify-center overflow-hidden rounded-xl bg-surface shadow-overlay md:col-span-2"
            >
              <img
                src="/banner1.png"
                alt="Cơ hội việc làm phổ thông - Thu nhập hấp dẫn"
                className="h-full w-full object-cover"
              />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Việc làm hấp dẫn ─────────────────────────────────── */}
      <section className="w-full bg-surface py-14">
        <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
          {/* Header row */}
          <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-headline-md font-bold text-navy">
                Việc làm hấp dẫn
              </h2>
              <span className="flex items-center gap-1.5 rounded-full border border-gold/40 bg-gold/10 px-3 py-1 text-label-sm font-semibold text-gold">
                <IconSparkles size={14} /> Đề xuất bởi FutureAI
              </span>
            </div>

            <div className="flex items-center gap-4">
              <Link
                to="/jobs"
                className="text-label font-semibold text-navy transition-colors hover:text-gold"
              >
                Xem tất cả
              </Link>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  aria-label="Trang trước"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="flex h-8 w-8 items-center justify-center rounded-full border border-border-strong bg-surface text-ink-variant transition-colors hover:border-navy hover:text-navy disabled:cursor-not-allowed disabled:opacity-30"
                >
                  <IconChevronLeft size={16} />
                </button>
                <button
                  type="button"
                  aria-label="Trang sau"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= Math.ceil((featuredJobs?.total ?? 8) / 8)}
                  className="flex h-8 w-8 items-center justify-center rounded-full border border-border-strong bg-surface text-ink-variant transition-colors hover:border-navy hover:text-navy disabled:cursor-not-allowed disabled:opacity-30"
                >
                  <IconChevronRight size={16} />
                </button>
              </div>
            </div>
          </div>

          {/* Filter row */}
          <div className="mb-4 flex items-center gap-2 overflow-x-auto pb-1">
            <div className="flex shrink-0 items-center gap-1 rounded-full border border-border-strong bg-surface px-3 py-1.5 text-label-sm text-ink-variant">
              <span className="text-ink-muted">Lọc theo:</span>
              <span className="font-semibold text-ink">Địa điểm</span>
            </div>
            {["Tất cả", "Hà Nội", "TP. HCM", "Đà Nẵng", "Từ xa"].map((chip) => {
              const isSelected = activeChip === chip || (chip === "Tất cả" && !activeChip);
              return (
                <button
                  key={chip}
                  type="button"
                  onClick={() => {
                    setActiveChip(chip === "Tất cả" ? null : chip);
                    setPage(1);
                  }}
                  className={`whitespace-nowrap rounded-full border px-4 py-1.5 text-label-sm transition-all ${
                    isSelected
                      ? "border-navy bg-navy font-semibold text-white shadow-sm"
                      : "border-border-subtle bg-surface text-ink-variant hover:border-border-strong hover:bg-surface-low"
                  }`}
                >
                  {chip}
                </button>
              );
            })}
          </div>

          {/* Hint bar */}
          {showHint && (
            <div className="mb-6 flex items-center justify-between rounded-lg border border-blue-100 bg-blue-50/70 px-4 py-2.5 text-label-sm text-navy">
              <div className="flex items-center gap-2">
                <span className="text-base">💡</span>
                <span>Gợi ý: Di chuột vào tiêu đề việc làm để xem thêm thông tin chi tiết</span>
              </div>
              <button
                type="button"
                onClick={() => setShowHint(false)}
                className="p-1 text-ink-muted transition-colors hover:text-navy"
                aria-label="Đóng gợi ý"
              >
                <IconX size={14} />
              </button>
            </div>
          )}

          {/* Main Content: 2 columns grid + Banner */}
          <div className="flex flex-col items-stretch gap-5 lg:flex-row">
            {/* Left: Cards Grid */}
            <div className="grid w-full flex-1 grid-cols-1 gap-3 sm:grid-cols-2">
              {(featuredJobs?.items ?? []).map((job, i) => (
                <AnimatedJobCard key={job.id} job={job} index={i} />
              ))}
            </div>

            {/* Right: Vertical Banner */}
            <div className="w-full shrink-0 lg:w-[250px]">
              <Link
                to="/jobs"
                className="group relative block h-full overflow-hidden rounded-xl bg-surface shadow-sm transition-all duration-300 hover:shadow-md"
              >
                <img
                  src="/banner2.png"
                  alt="2000+ Việc làm phổ thông thu nhập hấp dẫn"
                  className="h-full w-full object-cover rounded-xl"
                />
              </Link>
            </div>
          </div>

          {/* Pagination */}
          <div className="mt-8 flex items-center justify-center gap-3">
            <button
              type="button"
              aria-label="Trang trước"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-border-strong bg-surface text-ink-variant transition-colors hover:border-navy hover:text-navy disabled:cursor-not-allowed disabled:opacity-30"
            >
              <IconChevronLeft size={16} />
            </button>
            <span className="text-label-sm font-medium text-ink-muted">
              {page} / {Math.max(1, Math.ceil((featuredJobs?.total ?? 8) / 8))} trang
            </span>
            <button
              type="button"
              aria-label="Trang sau"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.max(1, Math.ceil((featuredJobs?.total ?? 8) / 8))}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-border-strong bg-surface text-ink-variant transition-colors hover:border-navy hover:text-navy disabled:cursor-not-allowed disabled:opacity-30"
            >
              <IconChevronRight size={16} />
            </button>
          </div>
        </div>
      </section>

      {/* ── Công ty nổi bật ────────────────────────────────── */}
      <section className="w-full bg-background py-14">
        <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
          <motion.div
            variants={fadeUp}
            custom={0}
            initial="hidden"
            whileInView="visible"
            viewport={sharedViewport}
          >
            <h2 className="mb-8 text-center text-headline text-navy">Công ty nổi bật</h2>
          </motion.div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {featuredCompanies.map((company, i) => (
              <motion.article
                key={company.name}
                variants={fadeUp}
                custom={i + 1}
                initial="hidden"
                whileInView="visible"
                viewport={sharedViewport}
                className="group flex h-[210px] flex-col justify-between rounded-xl border border-border-subtle bg-surface p-4 text-center shadow-sm transition-all hover:border-gold/60 hover:shadow-md"
              >
                <div className="flex flex-col items-center">
                  <div className="mb-2.5 flex h-14 w-14 items-center justify-center rounded-xl border border-border-subtle bg-surface-low">
                    <IconDeviceDesktop size={26} stroke={1.4} className="text-ink-muted" />
                  </div>
                  <h3 className="mb-1 line-clamp-1 text-label font-bold text-navy">{company.name}</h3>
                  <p className="line-clamp-1 text-label-sm text-ink-muted">{company.industry}</p>
                </div>
                <Link
                  to={`/jobs?q=${encodeURIComponent(company.name)}`}
                  className="w-full rounded-lg bg-navy-secondary/10 px-3 py-2 text-label-sm font-semibold text-navy transition-colors hover:bg-navy-secondary/20"
                >
                  {company.jobs} Việc làm đang tuyển
                </Link>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      {/* ── Top ngành nghề nổi bật ──────────────────────────── */}
      <section className="w-full bg-surface py-14">
        <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
          <motion.div
            variants={fadeUp}
            custom={0}
            initial="hidden"
            whileInView="visible"
            viewport={sharedViewport}
          >
            <h2 className="mb-8 text-center text-headline text-navy">Top ngành nghề nổi bật</h2>
          </motion.div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 md:grid-cols-4">
            {industries.map((ind, i) => (
              <motion.div
                key={ind.label}
                variants={fadeUp}
                custom={i + 1}
                initial="hidden"
                whileInView="visible"
                viewport={sharedViewport}
              >
                <Link
                  to={resolveCategoryHref(ind.label)}
                  className="group flex h-[116px] flex-col items-center justify-center rounded-xl border border-border-subtle bg-surface p-3 text-center shadow-sm transition-all hover:border-gold/60 hover:shadow-md"
                >
                  <div className="mb-2 flex h-11 w-11 items-center justify-center rounded-full bg-navy-secondary/5 transition-colors group-hover:bg-gold/10">
                    <ind.icon
                      size={22}
                      stroke={1.6}
                      className="text-navy transition-colors group-hover:text-gold"
                    />
                  </div>
                  <h3 className="line-clamp-1 text-label font-bold text-navy">{ind.label}</h3>
                  <p className="mt-0.5 text-[11px] text-ink-muted">
                    {formatNumber(ind.count)} việc làm
                  </p>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Hotline ────────────────────────────────────────── */}
      <section
        ref={hotlineRef}
        className="relative w-full overflow-hidden bg-gradient-to-r from-navy to-slate-800 py-16 text-white"
      >
        <div
          aria-hidden
          className="absolute inset-0 opacity-10"
          style={{
            background:
              "radial-gradient(circle at center, white, transparent 70%)",
          }}
        />
        <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 relative z-10">
          <h2 className="mb-8 text-headline font-bold">Hotline Tư Vấn</h2>
          <div className="flex flex-col overflow-hidden rounded-xl bg-surface md:flex-row">
            <div className="w-full bg-white p-8 md:w-3/5 md:p-12">
              <h3 className="mb-8 text-3xl font-bold text-navy">
                Tìm việc khó đã có <span className="text-gold">FutureCV</span>
              </h3>
              <div className="mb-8 flex flex-col items-start gap-4 sm:flex-row sm:items-center">
                <div className="flex items-center rounded-full bg-navy p-1 pr-6">
                  <span className="px-4 font-semibold text-white">1900 068 889 | Nhánh 2</span>
                  <a
                    href="tel:1900068889"
                    className="ml-2 flex items-center gap-2 rounded-full bg-white px-6 py-2 font-bold text-navy transition-colors hover:bg-surface-low"
                  >
                    <IconPhone size={16} stroke={2} /> GỌI NGAY
                  </a>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-body text-ink-variant">
                <span>Email hỗ trợ Ứng viên:</span>
                <a
                  href="mailto:hotro@futurecv.vn"
                  className="flex items-center gap-1 font-bold text-navy underline decoration-gold hover:text-gold"
                >
                  <IconMail size={16} stroke={1.8} /> hotro@futurecv.vn
                </a>
              </div>
            </div>
            <div className="relative flex min-h-[240px] w-full items-end justify-center bg-[#f0f4f8] md:w-2/5">
              <div className="absolute right-10 top-1/4 z-30 flex items-center gap-2 rounded-full bg-navy px-4 py-2 text-label-sm shadow-lg">
                <span className="h-2 w-2 rounded-full bg-emerald-400" aria-hidden />
                Xin chào
              </div>
              <div className="absolute bottom-1/4 left-10 z-30 flex items-center gap-2 rounded-full bg-gold px-4 py-2 text-label-sm shadow-lg">
                FutureCV có thể giúp bạn điều gì?
              </div>
              <IconSparkles
                size={96}
                stroke={1}
                className="absolute bottom-6 text-navy/10"
                aria-hidden
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
