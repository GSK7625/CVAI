/**
 * @file CvUploadView.tsx
 * @description Giao diện trang Tải CV lên (/cv/upload).
 * - Tập trung tối đa vào trải nghiệm tải file CV dạng PDF (≤ 5MB).
 * - Không hiển thị danh sách hồ sơ CV tại trang này (danh sách được quản lý tại /candidate/cvs).
 * - Tái sử dụng CvUploadZone, CvInsightsAside và tuân thủ thiết kế Midnight & Gold.
 */

import { useState } from "react";
import { Link } from "react-router";
import {
  IconCloudUpload,
  IconFolderOpen,
  IconTemplate,
  IconSparkles,
  IconShieldCheck,
  IconCheck,
  IconLogin,
  IconUserPlus,
  IconFileText,
  IconCircleCheck,
  IconArrowRight,
  IconInfoCircle,
} from "@tabler/icons-react";
import { useAuthStore } from "~/stores/useAuthStore";
import { CvUploadZone } from "../cv-management/CvUploadZone";
import { CvInsightsAside } from "../cv-management/CvInsightsAside";
import type { CvResponse } from "../../types";

export function CvUploadView() {
  const user = useAuthStore((s) => s.user);
  const isAuthenticatedCandidate = !!user && user.role === "candidate";

  const [lastUploadedCv, setLastUploadedCv] = useState<CvResponse | null>(null);

  const handleUploadSuccess = (uploaded?: CvResponse) => {
    if (uploaded) {
      setLastUploadedCv(uploaded);
    }
  };

  return (
    <div className="container-page mx-auto px-margin-mobile py-8 md:px-margin-desktop space-y-8">
      {/* ── Page Header ─────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-5 border-b border-navy/10 pb-6">
        <div className="space-y-1.5">
          <nav className="flex items-center gap-2 text-xs text-ink-muted mb-1.5">
            <Link to="/" className="hover:text-navy transition-colors">
              Trang chủ
            </Link>
            <span>/</span>
            <span className="font-semibold text-navy">Tải CV lên</span>
          </nav>
          <h1 className="text-2xl sm:text-3xl font-bold text-navy tracking-tight">
            Tải CV lên hệ thống FutureCV
          </h1>
          <p className="text-sm text-ink-variant max-w-2xl leading-relaxed">
            Tải lên bản CV cá nhân dạng PDF (tối đa 5MB). Hệ thống sẽ tự động lưu trữ an toàn vào Kho hồ sơ, phân tích chất lượng và đồng bộ 1-chạm khi ứng tuyển.
          </p>
        </div>

        {/* Action Buttons Deck */}
        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <Link
            to="/cv/templates"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-navy/20 bg-surface text-xs font-bold text-navy hover:bg-navy/5 transition-all active:scale-[0.98] shadow-xs"
          >
            <IconTemplate size={16} />
            <span>Mẫu CV chuyên nghiệp</span>
          </Link>

          {isAuthenticatedCandidate && (
            <Link
              to="/candidate/cvs"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-navy text-white text-xs font-bold hover:bg-navy-secondary transition-all active:scale-[0.98] shadow-xs"
            >
              <IconFolderOpen size={16} />
              <span>Quản lý Kho CV</span>
            </Link>
          )}
        </div>
      </div>

      {/* ── Auth Alert Notice if Guest ───────────────────────────── */}
      {!isAuthenticatedCandidate && (
        <div className="rounded-2xl border border-gold/40 bg-gradient-to-r from-gold/10 via-surface to-navy/5 p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-gold text-white flex items-center justify-center shrink-0 shadow-xs">
              <IconSparkles size={20} />
            </div>
            <div className="space-y-1">
              <h2 className="text-sm font-bold text-navy">
                Đăng nhập tài khoản ứng viên để lưu trữ và đánh giá hồ sơ
              </h2>
              <p className="text-xs text-ink-variant leading-relaxed max-w-2xl">
                Bạn cần đăng nhập để tệp CV được tự động lưu vào Kho hồ sơ cá nhân và nhận báo cáo phân tích điểm mạnh, điểm yếu chi tiết từ hệ thống.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link
              to={`/login?returnTo=${encodeURIComponent("/cv/upload")}`}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-navy text-white text-xs font-bold hover:bg-navy-secondary transition-all active:scale-[0.98]"
            >
              <IconLogin size={15} />
              <span>Đăng nhập</span>
            </Link>
            <Link
              to="/register"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-navy/20 bg-white text-xs font-bold text-navy hover:bg-navy/5 transition-all active:scale-[0.98]"
            >
              <IconUserPlus size={15} />
              <span>Đăng ký</span>
            </Link>
          </div>
        </div>
      )}

      {/* ── Main Split Layout (8 / 4 Grid) ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* ── Left Column: Upload Hero & Guidance (8 cols) ────────── */}
        <div className="lg:col-span-8 space-y-6">
          {/* Success Banner when a CV was uploaded */}
          {lastUploadedCv && (
            <div className="rounded-2xl border border-success/30 bg-success/8 p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in slide-in-from-top-2 duration-300">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-success text-white flex items-center justify-center shrink-0 shadow-xs">
                  <IconCircleCheck size={22} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-navy">
                    Tải lên thành công: {lastUploadedCv.title || "Bản CV mới"}
                  </h3>
                  <p className="text-xs text-ink-variant mt-0.5">
                    Hồ sơ đã được lưu trữ an toàn trong Kho CV của bạn.
                  </p>
                </div>
              </div>
              <Link
                to="/candidate/cvs"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-navy text-white text-xs font-bold hover:bg-navy-secondary transition-all active:scale-[0.98] shrink-0"
              >
                <span>Xem trong Kho CV</span>
                <IconArrowRight size={14} />
              </Link>
            </div>
          )}

          {/* Main Upload Box */}
          <section className="rounded-[2rem] p-1 bg-gradient-to-br from-gold/30 via-navy/5 to-surface-low border border-navy/10 shadow-sm">
            <div className="rounded-[calc(2rem-0.25rem)] bg-white p-6 sm:p-8 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-navy text-white flex items-center justify-center shadow-xs">
                    <IconCloudUpload size={22} />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-navy">
                      Chọn hoặc kéo thả file CV của bạn
                    </h2>
                    <p className="text-xs text-ink-muted">
                      Hệ thống tự động đọc và phân tích cấu trúc tài liệu PDF
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-navy/5 text-navy text-[11px] font-semibold">
                    <IconFileText size={13} />
                    PDF tối đa 5MB
                  </span>
                </div>
              </div>

              {/* Reused Dropzone Component */}
              <CvUploadZone onUploaded={handleUploadSuccess} />

              {/* 3 Value Pillars */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-border-subtle">
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-surface-low">
                  <div className="w-6 h-6 rounded-lg bg-success/15 text-success flex items-center justify-center shrink-0 mt-0.5">
                    <IconCheck size={14} />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-navy">Phân tích tức thì</h3>
                    <p className="text-[11px] text-ink-muted mt-0.5">
                      Chấm điểm chất lượng cấu trúc hồ sơ tự động
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-surface-low">
                  <div className="w-6 h-6 rounded-lg bg-gold/15 text-gold flex items-center justify-center shrink-0 mt-0.5">
                    <IconSparkles size={14} />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-navy">Đồng bộ Kho CV</h3>
                    <p className="text-[11px] text-ink-muted mt-0.5">
                      Quản lý tập trung, chỉnh sửa và đổi tên linh hoạt
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-surface-low">
                  <div className="w-6 h-6 rounded-lg bg-navy/15 text-navy flex items-center justify-center shrink-0 mt-0.5">
                    <IconShieldCheck size={14} />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-navy">Ứng tuyển 1-chạm</h3>
                    <p className="text-[11px] text-ink-muted mt-0.5">
                      Sẵn sàng gửi đến các nhà tuyển dụng hàng đầu
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Upload Guidelines & Best Practices Card */}
          <section className="rounded-2xl border border-border-subtle bg-surface p-6 space-y-4 shadow-xs">
            <div className="flex items-center gap-2">
              <IconInfoCircle size={20} className="text-navy" />
              <h3 className="text-sm font-bold text-navy">
                Lưu ý định dạng để CV đạt điểm chất lượng cao
              </h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-ink-variant">
              <div className="space-y-1.5 p-3 rounded-xl bg-surface-low">
                <strong className="text-navy block font-semibold">1. Định dạng văn bản rõ ràng</strong>
                <p className="text-ink-muted leading-relaxed text-[11px]">
                  Sử dụng file PDF xuất trực tiếp từ Word hoặc Canva, tránh dùng file scan dạng ảnh để hệ thống có thể phân tích từ khóa chính xác.
                </p>
              </div>
              <div className="space-y-1.5 p-3 rounded-xl bg-surface-low">
                <strong className="text-navy block font-semibold">2. Đầy đủ các mục thông tin</strong>
                <p className="text-ink-muted leading-relaxed text-[11px]">
                  Hồ sơ nên bao gồm thông tin liên hệ, mục tiêu nghề nghiệp, kinh nghiệm làm việc, học vấn và các kỹ năng chuyên môn.
                </p>
              </div>
            </div>
          </section>

          {/* Alternative Pathway: CV Builder promotion banner */}
          <div className="rounded-2xl border border-gold/30 bg-gradient-to-r from-gold/15 via-white to-surface-low p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-navy">
                Bạn chưa có sẵn file CV hoàn chỉnh?
              </h3>
              <p className="text-xs text-ink-variant leading-relaxed max-w-xl">
                Sử dụng công cụ CV Builder trực tuyến của FutureCV để tạo CV chuẩn Harvard, ATS và chuyên nghiệp hoàn toàn miễn phí chỉ trong 5 phút.
              </p>
            </div>
            <Link
              to="/cv/templates"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gold text-white text-xs font-bold hover:bg-gold-light transition-all active:scale-[0.98] shrink-0 shadow-xs"
            >
              <IconTemplate size={16} />
              <span>Khám phá mẫu CV</span>
            </Link>
          </div>
        </div>

        {/* ── Right Column: Reused Insights & Tips Sidebar (4 cols) ─ */}
        <CvInsightsAside />
      </div>
    </div>
  );
}
