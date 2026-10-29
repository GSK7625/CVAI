import { Link } from "react-router";
import { IconTarget, IconShieldCheck, IconRocket } from "@tabler/icons-react";

const values = [
  {
    icon: IconTarget,
    title: "Sứ mệnh",
    description:
      "Kết nối ứng viên Việt Nam với cơ hội việc làm phù hợp nhất thông qua công nghệ AI.",
  },
  {
    icon: IconShieldCheck,
    title: "Uy tín",
    description:
      "Mọi tin tuyển dụng đều được kiểm duyệt để đảm bảo môi trường làm việc minh bạch, an toàn.",
  },
  {
    icon: IconRocket,
    title: "Tương lai",
    description:
      "Công cụ tạo CV online và gợi ý nghề nghiệp thông minh giúp bạn tiến nhanh trên lộ trình sự nghiệp.",
  },
];

export default function AboutPage() {
  return (
    <div className="container-page mx-auto px-margin-mobile py-16 md:px-margin-desktop">
      <header className="mx-auto max-w-2xl text-center">
        <h1 className="text-headline text-navy">Về FutureCV</h1>
        <p className="mt-4 text-body-lg text-ink-variant">
          Nền tảng tìm việc làm và tạo CV online, đồng hành cùng ứng viên và doanh nghiệp Việt Nam.
        </p>
      </header>

      <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
        {values.map((item) => (
          <article
            key={item.title}
            className="rounded-default border border-border-subtle bg-surface p-8 text-center shadow-surface"
          >
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-navy-secondary/5">
              <item.icon size={26} stroke={1.6} className="text-navy" />
            </div>
            <h2 className="mb-2 text-headline-md text-navy">{item.title}</h2>
            <p className="text-ink-variant">{item.description}</p>
          </article>
        ))}
      </div>

      <div className="mt-12 rounded-xl bg-navy px-8 py-12 text-center text-white">
        <h2 className="text-headline-md">Sẵn sàng bắt đầu hành trình sự nghiệp?</h2>
        <p className="mx-auto mt-3 max-w-xl text-white/70">
          Tạo tài khoản miễn phí hôm nay để tiếp cận hàng nghìn cơ hội việc làm.
        </p>
        <Link
          to="/register"
          className="mt-6 inline-flex rounded-default bg-gold px-8 py-3 font-semibold text-white transition-colors hover:bg-[#b08233]"
        >
          Đăng ký ngay
        </Link>
      </div>
    </div>
  );
}
