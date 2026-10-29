/**
 * @file PublicLayout.tsx
 * @description Layout Shell tổng thể cho các trang công khai của FutureCV (Trang chủ, Chi tiết việc làm, Danh mục CV, v.v.).
 * @architecture Tuân thủ Single Responsibility Principle (SRP): Chỉ chịu trách nhiệm dàn khung Header + Outlet + Footer.
 */

import { Outlet } from "react-router";
import { PublicHeader } from "./public/PublicHeader";
import { PublicFooter } from "./public/PublicFooter";

export default function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <PublicHeader />
      <main className="flex-1">
        <Outlet />
      </main>
      <PublicFooter />
    </div>
  );
}
