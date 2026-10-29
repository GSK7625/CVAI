import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { IconEye, IconEyeOff, IconShield } from "@tabler/icons-react";
import { Field, Input, Button } from "~/components/ui";
import { useLogin } from "~/features/auth/hooks/useLogin";
import { useUIStore } from "~/stores/useUIStore";

export default function LoginAdminPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const login = useLogin();
  const showToast = useUIStore((s) => s.showToast);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  const validate = () => {
    const next: typeof errors = {};
    if (!email.trim()) next.email = "Vui lòng nhập email.";
    if (!password) next.password = "Vui lòng nhập mật khẩu.";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    login.mutate(
      { email: email.trim(), password },
      {
        onError: (error) => showToast(error.message, "error"),
        onSuccess: () => {
          const returnTo = searchParams.get("returnTo");
          if (returnTo?.startsWith("/")) {
            navigate(returnTo, { replace: true });
          } else {
            navigate("/admin", { replace: true });
          }
        },
      },
    );
  };

  return (
    <div>
      <div className="mb-6">
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-navy">
          <IconShield size={24} stroke={1.6} className="text-gold" />
        </div>
        <h1 className="text-2xl font-bold text-ink">Đăng nhập Quản trị viên</h1>
        <p className="mt-1 text-label-sm text-ink-muted">Quản lý hệ thống FutureCV toàn diện.</p>
      </div>

      <div className="mb-6 rounded-lg border border-gold/20 bg-gold/5 px-4 py-3">
        <p className="text-label-sm text-ink-variant">
          <span className="font-semibold text-gold">⚠️ Khu vực bảo mật:</span> Chỉ dành cho quản trị viên hệ thống.
        </p>
      </div>

      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <Field label="Email quản trị" htmlFor="login-admin-email" error={errors.email} required>
          <Input
            id="login-admin-email"
            type="email"
            inputSize="md"
            autoComplete="email"
            placeholder="admin@futurecv.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>

        <Field label="Mật khẩu" htmlFor="login-admin-password" error={errors.password} required>
          <div className="relative">
            <Input
              id="login-admin-password"
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
        <p className="text-ink-muted">
          Quay lại{" "}
          <Link to="/login" className="font-semibold text-navy hover:underline">
            Đăng nhập thường
          </Link>
        </p>
      </div>
    </div>
  );
}
