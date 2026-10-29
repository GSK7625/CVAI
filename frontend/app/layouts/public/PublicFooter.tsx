/**
 * @file PublicFooter.tsx
 * @description Chân trang (Footer) hiển thị thông tin giới thiệu, các nhóm liên kết ứng viên/nhà tuyển dụng và bản quyền.
 * @architecture Tuân thủ SRP (Chỉ quản lý UI chân trang) & OCP (Nạp dữ liệu từ FOOTER_SECTIONS trong navConfig).
 */

import { memo } from "react";
import { Link } from "react-router";

import { FOOTER_SECTIONS } from "./navConfig";

export const PublicFooter = memo(function PublicFooter() {
  return (
    <footer className="mt-auto border-t border-border-subtle bg-navy text-white">
      <div className="container-page mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-4">
          <div className="flex flex-col gap-4">
            <Link to="/" className="flex items-center">
              <img
                src="/Logo.png"
                alt="FutureCV"
                className="h-8 w-auto object-contain brightness-0 invert"
              />
            </Link>
            <p className="text-body-sm text-white/70">
              Nền tảng tuyển dụng và tạo CV ứng dụng AI hàng đầu tại Việt Nam. Kết nối nhân tài với
              hàng nghìn doanh nghiệp uy tín.
            </p>
          </div>

          {FOOTER_SECTIONS.map((sec) => (
            <div key={sec.title}>
              <h4 className="mb-4 text-label font-bold uppercase tracking-wider text-gold">
                {sec.title}
              </h4>
              <ul className="flex flex-col gap-2.5 text-body-sm text-white/70">
                {sec.links?.map((link) => (
                  <li key={link.label}>
                    <Link to={link.href} className="hover:text-white">
                      {link.label}
                    </Link>
                  </li>
                ))}
                {sec.items?.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 border-t border-white/10 pt-6 text-center text-label-sm text-white/50">
          © {new Date().getFullYear()} FutureCV. Tất cả các quyền được bảo lưu.
        </div>
      </div>
    </footer>
  );
});
