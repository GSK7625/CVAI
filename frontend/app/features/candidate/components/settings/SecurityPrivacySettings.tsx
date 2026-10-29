import { useState } from "react";
import { Link } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import {
  IconShieldLock,
  IconCookie,
  IconChevronDown,
  IconInfoCircle,
  IconExternalLink,
  IconCheck,
} from "@tabler/icons-react";
import { Switch } from "~/components/ui/Switch";
import { Button } from "~/components/ui/Button";
import { useUIStore } from "~/stores/useUIStore";
import { cn } from "~/lib/cn";

export function SecurityPrivacySettings() {
  const showToast = useUIStore((s) => s.showToast);

  // State các toggle quyền riêng tư
  const [privacySettings, setPrivacySettings] = useState({
    jobOpportunities: true,
    cvReviewSupport: true,
    partnerDataSharing: false,
  });

  // State cookie toggles
  const [cookieSettings, setCookieSettings] = useState({
    performance: true,
    advertising: false,
  });

  // Toggle mở rộng mô tả chi tiết cookie
  const [showCookieDetails, setShowCookieDetails] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSave = () => {
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      showToast("Đã cập nhật cài đặt bảo mật & Cookie thành công", "success");
    }, 400);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Phân hệ A: Cài đặt quyền riêng tư & cơ hội việc làm */}
      <div className="rounded-2xl border border-navy/10 bg-surface/80 p-2 shadow-surface backdrop-blur-sm">
        <div className="rounded-xl border border-border-subtle bg-surface p-6 md:p-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
          <div className="flex items-center gap-3 border-b border-border-subtle pb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy/5 text-navy">
              <IconShieldLock size={22} stroke={1.6} />
            </div>
            <div>
              <h1 className="text-headline-md font-bold text-navy">Thay đổi cài đặt bảo mật</h1>
              <p className="text-body-sm text-ink-muted">
                Quản lý quyền riêng tư và khả năng hiển thị hồ sơ của bạn với nhà tuyển dụng
              </p>
            </div>
          </div>

          <div className="divide-y divide-border-subtle pt-3">
            {/* Toggle 1: Cơ hội việc làm */}
            <div className="flex items-start justify-between gap-4 py-5">
              <div className="space-y-1 pr-2">
                <p className="text-label font-semibold text-navy">
                  Nhận cơ hội việc làm tốt hơn từ hệ thống
                </p>
                <p className="text-body-sm text-ink-variant leading-relaxed">
                  Nhận cơ hội việc làm với mức lương cao hơn 20 - 50% lương hiện tại. Mỗi khi có công việc
                  phù hợp, hệ thống sẽ gửi thông báo tới bạn qua email hoặc điện thoại.
                </p>
              </div>
              <Switch
                checked={privacySettings.jobOpportunities}
                onChange={(checked) =>
                  setPrivacySettings((prev) => ({ ...prev, jobOpportunities: checked }))
                }
                ariaLabel="Nhận cơ hội việc làm tốt hơn từ hệ thống"
              />
            </div>

            {/* Toggle 2: Đánh giá CV */}
            <div className="flex items-start justify-between gap-4 py-5">
              <div className="space-y-1 pr-2">
                <p className="text-label font-semibold text-navy">
                  Cho phép hỗ trợ sửa và đánh giá CV
                </p>
                <p className="text-body-sm text-ink-variant leading-relaxed">
                  Hỗ trợ bạn cải thiện chất lượng CV và tối ưu từ khoá để tăng tỷ lệ được mời phỏng vấn.
                </p>
              </div>
              <Switch
                checked={privacySettings.cvReviewSupport}
                onChange={(checked) =>
                  setPrivacySettings((prev) => ({ ...prev, cvReviewSupport: checked }))
                }
                ariaLabel="Cho phép hỗ trợ sửa và đánh giá CV"
              />
            </div>

            {/* Toggle 3: Chia sẻ dữ liệu đối tác */}
            <div className="flex items-start justify-between gap-4 py-5">
              <div className="space-y-2 pr-2">
                <p className="text-label font-semibold text-navy">
                  Cho phép chia sẻ dữ liệu cho Đối tác hệ sinh thái để sử dụng quyền lợi khoá học từ đối
                  tác khi nâng cấp tài khoản
                </p>
                <p className="rounded-lg bg-surface-low/80 p-3 text-label-sm text-ink-variant leading-relaxed border border-border-subtle">
                  <span className="font-semibold text-navy">Lưu ý:</span> Ưu đãi khóa học từ đối tác chỉ
                  được áp dụng khi bạn tích chọn đồng ý chia sẻ dữ liệu. Trường hợp không tích chọn, bạn
                  vẫn có thể nâng cấp tài khoản nhưng sẽ không nhận được các phần quà/quyền lợi đi kèm
                  từ đối tác.
                </p>
              </div>
              <Switch
                checked={privacySettings.partnerDataSharing}
                onChange={(checked) =>
                  setPrivacySettings((prev) => ({ ...prev, partnerDataSharing: checked }))
                }
                ariaLabel="Cho phép chia sẻ dữ liệu cho Đối tác hệ sinh thái"
              />
            </div>
          </div>

          {/* Legal disclaimer link */}
          <div className="mt-4 flex items-start gap-2 border-t border-border-subtle pt-4 text-label-sm text-ink-muted">
            <IconInfoCircle size={16} stroke={1.8} className="shrink-0 text-gold mt-0.5" />
            <p>
              Tìm hiểu thêm về{" "}
              <Link
                to="/privacy"
                target="_blank"
                className="font-medium text-navy underline decoration-border-strong hover:text-gold hover:decoration-gold transition-colors"
              >
                Chính sách quyền riêng tư
              </Link>{" "}
              và{" "}
              <Link
                to="/terms"
                target="_blank"
                className="font-medium text-navy underline decoration-border-strong hover:text-gold hover:decoration-gold transition-colors"
              >
                Điều khoản dịch vụ
              </Link>{" "}
              (đã được cập nhật theo các quy định mới nhất của Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15
              về Bảo vệ dữ liệu cá nhân).
            </p>
          </div>
        </div>
      </div>

      {/* Phân hệ B: Cài đặt Cookie */}
      <div className="rounded-2xl border border-navy/10 bg-surface/80 p-2 shadow-surface backdrop-blur-sm">
        <div className="rounded-xl border border-border-subtle bg-surface p-6 md:p-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
          <div className="flex items-center gap-3 border-b border-border-subtle pb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy/5 text-navy">
              <IconCookie size={22} stroke={1.6} />
            </div>
            <div className="flex-1">
              <h2 className="text-headline-md font-bold text-navy">Cài đặt cookie</h2>
              <p className="text-body-sm text-ink-muted">
                Kiểm soát các loại cookie lưu trữ trên trình duyệt của bạn
              </p>
            </div>
          </div>

          <div className="space-y-3 pt-5 text-body-sm text-ink-variant leading-relaxed">
            <p>
              Cookie là công cụ giúp chúng tôi lưu trữ hoặc truy xuất các thông tin cần thiết từ trình duyệt
              của bạn. Thông tin này có thể liên quan đến bạn, sở thích của bạn hoặc thiết bị của bạn và chủ
              yếu được sử dụng để giúp trang web hoạt động như bạn mong đợi.
            </p>
            <p>
              Vì chúng tôi tôn trọng quyền riêng tư của bạn, bạn có thể chọn không cho phép một số loại
              cookie bên dưới. Tuy nhiên, việc chặn một số loại cookie có thể ảnh hưởng đến trải nghiệm của
              bạn trên trang web và các dịch vụ mà chúng tôi có thể cung cấp.
            </p>

            <div>
              <button
                type="button"
                onClick={() => setShowCookieDetails((v) => !v)}
                className="inline-flex items-center gap-1.5 font-semibold text-gold hover:underline text-label-sm pt-1"
              >
                <span>{showCookieDetails ? "Thu gọn mô tả" : "Xem mô tả chi tiết các loại cookie"}</span>
                <IconChevronDown
                  size={15}
                  stroke={2}
                  className={cn("transition-transform duration-200", showCookieDetails && "rotate-180")}
                />
              </button>
            </div>
          </div>

          {/* Danh sách phân loại cookie */}
          <div className="mt-5 space-y-4 border-t border-border-subtle pt-5">
            {/* 1. Cookie thiết yếu */}
            <div className="rounded-xl border border-border-subtle bg-surface-low/40 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-label font-semibold text-navy">Cookie thiết yếu</h3>
                  <p className="text-label-sm text-ink-muted">Bắt buộc cho hoạt động cốt lõi</p>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2.5 py-1 text-label-sm font-semibold text-success ring-1 ring-success/20">
                  <IconCheck size={13} stroke={2.5} />
                  Luôn hoạt động
                </span>
              </div>
              <AnimatePresence>
                {showCookieDetails && (
                  <motion.p
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mt-3 border-t border-border-subtle/80 pt-3 text-body-sm text-ink-variant leading-relaxed"
                  >
                    Các cookie này thực hiện nhiều hoạt động cần thiết để điều hướng trang web và sử dụng
                    các chức năng của trang. Bạn sẽ không thể sử dụng trang web nếu không cho phép cookie này
                    hoạt động.
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            {/* 2. Cookie hiệu năng */}
            <div className="rounded-xl border border-border-subtle bg-surface-low/40 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-label font-semibold text-navy">
                    Cookie hiệu năng <span className="font-normal text-gold">(Khuyên dùng)</span>
                  </h3>
                  <p className="text-label-sm text-ink-muted">Phân tích trải nghiệm và tăng tốc độ tải trang</p>
                </div>
                <Switch
                  checked={cookieSettings.performance}
                  onChange={(checked) =>
                    setCookieSettings((prev) => ({ ...prev, performance: checked }))
                  }
                  ariaLabel="Bật / Tắt Cookie hiệu năng"
                />
              </div>
              <AnimatePresence>
                {showCookieDetails && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mt-3 border-t border-border-subtle/80 pt-3 text-body-sm text-ink-variant leading-relaxed"
                  >
                    Những cookie này cho chúng tôi biết cách bạn sử dụng trang web và giúp chúng tôi cải
                    thiện trang web. Ví dụ giúp tăng tốc độ tải trang để trải nghiệm của bạn tốt hơn, hoặc cá
                    nhân hoá các tính năng để bạn tìm việc, tạo CV, sử dụng các công cụ hiệu quả hơn.{" "}
                    <Link
                      to="/cookie-policy"
                      target="_blank"
                      className="inline-flex items-center gap-0.5 text-navy font-medium underline hover:text-gold"
                    >
                      Xem thêm
                      <IconExternalLink size={12} stroke={2} />
                    </Link>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* 3. Cookie quảng cáo */}
            <div className="rounded-xl border border-border-subtle bg-surface-low/40 p-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-label font-semibold text-navy">Cookie quảng cáo & Đối tác</h3>
                  <p className="text-label-sm text-ink-muted">Cá nhân hoá cơ hội việc làm theo nhu cầu thực tế</p>
                </div>
                <Switch
                  checked={cookieSettings.advertising}
                  onChange={(checked) =>
                    setCookieSettings((prev) => ({ ...prev, advertising: checked }))
                  }
                  ariaLabel="Bật / Tắt Cookie quảng cáo"
                />
              </div>
              <AnimatePresence>
                {showCookieDetails && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mt-3 border-t border-border-subtle/80 pt-3 text-body-sm text-ink-variant leading-relaxed"
                  >
                    Cookie quảng cáo giúp các bên thứ ba như LinkedIn, Facebook, Google,... hiển thị các
                    quảng cáo, cơ hội việc làm hoặc nội dung phù hợp với nhu cầu và sở thích thực tế của bạn
                    thay vì những quảng cáo ngẫu nhiên không liên quan. Chúng tôi cùng chịu trách nhiệm với
                    nền tảng thứ ba về việc thu thập dữ liệu. Sau khi thu thập, nền tảng thứ ba sẽ xử lý dữ
                    liệu theo chính sách quyền riêng tư của họ.{" "}
                    <Link
                      to="/cookie-policy"
                      target="_blank"
                      className="inline-flex items-center gap-0.5 text-navy font-medium underline hover:text-gold"
                    >
                      Xem thêm
                      <IconExternalLink size={12} stroke={2} />
                    </Link>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className="mt-6 pt-3">
            <Button
              type="button"
              disabled={isSubmitting}
              onClick={handleSave}
              className="min-w-[120px] rounded-lg bg-navy px-6 py-2.5 text-label font-semibold text-white shadow-sm transition-all hover:bg-navy-secondary active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Đang lưu..." : "Lưu cài đặt"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
