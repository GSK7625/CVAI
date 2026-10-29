import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import { IconEye, IconEyeOff, IconBrandGoogle, IconBrandFacebook, IconUser, IconBriefcase } from "@tabler/icons-react";
import { Field, Input } from "~/components/ui";
import { useRegister } from "~/features/auth/hooks/useRegister";
import { useUIStore } from "~/stores/useUIStore";

interface FormErrors {
  fullName?: string;
  email?: string;
  phoneNumber?: string;
  gender?: string;
  companyName?: string;
  password?: string;
  confirmPassword?: string;
}

type AccountType = "candidate" | "employer";

export default function RegisterPage() {
  const register = useRegister();
  const showToast = useUIStore((s) => s.showToast);

  const [accountType, setAccountType] = useState<AccountType>("candidate");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [gender, setGender] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const validate = () => {
    const next: FormErrors = {};
    if (!fullName.trim()) next.fullName = "Vui lòng nhập họ và tên.";
    if (!email.trim()) {
      next.email = "Vui lòng nhập email.";
    } else if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      next.email = "Email chưa đúng định dạng.";
    }
    if (accountType === "employer") {
      if (!phoneNumber.trim()) {
        next.phoneNumber = "Vui lòng nhập số điện thoại.";
      } else if (!/^0\d{9}$/.test(phoneNumber.trim())) {
        next.phoneNumber = "Số điện thoại phải có 10 chữ số và bắt đầu bằng 0.";
      }
      if (!gender.trim()) {
        next.gender = "Vui lòng chọn giới tính.";
      }
      if (!companyName.trim()) {
        next.companyName = "Vui lòng nhập tên công ty.";
      }
    }
    if (!password) {
      next.password = "Vui lòng nhập mật khẩu.";
    } else if (password.length < 6) {
      next.password = "Mật khẩu cần ít nhất 6 ký tự.";
    } else if (!/[A-Z]/.test(password)) {
      next.password = "Mật khẩu phải có ít nhất 1 chữ hoa.";
    } else if (!/[a-z]/.test(password)) {
      next.password = "Mật khẩu phải có ít nhất 1 chữ thường.";
    } else if (!/[0-9]/.test(password)) {
      next.password = "Mật khẩu phải có ít nhất 1 chữ số.";
    }
    if (confirmPassword !== password) {
      next.confirmPassword = "Mật khẩu xác nhận không khớp.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    register.mutate(
      {
        fullName: fullName.trim(),
        email: email.trim(),
        phoneNumber: phoneNumber.trim(),
        gender: gender.trim(),
        companyName: companyName.trim(),
        password,
        confirmPassword,
        accountType
      },
      { onError: (error) => showToast(error.message, "error") },
    );
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-ink">Đăng ký</h1>
        <p className="mt-1 text-label-sm text-ink-muted">Tạo tài khoản miễn phí chỉ với vài bước.</p>
      </div>

      {/* Account Type Selection */}
      <div className="mb-5">
        <label className="mb-2 block text-label-sm font-semibold text-ink">Loại tài khoản</label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setAccountType("candidate")}
            className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-all ${
              accountType === "candidate"
                ? "border-navy bg-navy/5 shadow-sm"
                : "border-border-strong bg-background hover:border-navy/30"
            }`}
          >
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-full ${
                accountType === "candidate" ? "bg-navy text-gold" : "bg-background-secondary text-ink-muted"
              }`}
            >
              <IconUser size={24} stroke={1.6} />
            </div>
            <div className="text-center">
              <div className={`text-label-sm font-semibold ${accountType === "candidate" ? "text-navy" : "text-ink"}`}>
                Ứng viên
              </div>
              <div className="text-[11px] text-ink-muted">Tìm việc & Tạo CV</div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => setAccountType("employer")}
            className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-all ${
              accountType === "employer"
                ? "border-navy bg-navy/5 shadow-sm"
                : "border-border-strong bg-background hover:border-navy/30"
            }`}
          >
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-full ${
                accountType === "employer" ? "bg-navy text-gold" : "bg-background-secondary text-ink-muted"
              }`}
            >
              <IconBriefcase size={24} stroke={1.6} />
            </div>
            <div className="text-center">
              <div className={`text-label-sm font-semibold ${accountType === "employer" ? "text-navy" : "text-ink"}`}>
                Nhà tuyển dụng
              </div>
              <div className="text-[11px] text-ink-muted">Đăng tin & Tuyển dụng</div>
            </div>
          </button>
        </div>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2.5">
        <button
          type="button"
          onClick={() => showToast("Đăng ký Google sẽ ra mắt sớm.", "info")}
          className="flex h-10 items-center justify-center gap-2 rounded-default bg-navy px-3 text-label-sm font-semibold text-white shadow-sm transition-all hover:bg-navy-secondary active:scale-[0.98]"
        >
          <IconBrandGoogle size={18} />
          Google
        </button>
        <button
          type="button"
          onClick={() => showToast("Đăng ký Facebook sẽ ra mắt sớm.", "info")}
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

      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-3">
        <Field label="Họ và tên" htmlFor="reg-name" error={errors.fullName} required>
          <Input
            id="reg-name"
            inputSize="md"
            autoComplete="name"
            placeholder="Nguyễn Văn A"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </Field>

        <Field label="Email" htmlFor="reg-email" error={errors.email} required>
          <Input
            id="reg-email"
            type="email"
            inputSize="md"
            autoComplete="email"
            placeholder="ban@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>

        {accountType === "employer" && (
          <>
            <Field label="Số điện thoại" htmlFor="reg-phone" error={errors.phoneNumber} required>
              <Input
                id="reg-phone"
                type="tel"
                inputSize="md"
                autoComplete="tel"
                placeholder="0912345678"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
              />
            </Field>

            <Field label="Giới tính" htmlFor="reg-gender" error={errors.gender} required>
              <select
                id="reg-gender"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="flex h-10 w-full rounded-default border border-border-strong bg-surface px-3 text-body-sm text-ink outline-none ring-offset-background transition-colors hover:border-border-hover focus:border-sky focus:ring-2 focus:ring-sky/20 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="">Chọn giới tính</option>
                <option value="Male">Nam</option>
                <option value="Female">Nữ</option>
              </select>
            </Field>

            <Field label="Tên công ty" htmlFor="reg-company" error={errors.companyName} required>
              <Input
                id="reg-company"
                inputSize="md"
                placeholder="Công ty TNHH ABC"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </Field>
          </>
        )}

        <Field
          label="Mật khẩu"
          htmlFor="reg-password"
          error={errors.password}
          hint="Tối thiểu 8 ký tự"
          required
        >
          <div className="relative">
            <Input
              id="reg-password"
              type={showPassword ? "text" : "password"}
              inputSize="md"
              autoComplete="new-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="pr-11"
            />
            <button
              type="button"
              aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted transition-colors hover:text-navy"
              onClick={() => setShowPassword((v) => !v)}
            >
              {showPassword ? <IconEyeOff size={18} stroke={1.6} /> : <IconEye size={18} stroke={1.6} />}
            </button>
          </div>
        </Field>

        <Field label="Xác nhận mật khẩu" htmlFor="reg-confirm" error={errors.confirmPassword} required>
          <div className="relative">
            <Input
              id="reg-confirm"
              type={showConfirmPassword ? "text" : "password"}
              inputSize="md"
              autoComplete="new-password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="pr-11"
            />
            <button
              type="button"
              aria-label={showConfirmPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted transition-colors hover:text-navy"
              onClick={() => setShowConfirmPassword((v) => !v)}
            >
              {showConfirmPassword ? <IconEyeOff size={18} stroke={1.6} /> : <IconEye size={18} stroke={1.6} />}
            </button>
          </div>
        </Field>

        <button
          type="submit"
          disabled={register.isPending}
          className="mt-1 flex h-10 w-full items-center justify-center rounded-default bg-navy px-4 font-bold !text-white shadow-sm transition-all hover:bg-navy-secondary active:scale-[0.98] disabled:opacity-50"
        >
          <span className="font-bold !text-white">{register.isPending ? "Đang tạo tài khoản..." : "Đăng ký"}</span>
        </button>
      </form>

      <p className="mt-5 text-center text-label-sm text-ink-variant">
        Bạn đã có tài khoản?{" "}
        <Link to="/login" className="font-semibold text-navy underline decoration-gold hover:text-gold">
          Đăng nhập
        </Link>
      </p>
    </div>
  );
}
