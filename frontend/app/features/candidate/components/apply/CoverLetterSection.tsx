/**
 * @file CoverLetterSection.tsx
 * @description Phần nhập thư giới thiệu ứng tuyển (FC-81a).
 * @architecture Double-bezel nesting, textarea giới hạn 1500 ký tự với bộ đếm ký tự.
 */

interface CoverLetterSectionProps {
  value: string;
  onChange: (value: string) => void;
}

export function CoverLetterSection({ value, onChange }: CoverLetterSectionProps) {
  return (
    <div className="p-1.5 rounded-[2rem] bg-navy/5 border border-navy/10">
      <div className="p-6 sm:p-8 bg-white rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.8)]">
        <div className="border-b border-navy/5 pb-4 mb-4">
          <h2 className="text-base font-bold text-navy">
            3. Thư giới thiệu (Không bắt buộc)
          </h2>
          <p className="text-xs text-ink-variant mt-0.5">
            Chia sẻ ngắn gọn lý do bạn phù hợp và hào hứng với vị trí này
          </p>
        </div>

        <div className="relative">
          <textarea
            rows={5}
            value={value}
            maxLength={1500}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Kính gửi Nhà tuyển dụng, tôi quan tâm đến vị trí này bởi vì..."
            className="w-full rounded-xl border border-navy/15 bg-surface-low/40 p-4 text-sm text-navy outline-none transition-all placeholder:text-ink-muted focus:border-navy focus:bg-white focus:ring-2 focus:ring-navy/10"
          />
          <div className="mt-1 text-right text-[11px] text-ink-muted">
            {value.length} / 1500 ký tự
          </div>
        </div>
      </div>
    </div>
  );
}
