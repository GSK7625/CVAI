/**
 * @file CvCard.tsx
 * @description Thẻ hiển thị CV trong Kho hồ sơ ứng viên (FC-82).
 * - Bố cục Dạng Danh sách (List View) tinh xảo, sạch sẽ, phong cách Midnight & Gold.
 * - Tactile Document Preview: Thumbnail mô phỏng tài liệu trực quan kèm badge PDF.
 * - Huy hiệu CV chính mạ vàng hổ phách nổi bật.
 * - Tách RenameInput & DeleteConfirmBanner ra component riêng.
 * - State xóa được nâng lên View (Lift State Up) để tránh hiển thị nhiều banner cùng lúc.
 * Design: Anti-slop rules, zero em-dash, @tabler/icons-react.
 */

import { useState } from "react";
import {
  IconFileTypePdf,
  IconStar,
  IconTrash,
  IconPencil,
  IconChartBar,
  IconCloudDownload,
  IconChevronDown,
  IconChevronUp,
} from "@tabler/icons-react";
import { useSelectPrimaryCv } from "../../hooks/useCandidateCvs";
import { CvAnalysisPanel } from "./CvAnalysisPanel";
import { RenameInput } from "./RenameInput";
import { DeleteConfirmBanner } from "./DeleteConfirmBanner";
import type { CvResponse } from "../../types";

interface CvCardProps {
  cv: CvResponse;
  isDeleting?: boolean;
  onStartDelete?: () => void;
  onCancelDelete?: () => void;
}

// ── Badge helpers ─────────────────────────────────────────────────────────────

function PrimaryBadge() {
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-gold/15 text-gold border border-gold/30 shadow-xs">
      <IconStar size={12} className="fill-gold" />
      CV chính
    </span>
  );
}

// ── Mini Tactile Document Preview ─────────────────────────────────────────────

function DocumentThumbnail({ isPrimary }: { isPrimary: boolean }) {
  return (
    <div
      className={`relative w-14 h-18 sm:w-16 sm:h-20 rounded-xl flex flex-col justify-between p-2 shrink-0 select-none overflow-hidden transition-transform duration-300 group-hover:scale-105 ${
        isPrimary
          ? "bg-gradient-to-b from-surface to-gold/5 border-2 border-gold/40 shadow-xs"
          : "bg-surface border border-border-strong shadow-xs"
      }`}
    >
      {/* Top document lines simulation */}
      <div className="space-y-1">
        <div className="flex items-center gap-1">
          <div
            className={`w-3 h-3 rounded-full ${
              isPrimary ? "bg-gold/40" : "bg-navy/20"
            }`}
          />
          <div
            className={`h-1.5 rounded-full flex-1 ${
              isPrimary ? "bg-gold/30" : "bg-navy/15"
            }`}
          />
        </div>
        <div className="h-1 w-4/5 rounded-full bg-border-strong" />
        <div className="h-1 w-full rounded-full bg-border-strong/70" />
        <div className="h-1 w-3/5 rounded-full bg-border-strong/50" />
      </div>

      {/* Bottom corner PDF icon badge */}
      <div className="flex items-center justify-between pt-1 border-t border-border-subtle">
        <span className="text-[8px] font-bold tracking-wider text-danger uppercase">
          PDF
        </span>
        <IconFileTypePdf size={14} className="text-danger opacity-80" />
      </div>

      {/* Primary indicator ribbon corner */}
      {isPrimary && (
        <div className="absolute top-0 right-0 w-4 h-4 bg-gold flex items-center justify-center rounded-bl-md shadow-xs">
          <IconStar size={9} className="text-white fill-white" />
        </div>
      )}
    </div>
  );
}

// ── Main Card (List View Only) ────────────────────────────────────────────────

export function CvCard({
  cv,
  isDeleting = false,
  onStartDelete,
  onCancelDelete,
}: CvCardProps) {
  const [isRenaming, setIsRenaming] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const selectPrimary = useSelectPrimaryCv();

  const fileSizeKb = cv.fileSizeBytes ? Math.round(cv.fileSizeBytes / 1024) : null;
  const displayTitle = cv.title || "CV chưa đặt tên";
  const uploadDate = new Date(cv.uploadedAt).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });

  return (
    <article
      className={`group transition-all duration-300 rounded-[1.75rem] p-1 ${
        cv.isPrimary
          ? "bg-gradient-to-br from-gold/30 via-gold/10 to-navy/5 border border-gold/40 shadow-sm"
          : "bg-navy/5 border border-navy/10 hover:border-navy/20 hover:shadow-sm"
      }`}
    >
      <div className="rounded-[calc(1.75rem-0.25rem)] bg-white p-5 space-y-4">
        {/* Main Header / Info row */}
        <div className="flex items-start gap-4">
          {/* Document visual thumbnail */}
          <DocumentThumbnail isPrimary={cv.isPrimary} />

          {/* Info Details */}
          <div className="flex-1 min-w-0 space-y-2">
            {/* Title & Rename */}
            {isRenaming ? (
              <RenameInput
                initial={displayTitle}
                cvId={cv.id}
                onDone={() => setIsRenaming(false)}
              />
            ) : (
              <div className="flex items-center gap-2 min-w-0">
                <h3 className="text-base font-bold text-navy truncate leading-snug">
                  {displayTitle}
                </h3>
                <button
                  type="button"
                  title="Đổi tên hồ sơ"
                  onClick={() => setIsRenaming(true)}
                  className="shrink-0 p-1.5 rounded-lg text-ink-muted hover:text-navy hover:bg-surface-low transition-colors"
                >
                  <IconPencil size={14} />
                </button>
              </div>
            )}

            {/* Meta tags */}
            <div className="flex flex-wrap items-center gap-y-1 gap-x-2 text-xs text-ink-muted">
              <span>Đã tải lên: {uploadDate}</span>
              {fileSizeKb && (
                <>
                  <span>&middot;</span>
                  <span>{fileSizeKb} KB</span>
                </>
              )}
              {cv.isPrimary && (
                <>
                  <span>&middot;</span>
                  <span className="text-gold font-semibold">Hồ sơ ứng tuyển chính</span>
                </>
              )}
            </div>

            {/* Badges container */}
            <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
              {cv.isPrimary && <PrimaryBadge />}
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-navy/5 text-navy border border-navy/10">
                File PDF
              </span>
            </div>
          </div>

          {/* Quick tool icons */}
          <div className="shrink-0 flex items-center gap-1">
            {cv.fileUrl && (
              <a
                href={cv.fileUrl}
                target="_blank"
                rel="noreferrer"
                title="Tải về file PDF gốc"
                className="p-2 rounded-xl text-ink-muted hover:text-navy hover:bg-surface-low transition-colors"
              >
                <IconCloudDownload size={18} />
              </a>
            )}
            <button
              type="button"
              title="Xóa hồ sơ"
              onClick={isDeleting ? onCancelDelete : onStartDelete}
              className={`p-2 rounded-xl transition-colors ${
                isDeleting
                  ? "bg-danger/15 text-danger"
                  : "text-ink-muted hover:text-danger hover:bg-danger/8"
              }`}
            >
              <IconTrash size={18} />
            </button>
          </div>
        </div>

        {/* Delete Confirmation Alert (Lifted state) */}
        {isDeleting && (
          <DeleteConfirmBanner
            cvId={cv.id}
            title={displayTitle}
            onCancel={onCancelDelete || (() => {})}
          />
        )}

        {/* Action Button Bar */}
        <div className="pt-3 border-t border-border-subtle flex flex-wrap items-center justify-between gap-2.5">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setShowAnalysis((v) => !v)}
              className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border text-xs font-semibold transition-all active:scale-[0.98] ${
                showAnalysis
                  ? "border-navy bg-navy/5 text-navy font-bold"
                  : "border-border-strong bg-surface-low text-ink-variant hover:border-navy/30 hover:text-navy hover:bg-surface"
              }`}
            >
              <IconChartBar size={14} className={showAnalysis ? "text-navy" : "text-gold"} />
              <span>Xem điểm đánh giá</span>
              {showAnalysis ? <IconChevronUp size={14} /> : <IconChevronDown size={14} />}
            </button>
          </div>

          {/* Set as Primary Button */}
          {!cv.isPrimary && (
            <button
              type="button"
              onClick={() => selectPrimary.mutate(cv.id)}
              disabled={selectPrimary.isPending}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-gold/30 bg-gold/10 text-xs font-bold text-gold hover:bg-gold/20 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              <IconStar size={14} />
              <span>{selectPrimary.isPending ? "Đang xử lý..." : "Đặt làm CV chính"}</span>
            </button>
          )}
        </div>

        {/* Analysis Drawer Panel */}
        {showAnalysis && (
          <div className="pt-4 border-t border-border-subtle">
            <CvAnalysisPanel cvId={cv.id} />
          </div>
        )}
      </div>
    </article>
  );
}
