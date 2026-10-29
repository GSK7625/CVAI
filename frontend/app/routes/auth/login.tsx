import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import { IconEye, IconEyeOff, IconBrandGoogle, IconBrandFacebook } from "@tabler/icons-react";
import { Field, Input, Button } from "~/components/ui";
import { useLogin } from "~/features/auth/hooks/useLogin";
import { useUIStore } from "~/stores/useUIStore";

export default function LoginPage() {
  const login = useLogin();
  const showToast = useUIStore((s) => s.showToast);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  const validate = () => {
    const next: typeof errors = {};
    if (!email.trim()) next.email = "Vui lòng nhập email hoặc số điện thoại.";
    if (!password) next.password = "Vui lòng nhập mật khẩu.";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    login.mutate(
      { email: email.trim(), password },
      { onError: (error) => showToast(error.message, "error") },
    );
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-ink">Đăng nhập</h1>
        <p className="mt-1 text-label-sm text-ink-muted">Chào mừng bạn quay trở lại với tương lai sự nghiệp.</p>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2.5">
        <button
          type="button"
          onClick={() => showToast("Đăng nhập Google sẽ ra mắt sớm.", "info")}
          className="flex h-10 items-center justify-center gap-2 rounded-default bg-navy px-3 text-label-sm font-semibold text-white shadow-sm transition-all hover:bg-navy-secondary active:scale-[0.98]"
        >
          <IconBrandGoogle size={18} />
          Google
        </button>
        <button
          type="button"
          onClick={() => showToast("Đăng nhập Facebook sẽ ra mắt sớm.", "info")}
          className="flex h-10 items-center justify-center gap-2 rounded-default bg-[#1877F2] px-3 text-label-sm font-semibold text-white shadow-sm transition-all hover:bg-[#166fe5] active:scale-[0.98]"
        >
          <IconBrandFacebook size={18} />
          Facebook
        </button>
      </div>

      <div className="mb-4 flex items-center gap-3" aria-hidden>
        <div className="h-px flex-1 bg-border-strong" />
        <span className="text-[11px] uppercase tracking-wider text-ink-muted">Hoặc</span>
        <div className="h-px flex-1 bg-border-strong" />
      </div>

      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <Field label="Email" htmlFor="login-email" error={errors.email} required>
          <Input
            id="login-email"
            type="email"
            inputSize="md"
            autoComplete="email"
            placeholder="Nhập email của bạn"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>

        <Field label="Mật khẩu" htmlFor="login-password" error={errors.password} required>
          <div className="relative">
            <Input
              id="login-password"
              type={showPassword ? "text" : "password"}
              inputSize="md"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="pr-12"
            />
            <button
              type="button"
              aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-ink-muted transition-colors hover:text-navy"
              onClick={() => setShowPassword((v) => !v)}
            >
              {showPassword ? <IconEyeOff size={18} stroke={1.6} /> : <IconEye size={18} stroke={1.6} />}
            </button>
          </div>
        </Field>

        <div className="flex justify-end">
          <Link to="/forgot-password" className="text-label-sm font-semibold text-navy hover:underline">
            Quên mật khẩu?
          </Link>
        </div>

        <button
          type="submit"
          disabled={login.isPending}
          className="mt-1 flex h-10 w-full items-center justify-center rounded-default bg-navy px-4 font-bold !text-white shadow-sm transition-all hover:bg-navy-secondary active:scale-[0.98] disabled:opacity-50"
        >
          <span className="font-bold !text-white">{login.isPending ? "Đang đăng nhập..." : "Đăng nhập"}</span>
        </button>
      </form>

      <div className="mt-5 space-y-3 text-center text-label-sm">
        <p className="text-ink-variant">
          Bạn chưa có tài khoản?{" "}
          <Link to="/register" className="font-semibold text-navy underline decoration-gold hover:text-gold">
            Đăng ký ngay
          </Link>
        </p>
        <p className="text-ink-muted">
          Bạn là nhà tuyển dụng?{" "}
          <Link to="/login-employer" className="font-semibold text-navy hover:underline">
            Đăng nhập nhà tuyển dụng
          </Link>
        </p>
      </div>
    </div>
  );
}
