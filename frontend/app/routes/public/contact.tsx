import { useState } from "react";
import { IconPhone, IconMail, IconMapPin } from "@tabler/icons-react";
import { Field, Input, Button } from "~/components/ui";
import { useUIStore } from "~/stores/useUIStore";

export default function ContactPage() {
  const showToast = useUIStore((s) => s.showToast);
  const [sending, setSending] = useState(false);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSending(true);
    window.setTimeout(() => {
      setSending(false);
      showToast("Đã gửi liên hệ. Chúng tôi sẽ phản hồi trong 24 giờ.", "success");
      (e.target as HTMLFormElement).reset();
    }, 600);
  };

  return (
    <div className="container-page mx-auto px-margin-mobile py-16 md:px-margin-desktop">
      <header className="mx-auto max-w-2xl text-center">
        <h1 className="text-headline text-navy">Liên hệ</h1>
        <p className="mt-4 text-body-lg text-ink-variant">
          Đội ngũ hỗ trợ của FutureCV luôn sẵn sàng giải đáp mọi thắc mắc của bạn.
        </p>
      </header>

      <div className="mt-12 grid grid-cols-1 gap-8 lg:grid-cols-3">
        <div className="flex flex-col gap-6">
          {[
            { icon: IconPhone, label: "Hotline", value: "1900 068 889 (Nhánh 2)" },
            { icon: IconMail, label: "Email", value: "hotro@futurecv.vn" },
            { icon: IconMapPin, label: "Địa chỉ", value: "Tầng 12, Tòa nhà Sông Đà, Mỹ Đình, Hà Nội" },
          ].map((item) => (
            <div
              key={item.label}
              className="flex items-start gap-4 rounded-default border border-border-subtle bg-surface p-6 shadow-surface"
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-navy-secondary/5">
                <item.icon size={22} stroke={1.6} className="text-navy" />
              </div>
              <div>
                <h2 className="font-semibold text-navy">{item.label}</h2>
                <p className="mt-1 text-ink-variant">{item.value}</p>
              </div>
            </div>
          ))}
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-5 rounded-default border border-border-subtle bg-surface p-8 shadow-surface lg:col-span-2"
        >
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            <Field label="Họ và tên" htmlFor="contact-name" required>
              <Input id="contact-name" name="name" placeholder="Nguyễn Văn A" required />
            </Field>
            <Field label="Email" htmlFor="contact-email" required>
              <Input id="contact-email" name="email" type="email" placeholder="ban@email.com" required />
            </Field>
          </div>
          <Field label="Nội dung" htmlFor="contact-message" required>
            <textarea
              id="contact-message"
              name="message"
              rows={6}
              required
              placeholder="Mô tả câu hỏi hoặc vấn đề của bạn..."
              className="rounded-default border border-border-strong bg-white px-4 py-3 text-body text-ink outline-none transition-all placeholder:text-ink-muted/70 focus:border-navy focus:ring-2 focus:ring-navy/20"
            />
          </Field>
          <div>
            <Button type="submit" variant="primary" size="lg" disabled={sending}>
              {sending ? "Đang gửi..." : "Gửi liên hệ"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
