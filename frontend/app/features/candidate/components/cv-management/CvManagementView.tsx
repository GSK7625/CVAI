/**
 * @file CvManagementView.tsx
 * @description Giao diện chính "Kho CV của tôi" (/candidate/cvs - FC-82).
 * - Bố cục Dạng Danh sách (List View) tinh gọn, thanh thoát, phong cách Midnight & Gold.
 * - Quản lý deletingCvId tập trung (Lift State Up) để chỉ có 1 thẻ mở banner xóa một lúc.
 * - Kết hợp các component tách biệt: CvCockpitSkeleton, CvMetricsDeck, CvInsightsAside.
 * Design: Anti-slop rules, zero em-dash, @tabler/icons-react.
 */

import { useState, useMemo } from "react";
import { Link } from "react-router";
import {
  IconFolderOpen,
  IconPlus,
  IconTemplate,
  IconRefresh,
  IconCloudUpload,
  IconSearch,
  IconX,
  IconAlertCircle,
  IconSparkles,
  IconCheck,
} from "@tabler/icons-react";
import { useCandidateCvs } from "../../hooks/useCandidateCvs";
import { CvCard } from "./CvCard";
import { CvUploadZone } from "./CvUploadZone";
import { CvCockpitSkeleton } from "./CvCockpitSkeleton";
import { CvMetricsDeck } from "./CvMetricsDeck";
import { CvInsightsAside } from "./CvInsightsAside";

// ── Rich Empty States ─────────────────────────────────────────────────────────

function EmptySearchResults({ onReset }: { onReset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-border-strong bg-surface py-14 px-6 text-center">
      <div className="w-14 h-14 rounded-2xl bg-navy/5 flex items-center justify-center">
        <IconSearch size={28} className="text-ink-muted" />
      </div>
      <div>
        <h3 className="text-base font-bold text-ink">Không tìm thấy hồ sơ phù hợp</h3>
        <p className="mt-1 text-xs text-ink-muted max-w-sm mx-auto leading-relaxed">
          Không có CV nào khớp với từ khóa tìm kiếm hoặc bộ lọc hiện tại của bạn.
        </p>
      </div>
      <button
        type="button"
        onClick={onReset}
        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-navy/20 bg-surface-low text-xs font-semibold text-navy hover:bg-navy/5 transition-all"
      >
        <IconRefresh size={14} />
        <span>Xem tất cả CV</span>
      </button>
    </div>
  );
}

function EmptyStateNoCV({ onUploadClick }: { onUploadClick: () => void }) {
  return (
    <div className="rounded-[2rem] p-1 bg-gradient-to-br from-gold/20 via-navy/5 to-surface-low border border-navy/10 shadow-sm">
      <div className="rounded-[calc(2rem-0.25rem)] bg-white p-6 sm:p-10 space-y-8 text-center">
        <div className="max-w-md mx-auto space-y-2.5">
          <div className="w-16 h-16 rounded-2xl bg-navy/8 flex items-center justify-center mx-auto text-navy">
            <IconFolderOpen size={32} />
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-navy tracking-tight">
            Kho hồ sơ của bạn đang trống
          </h2>
          <p className="text-xs sm:text-sm text-ink-variant leading-relaxed">
            Tải lên bản CV cá nhân dạng PDF hoặc tạo bản CV chuyên nghiệp trực tuyến với công cụ CV Builder.
          </p>
        </div>

        {/* 2 Pathway Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mx-auto text-left">
          {/* Pathway 1: Upload */}
          <div className="rounded-2xl border border-border-strong bg-surface-low p-5 flex flex-col justify-between space-y-4 hover:border-gold/50 transition-colors">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-navy text-white flex items-center justify-center">
                <IconCloudUpload size={20} />
              </div>
              <h3 className="text-sm font-bold text-navy">Tải lên file PDF có sẵn</h3>
              <p className="text-xs text-ink-muted leading-relaxed">
                Tải lên bản CV cá nhân dạng PDF (dung lượng tối đa 5MB). Hệ thống sẽ tự động phân tích điểm chất lượng hồ sơ.
              </p>
            </div>
            <button
              type="button"
              onClick={onUploadClick}
              className="inline-flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-navy text-white text-xs font-bold hover:bg-navy-secondary transition-all active:scale-[0.98]"
            >
              <IconCloudUpload size={15} />
              <span>Tải file PDF lên</span>
            </button>
          </div>

          {/* Pathway 2: Builder */}
          <div className="rounded-2xl border border-gold/30 bg-gradient-to-b from-gold/10 to-surface-low p-5 flex flex-col justify-between space-y-4 hover:border-gold/60 transition-colors">
            <div className="space-y-2">
              <div className="w-10 h-10 rounded-xl bg-gold text-white flex items-center justify-center">
                <IconSparkles size={20} />
              </div>
              <h3 className="text-sm font-bold text-navy">Tạo CV từ mẫu chuyên nghiệp</h3>
              <p className="text-xs text-ink-muted leading-relaxed">
                Lựa chọn các mẫu thiết kế đẹp mắt, chỉnh sửa trực quan theo thời gian thực và đồng bộ 1-chạm vào kho hồ sơ.
              </p>
            </div>
            <Link
              to="/cv/templates"
              className="inline-flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-gold text-white text-xs font-bold hover:bg-gold-light transition-all active:scale-[0.98]"
            >
              <IconTemplate size={15} />
              <span>Khám phá kho mẫu CV</span>
            </Link>
          </div>
        </div>

        {/* Value props bullets */}
        <div className="pt-4 border-t border-border-subtle max-w-xl mx-auto flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-ink-muted">
          <span className="inline-flex items-center gap-1.5">
            <IconCheck size={14} className="text-success" />
            Phân tích điểm hồ sơ tự động
          </span>
          <span className="inline-flex items-center gap-1.5">
            <IconCheck size={14} className="text-success" />
            Đồng bộ ứng tuyển 1-chạm
          </span>
          <span className="inline-flex items-center gap-1.5">
            <IconCheck size={14} className="text-success" />
            Bảo mật thông tin cá nhân
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Main View ─────────────────────────────────────────────────────────────────

export function CvManagementView() {
  const { data: cvs = [], isLoading, isError, refetch, isFetching } = useCandidateCvs();
  const [showUpload, setShowUpload] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"all" | "primary">("all");
  const [deletingCvId, setDeletingCvId] = useState<string | null>(null);

  const primaryCv = cvs.find((cv) => cv.isPrimary);

  // Filtered CVs
  const filteredCvs = useMemo(() => {
    let list = [...cvs];

    // Filter by tab
    if (activeTab === "primary") {
      list = list.filter((cv) => cv.isPrimary);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter((cv) => (cv.title || "").toLowerCase().includes(q));
    }

    // Sort: primary first, then newest
    return list.sort((a, b) => {
      if (a.isPrimary) return -1;
      if (b.isPrimary) return 1;
      return new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime();
    });
  }, [cvs, activeTab, searchQuery]);

  if (isLoading) {
    return (
      <div className="w-full">
        <CvCockpitSkeleton />
      </div>
    );
  }

  return (
    <div className="w-full space-y-8">
      {/* ── Page Header ──────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-5 border-b border-navy/10 pb-6">
        <div className="space-y-1.5">
          <nav className="flex items-center gap-2 text-xs text-ink-muted mb-1.5">
            <Link to="/" className="hover:text-navy transition-colors">
              Trang chủ
            </Link>
            <span>/</span>
            <span className="font-semibold text-navy">Hồ sơ ứng tuyển</span>
          </nav>
          <h1 className="text-2xl sm:text-3xl font-bold text-navy tracking-tight">
            Kho CV của tôi
          </h1>
          <p className="text-sm text-ink-variant max-w-2xl leading-relaxed">
            Quản lý các bản CV ứng tuyển và đặt hồ sơ mặc định để hệ thống tự động tính điểm phù hợp khi tìm việc.
          </p>
        </div>

        {/* Action Buttons Deck */}
        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <button
            type="button"
            title="Làm mới dữ liệu"
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2.5 rounded-xl border border-border-strong bg-surface text-ink-muted hover:text-navy hover:bg-surface-low transition-colors disabled:opacity-50 shadow-xs"
          >
            <IconRefresh size={18} className={isFetching ? "animate-spin" : ""} />
          </button>

          <Link
            to="/cv/templates"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-navy/20 bg-surface text-xs font-bold text-navy hover:bg-navy/5 transition-all active:scale-[0.98] shadow-xs"
          >
            <IconTemplate size={16} />
            <span>Tạo CV mới</span>
          </Link>

          <button
            type="button"
            onClick={() => setShowUpload((v) => !v)}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-navy text-white text-xs font-bold hover:bg-navy-secondary transition-all active:scale-[0.98] shadow-xs"
          >
            <IconPlus size={16} />
            <span>Tải lên CV PDF</span>
          </button>
        </div>
      </div>

      {/* ── Bento Metrics Deck ─────────────────────────────────────── */}
      <CvMetricsDeck cvs={cvs} primaryCv={primaryCv} />

      {/* ── Main Split Layout (8 / 4 Grid) ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:h-[750px]">
        {/* ── Left Column: CV List & Management (8 cols) ──────────── */}
        <div className="lg:col-span-8 flex flex-col space-y-6 min-h-0 h-full">
          {/* Smart Upload Zone Drawer */}
          {showUpload && (
            <section className="rounded-2xl border border-gold/30 bg-gold/5 p-5 space-y-4 shadow-xs">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-navy flex items-center gap-2">
                  <IconCloudUpload size={18} className="text-gold" />
                  Tải lên hồ sơ CV mới
                </h2>
                <button
                  type="button"
                  onClick={() => setShowUpload(false)}
                  className="p-1.5 rounded-lg text-ink-muted hover:text-navy hover:bg-surface transition-colors"
                >
                  <IconX size={16} />
                </button>
              </div>
              <CvUploadZone
                onUploaded={() => {
                  setShowUpload(false);
                  refetch();
                }}
              />
            </section>
          )}

          {/* Filter & Search Toolbar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-2 rounded-2xl border border-border-subtle bg-surface shadow-xs">
            {/* Search Input */}
            <div className="relative flex-1 min-w-[200px]">
              <IconSearch
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"
              />
              <input
                type="text"
                placeholder="Tìm kiếm theo tên CV..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-8 py-2 rounded-xl bg-surface-low border border-transparent text-xs font-medium text-ink placeholder:text-ink-muted focus:outline-none focus:border-navy/20 focus:bg-surface transition-all"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-muted hover:text-navy"
                >
                  <IconX size={14} />
                </button>
              )}
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1 shrink-0">
              <button
                type="button"
                onClick={() => setActiveTab("all")}
                className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${activeTab === "all"
                    ? "bg-navy text-white shadow-xs"
                    : "text-ink-variant hover:bg-surface-low"
                  }`}
              >
                Tất cả ({cvs.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("primary")}
                className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${activeTab === "primary"
                    ? "bg-navy text-white shadow-xs"
                    : "text-ink-variant hover:bg-surface-low"
                  }`}
              >
                CV chính
              </button>
            </div>
          </div>

          {/* CV Items List (Lifted delete state) */}
          {isError ? (
            <div className="rounded-2xl border border-danger/20 bg-danger/5 p-8 text-center space-y-3">
              <IconAlertCircle size={32} className="text-danger mx-auto opacity-70" />
              <p className="text-sm font-semibold text-danger">Không thể tải danh sách hồ sơ.</p>
              <button
                type="button"
                onClick={() => refetch()}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-danger/30 bg-surface text-xs font-semibold text-danger hover:bg-danger/8 transition-colors"
              >
                <IconRefresh size={14} />
                <span>Thử lại</span>
              </button>
            </div>
          ) : cvs.length === 0 ? (
            <EmptyStateNoCV onUploadClick={() => setShowUpload(true)} />
          ) : filteredCvs.length === 0 ? (
            <EmptySearchResults
              onReset={() => {
                setSearchQuery("");
                setActiveTab("all");
              }}
            />
          ) : (
            <div className="space-y-4 overflow-y-auto pr-1.5 pb-2 flex-1 min-h-0 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-navy/20 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-navy/30">
              {filteredCvs.map((cv) => (
                <CvCard
                  key={cv.id}
                  cv={cv}
                  isDeleting={deletingCvId === cv.id}
                  onStartDelete={() => setDeletingCvId(cv.id)}
                  onCancelDelete={() => setDeletingCvId(null)}
                />
              ))}
            </div>
          )}
        </div>

        {/* ── Right Column: Insights & Career Hub (4 cols) ─────────── */}
        <CvInsightsAside />
      </div>
    </div>
  );
}
