import { useState } from "react";
import {
  IconBellRinging,
  IconBellPlus,
  IconBulb,
  IconMailFast,
  IconInboxOff,
  IconSparkles,
} from "@tabler/icons-react";
import { Switch } from "~/components/ui/Switch";
import { Button } from "~/components/ui/Button";
import { useUIStore } from "~/stores/useUIStore";

export function JobAlertSettings() {
  const showToast = useUIStore((s) => s.showToast);
  const [aiMatchingAlert, setAiMatchingAlert] = useState(true);

  const handleCreateAlert = () => {
    showToast("Tính năng tạo thông báo tùy chỉnh đang được phát triển", "info");
  };

  const handleToggleAiMatching = (checked: boolean) => {
    setAiMatchingAlert(checked);
    showToast(
      checked
        ? "Đã bật gợi ý việc làm phù hợp từ AI"
        : "Đã tắt gợi ý việc làm phù hợp từ AI",
      "success",
    );
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Outer Shell (Double-Bezel) */}
      <div className="rounded-2xl border border-navy/10 bg-surface/80 p-2 shadow-surface backdrop-blur-sm">
        <div className="rounded-xl border border-border-subtle bg-surface p-6 md:p-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
          <div className="flex items-center gap-3 border-b border-border-subtle pb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy/5 text-navy">
              <IconBellRinging size={22} stroke={1.6} />
            </div>
            <div>
              <h1 className="text-headline-md font-bold text-navy">Cài đặt thông báo việc làm</h1>
              <p className="text-body-sm text-ink-muted">
                Quản lý các thông báo tuyển dụng tự động và nhận việc làm phù hợp từ AI
              </p>
            </div>
          </div>

          <div className="space-y-6 pt-6">
            {/* Khối 3: Tự động gợi ý việc làm phù hợp (Card Toggle) */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-xl border border-gold/30 bg-gradient-to-r from-gold/5 via-surface to-surface p-4 md:p-5 shadow-sm">
              <div className="flex items-start gap-3.5">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gold/15 text-gold">
                  <IconBulb size={22} stroke={1.8} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-label font-bold text-navy">
                      Nhận thông báo việc làm phù hợp
                    </h2>
                    <span className="inline-flex items-center gap-1 rounded-full bg-gold/10 px-2 py-0.5 text-[11px] font-semibold text-gold ring-1 ring-gold/25">
                      <IconSparkles size={12} stroke={2} />
                      AI Powered
                    </span>
                  </div>
                  <p className="mt-1 text-body-sm text-ink-variant">
                    Việc làm được AI lựa chọn dựa trên hồ sơ và kinh nghiệm của bạn
                  </p>
                </div>
              </div>
              <div className="self-end sm:self-center">
                <Switch
                  checked={aiMatchingAlert}
                  onChange={handleToggleAiMatching}
                  ariaLabel="Nhận thông báo việc làm phù hợp từ AI"
                />
              </div>
            </div>

            {/* Khối 2: Banner hành động (Call to Action Card) */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 rounded-xl border border-navy/15 bg-surface-low/50 p-5 md:p-6">
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-navy text-white shadow-sm">
                  <IconMailFast size={26} stroke={1.6} />
                </div>
                <div>
                  <h3 className="text-body font-bold text-navy">
                    Bạn vẫn chưa tìm được công việc ưng ý?
                  </h3>
                  <p className="mt-1 text-body-sm text-ink-muted">
                    Đăng ký nhận thông báo ngay để không bỏ lỡ cơ hội mới nhất từ các nhà tuyển dụng hàng đầu.
                  </p>
                </div>
              </div>

              <Button
                type="button"
                onClick={handleCreateAlert}
                className="shrink-0 gap-2 rounded-lg bg-gold px-5 py-2.5 text-label font-semibold text-navy shadow-sm transition-all hover:bg-gold/90 active:scale-[0.98]"
              >
                <IconBellPlus size={18} stroke={2} />
                Tạo thông báo việc làm
              </Button>
            </div>

            {/* Khối 1: Trạng thái trống (Empty State) */}
            <div className="rounded-xl border border-dashed border-border-strong bg-surface-low/20 py-12 px-4 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-navy/5 text-ink-muted mb-3">
                <IconInboxOff size={28} stroke={1.5} />
              </div>
              <p className="text-body font-medium text-navy">
                Bạn chưa tạo thông báo việc làm nào
              </p>
              <p className="mt-1 text-body-sm text-ink-muted max-w-sm mx-auto">
                Khi bạn tạo thông báo việc làm theo từ khoá, địa điểm và mức lương, danh sách thiết lập sẽ hiển thị tại đây.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
