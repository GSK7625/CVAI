import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router";
import {
  IconCircleCheck as CircleCheck,
  IconAlertCircle,
  IconEye,
  IconEyeOff,
  IconArrowLeft,
} from "@tabler/icons-react";
import { Field, Input, Button } from "~/components/ui";
import { useResetPassword } from "~/features/auth/hooks/useResetPassword";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email") ?? "";
  const token = searchParams.get("token") ?? "";

  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<{ newPassword?: string; confirmNewPassword?: string }>({});

  const resetPassword = useResetPassword();

  const isMissingParams = !email.trim() || !token.trim();

  const validate = () => {
    const next: typeof errors = {};
    if (!newPassword) {
      next.newPassword = "Vui lòng nhập mật khẩu mới.";
    } else if (newPassword.length < 6 || newPassword.length > 25) {
      next.newPassword = "Mật khẩu mới phải có độ dài từ 6 đến 25 ký tự.";
    } else if (!/[A-Z]/.test(newPassword)) {
      next.newPassword = "Mật khẩu phải chứa ít nhất một chữ cái in hoa (A-Z).";
    } else if (!/[a-z]/.test(newPassword)) {
      next.newPassword = "Mật khẩu phải chứa ít nhất một chữ cái viết thường (a-z).";
    } else if (!/[0-9]/.test(newPassword)) {
      next.newPassword = "Mật khẩu phải chứa ít nhất một chữ số (0-9).";
    }

    if (!confirmNewPassword) {
      next.confirmNewPassword = "Vui lòng xác nhận mật khẩu mới.";
    } else if (confirmNewPassword !== newPassword) {
      next.confirmNewPassword = "Mật khẩu xác nhận không khớp.";
    }

    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    resetPassword.mutate({
      email: email.trim(),
      token: token.trim(),
      newPassword,
      confirmNewPassword,
    });
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-headline text-ink">Đặt lại mật khẩu</h1>
        <p className="mt-2 text-ink-variant">
          {email ? (
            <>
              Thiết lập mật khẩu mới cho tài khoản <strong className="text-navy">{email}</strong>.
            </>
          ) : (
            "Vui lòng nhập mật khẩu mới cho tài khoản của bạn."
          )}
        </p>
      </div>

      {isMissingParams ? (
        <div className="rounded-default border border-border-subtle bg-surface p-6 text-center shadow-surface">
          <IconAlertCircle size={44} stroke={1.5} className="mx-auto text-danger" />
          <h2 className="mt-3 text-headline-md text-navy">Liên kết không hợp lệ hoặc thiếu thông tin</h2>
          <p className="mt-2 text-label-sm text-ink-variant">
            Liên kết đặt lại mật khẩu không có đủ mã xác thực hoặc đã hết hạn (chỉ có hiệu lực trong 15 phút).
          </p>
          <div className="mt-6 flex flex-col gap-2.5 sm:flex-row sm:justify-center">
            <Link
              to="/forgot-password"
              className="inline-flex h-10 items-center justify-center rounded-default bg-navy px-5 text-label-sm font-semibold text-white transition-colors hover:bg-navy-secondary"
            >
              Gửi lại yêu cầu mới
            </Link>
            <Link
              to="/login"
              className="inline-flex h-10 items-center justify-center gap-1.5 rounded-default border border-border-subtle bg-surface px-4 text-label-sm font-semibold text-ink transition-colors hover:bg-surface-variant"
            >
              <IconArrowLeft size={16} /> Quay lại đăng nhập
            </Link>
          </div>
        </div>
      ) : resetPassword.isSuccess ? (
        <div className="rounded-default border border-border-subtle bg-surface p-6 text-center shadow-surface">
          <CircleCheck size={44} stroke={1.5} className="mx-auto text-success" />
          <h2 className="mt-3 text-headline-md text-navy">Đổi mật khẩu thành công!</h2>
          <p className="mt-2 text-label-sm text-ink-variant">
            Mật khẩu mới đã được cập nhật an toàn. Bạn có thể sử dụng mật khẩu mới để đăng nhập ngay bây giờ.
          </p>
          <Link
            to="/login"
            className="mt-6 inline-flex h-10 items-center rounded-default bg-navy px-6 text-label-sm font-semibold text-white transition-colors hover:bg-navy-secondary"
          >
            Đăng nhập ngay
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <Field
            label="Mật khẩu mới"
            htmlFor="rp-new-password"
            error={errors.newPassword}
            hint="Từ 6-25 ký tự, bao gồm chữ hoa (A-Z), chữ thường (a-z) và số (0-9)"
            required
          >
            <div className="relative">
              <Input
                id="rp-new-password"
                type={showNewPassword ? "text" : "password"}
                inputSize="md"
                autoComplete="new-password"
                placeholder="Nhập mật khẩu mới"
                value={newPassword}
                onChange={(e) => {
                  setNewPassword(e.target.value);
                  if (errors.newPassword) setErrors((prev) => ({ ...prev, newPassword: undefined }));
                }}
                className="pr-12"
              />
              <button
                type="button"
                aria-label={showNewPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-ink-muted transition-colors hover:text-navy"
                onClick={() => setShowNewPassword((v) => !v)}
              >
                {showNewPassword ? <IconEyeOff size={18} stroke={1.6} /> : <IconEye size={18} stroke={1.6} />}
              </button>
            </div>
          </Field>

          <Field
            label="Xác nhận mật khẩu mới"
            htmlFor="rp-confirm-password"
            error={errors.confirmNewPassword}
            required
          >
            <div className="relative">
              <Input
                id="rp-confirm-password"
                type={showConfirmPassword ? "text" : "password"}
                inputSize="md"
                autoComplete="new-password"
                placeholder="Nhập lại mật khẩu mới"
                value={confirmNewPassword}
                onChange={(e) => {
                  setConfirmNewPassword(e.target.value);
                  if (errors.confirmNewPassword)
                    setErrors((prev) => ({ ...prev, confirmNewPassword: undefined }));
                }}
                className="pr-12"
              />
              <button
                type="button"
                aria-label={showConfirmPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-ink-muted transition-colors hover:text-navy"
                onClick={() => setShowConfirmPassword((v) => !v)}
              >
                {showConfirmPassword ? <IconEyeOff size={18} stroke={1.6} /> : <IconEye size={18} stroke={1.6} />}
              </button>
            </div>
          </Field>

          <Button
            type="submit"
            variant="primary"
            size="md"
            disabled={resetPassword.isPending}
            className="mt-2 h-10 w-full font-bold text-white shadow-sm"
          >
            {resetPassword.isPending ? "Đang xử lý..." : "Cập nhật mật khẩu"}
          </Button>

          <div className="mt-2 text-center">
            <Link
              to="/login"
              className="inline-flex items-center gap-1 text-label-sm font-semibold text-navy hover:underline"
            >
              <IconArrowLeft size={16} /> Quay lại đăng nhập
            </Link>
          </div>
        </form>
      )}
    </div>
  );
}
