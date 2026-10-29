/**
 * @file CvInsightsAside.tsx
 * @description Cột phụ bên phải trang Quản lý CV: Mẹo tối ưu hồ sơ, CV Builder trực tuyến, và Bảo mật thông tin.
 * Design: Midnight & Gold, @tabler/icons-react.
 */

import { Link } from "react-router";
import { IconSparkles, IconTemplate, IconArrowRight, IconLock } from "@tabler/icons-react";

export function CvInsightsAside() {
  return (
    <aside className="lg:col-span-4 space-y-6 lg:sticky lg:top-8">
      {/* Widget 1: Lời khuyên tối ưu CV */}
      <section className="rounded-2xl border border-border-subtle bg-surface p-6 shadow-xs space-y-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gold/15 flex items-center justify-center text-gold">
            <IconSparkles size={18} />
          </div>
          <h2 className="text-sm font-bold text-navy">Mẹo tối ưu hồ sơ</h2>
        </div>
        <p className="text-xs text-ink-muted leading-relaxed">
          Những lưu ý quan trọng giúp hồ sơ của bạn nổi bật trước các nhà tuyển dụng:
        </p>

        <div className="space-y-3 pt-1">
          <div className="flex items-start gap-3 text-xs text-ink-variant leading-relaxed">
            <span className="w-5 h-5 rounded-full bg-navy/8 text-navy font-bold flex items-center justify-center shrink-0 text-[10px]">
              1
            </span>
            <div>
              <strong className="text-navy block">Đặt 1 CV làm hồ sơ chính</strong>
              Hệ thống tự động tính điểm phù hợp (% match) khi bạn duyệt các tin tuyển dụng.
            </div>
          </div>

          <div className="flex items-start gap-3 text-xs text-ink-variant leading-relaxed">
            <span className="w-5 h-5 rounded-full bg-navy/8 text-navy font-bold flex items-center justify-center shrink-0 text-[10px]">
              2
            </span>
            <div>
              <strong className="text-navy block">Kiểm tra điểm chất lượng</strong>
              Bấm "Xem điểm đánh giá" trên từng thẻ CV để xem điểm mạnh, điểm yếu và các kỹ năng gợi ý bổ sung.
            </div>
          </div>

          <div className="flex items-start gap-3 text-xs text-ink-variant leading-relaxed">
            <span className="w-5 h-5 rounded-full bg-navy/8 text-navy font-bold flex items-center justify-center shrink-0 text-[10px]">
              3
            </span>
            <div>
              <strong className="text-navy block">Cập nhật định kỳ</strong>
              Bổ sung các dự án và kinh nghiệm mới nhất để tăng cơ hội nhận được lời mời phỏng vấn.
            </div>
          </div>
        </div>
      </section>

      {/* Widget 2: Khám phá CV Builder Trực Tuyến */}
      <section className="rounded-2xl border border-gold/30 bg-gradient-to-br from-gold/10 via-surface to-navy/5 p-6 shadow-xs space-y-4">
        <div className="space-y-2">
          <div className="w-10 h-10 rounded-xl bg-gold text-white flex items-center justify-center shadow-xs">
            <IconTemplate size={22} />
          </div>
          <h2 className="text-base font-bold text-navy">CV Builder trực tuyến</h2>
          <p className="text-xs text-ink-variant leading-relaxed">
            Bạn muốn tạo bản CV mới ấn tượng? Khám phá thư viện mẫu CV đa ngành nghề, biên tập trực quan và đồng bộ tức thì lên hệ thống.
          </p>
        </div>

        <Link
          to="/cv/templates"
          className="inline-flex items-center justify-between w-full px-4 py-2.5 rounded-xl bg-navy text-white text-xs font-bold hover:bg-navy-secondary transition-all active:scale-[0.98] shadow-xs"
        >
          <span>Xem các mẫu CV đẹp</span>
          <IconArrowRight size={16} />
        </Link>
      </section>

      {/* Widget 3: Bảo mật & Quyền riêng tư */}
      <section className="rounded-2xl border border-border-subtle bg-surface-low p-5 space-y-2.5">
        <div className="flex items-center gap-2 text-xs font-bold text-navy">
          <IconLock size={15} className="text-ink-muted" />
          <span>Bảo mật thông tin</span>
        </div>
        <p className="text-[11px] text-ink-muted leading-relaxed">
          Hồ sơ của bạn được lưu trữ an toàn. Chỉ những nhà tuyển dụng của các vị trí việc làm bạn chủ động ứng tuyển mới có quyền xem thông tin liên hệ.
        </p>
      </section>
    </aside>
  );
}
