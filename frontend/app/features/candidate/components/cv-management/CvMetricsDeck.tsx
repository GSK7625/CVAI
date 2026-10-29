/**
 * @file CvMetricsDeck.tsx
 * @description Hàng 3 thẻ Bento Metrics Deck (Tổng số CV, CV chính, Điểm đánh giá chất lượng).
 * Design: Midnight & Gold, @tabler/icons-react.
 */

import { IconFileText, IconStar, IconChartBar } from "@tabler/icons-react";
import type { CvResponse } from "../../types";

interface CvMetricsDeckProps {
  cvs: CvResponse[];
  primaryCv?: CvResponse;
}

export function CvMetricsDeck({ cvs, primaryCv }: CvMetricsDeckProps) {
  return (
    <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {/* Metric 1: Tổng số CV */}
      <div className="p-5 rounded-2xl border border-border-subtle bg-surface shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-ink-muted">Tổng số hồ sơ</span>
          <div className="w-8 h-8 rounded-xl bg-navy/5 flex items-center justify-center text-navy">
            <IconFileText size={18} />
          </div>
        </div>
        <div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold text-navy">{cvs.length}</span>
            <span className="text-xs font-semibold text-ink-muted">bản CV đã lưu</span>
          </div>
          <p className="mt-2 text-[11px] text-ink-muted">
            Lưu trữ file an toàn trên máy chủ
          </p>
        </div>
        <p className="text-[11px] text-ink-muted">Dung lượng tối đa 5MB / file PDF</p>
      </div>

      {/* Metric 2: CV chính */}
      <div className="p-5 rounded-2xl border border-border-subtle bg-surface shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-ink-muted">CV chính ứng tuyển</span>
          <div className="w-8 h-8 rounded-xl bg-gold/15 flex items-center justify-center text-gold">
            <IconStar size={18} className="fill-gold" />
          </div>
        </div>
        <div>
          <p className="text-sm font-bold text-navy truncate" title={primaryCv?.title || "Chưa thiết lập"}>
            {primaryCv ? primaryCv.title || "CV chính thức" : "Chưa thiết lập"}
          </p>
          <div className="mt-2 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${primaryCv ? "bg-success" : "bg-warning"}`} />
            <span className="text-[11px] font-medium text-ink-variant">
              {primaryCv ? "Sẵn sàng nộp đơn 1-chạm" : "Khuyên chọn 1 CV làm chính"}
            </span>
          </div>
        </div>
        <p className="text-[11px] text-ink-muted">Tự động tính độ phù hợp khi xem việc làm</p>
      </div>

      {/* Metric 3: Điểm đánh giá chất lượng */}
      <div className="p-5 rounded-2xl border border-border-subtle bg-surface shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-ink-muted">Đánh giá chất lượng</span>
          <div className="w-8 h-8 rounded-xl bg-navy/5 flex items-center justify-center text-navy">
            <IconChartBar size={18} />
          </div>
        </div>
        <div>
          <p className="text-sm font-bold text-navy">Phân tích CV tự động</p>
          <p className="mt-2 text-[11px] text-ink-muted leading-tight">
            Chỉ ra điểm mạnh, điểm yếu và gợi ý cải thiện
          </p>
        </div>
        <p className="text-[11px] text-ink-muted">Hỗ trợ tối ưu hóa nội dung ứng tuyển</p>
      </div>
    </section>
  );
}
