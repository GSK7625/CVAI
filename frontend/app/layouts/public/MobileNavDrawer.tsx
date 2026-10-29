/**
 * @file MobileNavDrawer.tsx
 * @description Drawer điều hướng dành riêng cho thiết bị di động và tablet.
 * @architecture Tuân thủ SRP: Chỉ đảm nhiệm render menu mở rộng trên mobile khi bấm hamburger button.
 */

import { Link } from "react-router";

import { Button } from "~/components/ui/Button";
import type { User } from "~/stores/useAuthStore";

interface MobileNavDrawerProps {
  open: boolean;
  onClose: () => void;
  user: User | null;
  onLogout: () => void;
  onLoginClick: () => void;
  onRegisterClick: () => void;
}

export function MobileNavDrawer({
  open,
  onClose,
  user,
  onLogout,
  onLoginClick,
  onRegisterClick,
}: MobileNavDrawerProps) {
  if (!open) return null;

  return (
    <nav
      className="border-t border-border-subtle bg-surface px-margin-mobile py-4 md:hidden"
      aria-label="Điều hướng di động"
    >
      <div className="flex flex-col gap-1 text-label">
        <Link
          to="/"
          onClick={onClose}
          className="rounded px-3 py-2.5 font-semibold text-navy hover:bg-surface-low hover:text-gold"
        >
          Việc làm
        </Link>
        <Link
          to="/cv/templates"
          onClick={onClose}
          className="rounded px-3 py-2.5 text-navy hover:bg-surface-low hover:text-gold"
        >
          Tạo CV
        </Link>

        <div className="my-2 h-px bg-border-subtle" />

        {user ? (
          <>
            {user.role === "employer" && (
              <Link
                to="/hr"
                onClick={onClose}
                className="rounded px-3 py-2.5 font-bold text-navy hover:bg-surface-low hover:text-gold"
              >
                Vào trang Tuyển Dụng »
              </Link>
            )}
            <button
              type="button"
              onClick={onLogout}
              className="rounded px-3 py-2.5 text-left text-ink-variant hover:bg-surface-low"
            >
              Đăng xuất ({user.fullName || user.email})
            </button>
          </>
        ) : (
          <div className="flex flex-col gap-2 pt-2">
            <Button
              variant="ghost"
              onClick={() => {
                onClose();
                onLoginClick();
              }}
            >
              Đăng nhập
            </Button>
            <Button
              variant="accent"
              onClick={() => {
                onClose();
                onRegisterClick();
              }}
            >
              Đăng ký ngay
            </Button>
          </div>
        )}
      </div>
    </nav>
  );
}
