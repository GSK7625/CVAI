import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import { IconCircleCheck as CircleCheck } from "@tabler/icons-react";
import { Field, Input, Button } from "~/components/ui";
import { useForgotPassword } from "~/features/auth/hooks/useForgotPassword";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string>();
  const forgot = useForgotPassword();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError("Vui lòng nhập email.");
      return;
    }
    setError(undefined);
    forgot.mutate({ email: email.trim() });
  };

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-headline text-ink">Quên mật khẩu</h1>
        <p className="mt-2 text-ink-variant">
          Nhập email đã đăng ký, chúng tôi sẽ gửi hướng dẫn đặt lại mật khẩu.
        </p>
      </div>

      {forgot.isSuccess ? (
        <div className="rounded-default border border-border-subtle bg-surface p-6 text-center shadow-surface">
          <CircleCheck size={44} stroke={1.5} className="mx-auto text-success" />
          <h2 className="mt-3 text-headline-md text-navy">Đã gửi email hướng dẫn</h2>
          <p className="mt-2 text-label-sm text-ink-variant">
            Vui lòng kiểm tra hộp thư <strong className="text-navy">{email}</strong> và làm theo hướng
            dẫn. Email có hiệu lực trong 15 phút.
          </p>
          <Link
            to="/login"
            className="mt-5 inline-flex h-10 items-center rounded-default bg-navy px-5 text-label-sm font-semibold text-white transition-colors hover:bg-navy-secondary"
          >
            Quay lại đăng nhập
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <Field label="Email" htmlFor="fp-email" error={error} required>
            <Input
              id="fp-email"
              type="email"
              inputSize="md"
              autoComplete="email"
              placeholder="ban@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Field>
          <Button
            type="submit"
            variant="primary"
            size="md"
            disabled={forgot.isPending}
            className="mt-1 h-10 w-full font-bold text-white shadow-sm"
          >
            {forgot.isPending ? "Đang gửi..." : "Gửi hướng dẫn"}
          </Button>
        </form>
      )}

      <p className="mt-5 text-center text-label-sm text-ink-variant">
        Bạn chưa có tài khoản?{" "}
        <Link to="/register" className="font-semibold text-navy underline decoration-gold hover:text-gold">
          Đăng ký ngay
        </Link>
      </p>
    </div>
  );
}
