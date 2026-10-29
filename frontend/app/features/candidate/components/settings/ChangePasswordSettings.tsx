import { useState } from "react";
import {
  IconKey,
  IconEye,
  IconEyeOff,
  IconDeviceFloppy,
  IconShieldCheck,
} from "@tabler/icons-react";
import { useAuthStore } from "~/stores/useAuthStore";
import { useUIStore } from "~/stores/useUIStore";
import { Button } from "~/components/ui/Button";
import { Input, Field } from "~/components/ui/Input";

export function ChangePasswordSettings() {
  const user = useAuthStore((s) => s.user);
  const showToast = useUIStore((s) => s.showToast);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const [errors, setErrors] = useState<{
    currentPassword?: string;
    newPassword?: string;
    confirmPassword?: string;
  }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const errs: typeof errors = {};
    if (!currentPassword) {
      errs.currentPassword = "Vui lòng nhập mật khẩu hiện tại";
    }
    if (!newPassword) {
      errs.newPassword = "Vui lòng nhập mật khẩu mới";
    } else if (newPassword.length < 8) {
      errs.newPassword = "Mật khẩu mới phải có ít nhất 8 ký tự";
    }
    if (!confirmPassword) {
      errs.confirmPassword = "Vui lòng xác nhận mật khẩu mới";
    } else if (confirmPassword !== newPassword) {
      errs.confirmPassword = "Mật khẩu xác nhận không khớp với mật khẩu mới";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      showToast("Đổi mật khẩu thành công", "success");
    }, 500);
  };

  return (
    <div className="mx-auto max-w-3xl">
      {/* Outer Shell (Double-Bezel) */}
      <div className="rounded-2xl border border-navy/10 bg-surface/80 p-2 shadow-surface backdrop-blur-sm">
        <div className="rounded-xl border border-border-subtle bg-surface p-6 md:p-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
          <div className="flex items-center gap-3 border-b border-border-subtle pb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy/5 text-navy">
              <IconKey size={22} stroke={1.6} />
            </div>
            <div>
              <h1 className="text-headline-md font-bold text-navy">Thay đổi mật khẩu đăng nhập</h1>
              <p className="text-body-sm text-ink-muted">
                Định kỳ đổi mật khẩu mạnh giúp bảo vệ tài khoản của bạn an toàn hơn
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5 pt-6">
            {/* Email đăng nhập (Read-only) */}
            <Field label="Email đăng nhập" htmlFor="change-pwd-email">
              <Input
                id="change-pwd-email"
                type="email"
                value={user?.email || ""}
                disabled
                readOnly
                aria-disabled="true"
                className="cursor-not-allowed bg-surface-low text-ink-muted border-border-subtle opacity-80"
              />
            </Field>

            {/* Mật khẩu hiện tại */}
            <Field
              label="Mật khẩu hiện tại"
              required
              error={errors.currentPassword}
              htmlFor="current-password"
            >
              <div className="relative">
                <Input
                  id="current-password"
                  type={showCurrent ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => {
                    setCurrentPassword(e.target.value);
                    if (errors.currentPassword) setErrors((prev) => ({ ...prev, currentPassword: undefined }));
                  }}
                  placeholder="Nhập mật khẩu hiện tại"
                  className="pr-10 bg-surface focus:border-gold focus:ring-gold"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-navy transition-colors"
                  aria-label={showCurrent ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                >
                  {showCurrent ? <IconEyeOff size={18} stroke={1.8} /> : <IconEye size={18} stroke={1.8} />}
                </button>
              </div>
            </Field>

            {/* Mật khẩu mới */}
            <Field
              label="Mật khẩu mới"
              required
              error={errors.newPassword}
              htmlFor="new-password"
            >
              <div className="relative">
                <Input
                  id="new-password"
                  type={showNew ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value);
                    if (errors.newPassword) setErrors((prev) => ({ ...prev, newPassword: undefined }));
                  }}
                  placeholder="Nhập mật khẩu mới (tối thiểu 8 ký tự)"
                  className="pr-10 bg-surface focus:border-gold focus:ring-gold"
                />
                <button
                  type="button"
                  onClick={() => setShowNew((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-navy transition-colors"
                  aria-label={showNew ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                >
                  {showNew ? <IconEyeOff size={18} stroke={1.8} /> : <IconEye size={18} stroke={1.8} />}
                </button>
              </div>
            </Field>

            {/* Nhập lại mật khẩu mới */}
            <Field
              label="Nhập lại mật khẩu mới"
              required
              error={errors.confirmPassword}
              htmlFor="confirm-password"
            >
              <div className="relative">
                <Input
                  id="confirm-password"
                  type={showConfirm ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    if (errors.confirmPassword) setErrors((prev) => ({ ...prev, confirmPassword: undefined }));
                  }}
                  placeholder="Nhập lại mật khẩu mới"
                  className="pr-10 bg-surface focus:border-gold focus:ring-gold"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-navy transition-colors"
                  aria-label={showConfirm ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                >
                  {showConfirm ? <IconEyeOff size={18} stroke={1.8} /> : <IconEye size={18} stroke={1.8} />}
                </button>
              </div>
            </Field>

            <div className="rounded-lg bg-surface-low/50 p-3.5 border border-border-subtle flex items-start gap-2 text-label-sm text-ink-muted">
              <IconShieldCheck size={16} stroke={2} className="text-gold shrink-0 mt-0.5" />
              <span>
                Mật khẩu mạnh nên chứa ít nhất 8 ký tự, kết hợp chữ hoa, chữ thường, số và ký tự đặc biệt.
              </span>
            </div>

            <div className="pt-3">
              <Button
                type="submit"
                disabled={isSubmitting}
                className="min-w-[120px] rounded-lg bg-navy px-6 py-2.5 text-label font-semibold text-white shadow-sm transition-all hover:bg-navy-secondary active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Đang lưu...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <IconDeviceFloppy size={18} stroke={1.8} />
                    Lưu
                  </span>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
