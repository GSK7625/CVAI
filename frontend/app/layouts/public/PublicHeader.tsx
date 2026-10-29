/**
 * @file PublicHeader.tsx
 * @description Header chính cho các trang Public (Logo, điều hướng danh mục, menu mega, hồ sơ tài khoản và CTA tuyển dụng).
 * @architecture Tuân thủ Single Responsibility Principle (SRP): Chỉ đảm nhiệm hiển thị thanh điều hướng đầu trang và quản lý popup menu.
 */

import { useState, useRef, useEffect, memo } from "react";

import { Link, useNavigate } from "react-router";
import {
  IconMenu2,
  IconX,
  IconBell,
  IconChevronDown,
  IconChevronUp,
} from "@tabler/icons-react";
import { Button } from "~/components/ui/Button";
import { Avatar } from "~/components/ui/Avatar";
import { useAuthStore } from "~/stores/useAuthStore";
import { JobMegaMenu } from "./JobMegaMenu";
import { CvMegaMenu } from "./CvMegaMenu";
import { MobileNavDrawer } from "./MobileNavDrawer";
import { CandidateProfileMenu } from "~/features/candidate/components/CandidateProfileMenu";
import { authService } from "~/features/auth/services/authService";
import { queryClient } from "~/lib/queryClient";

export const PublicHeader = memo(function PublicHeader() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [jobDropdownOpen, setJobDropdownOpen] = useState(false);
  const [cvDropdownOpen, setCvDropdownOpen] = useState(false);

  const jobTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const cvTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = async () => {
    setMobileOpen(false);
    const { refreshToken } = useAuthStore.getState();
    if (refreshToken) {
      try {
        await authService().logout(refreshToken);
      } catch {
        // Revoke best-effort
      }
    }
    logout();
    queryClient.removeQueries({ type: "all" });
    navigate("/");
  };

  const handleJobMouseEnter = () => {
    if (jobTimeoutRef.current) clearTimeout(jobTimeoutRef.current);
    if (cvTimeoutRef.current) clearTimeout(cvTimeoutRef.current);
    setCvDropdownOpen(false);
    setJobDropdownOpen(true);
  };

  const handleJobMouseLeave = () => {
    jobTimeoutRef.current = setTimeout(() => {
      setJobDropdownOpen(false);
    }, 200);
  };

  const handleCvMouseEnter = () => {
    if (cvTimeoutRef.current) clearTimeout(cvTimeoutRef.current);
    if (jobTimeoutRef.current) clearTimeout(jobTimeoutRef.current);
    setJobDropdownOpen(false);
    setCvDropdownOpen(true);
  };

  const handleCvMouseLeave = () => {
    cvTimeoutRef.current = setTimeout(() => {
      setCvDropdownOpen(false);
    }, 200);
  };

  useEffect(() => {
    return () => {
      if (jobTimeoutRef.current) clearTimeout(jobTimeoutRef.current);
      if (cvTimeoutRef.current) clearTimeout(cvTimeoutRef.current);
    };
  }, []);

  return (
    <header className="sticky top-0 z-50 border-b border-border-subtle bg-surface shadow-sm">
      <div className="flex h-[72px] w-full items-center justify-between px-margin-mobile md:px-margin-desktop">
        {/* Logo & Navigation */}
        <div className="flex items-center gap-6 lg:gap-8">
          <Link to="/" className="flex items-center">
            <img src="/Logo.png" alt="FutureCV" className="h-7 w-auto object-contain md:h-8" />
          </Link>

          <nav className="hidden items-center gap-1 md:flex" aria-label="Điều hướng chính">
            {/* 1. Menu Việc làm + Mega Dropdown */}
            <div
              className="relative"
              onMouseEnter={handleJobMouseEnter}
              onMouseLeave={handleJobMouseLeave}
            >
              <Link
                to="/"
                className={`flex items-center gap-1.5 px-3.5 py-2.5 text-label font-semibold transition-all duration-200 ${jobDropdownOpen ? "text-gold" : "text-navy hover:text-gold"
                  }`}
              >
                <span>Việc làm</span>
                {jobDropdownOpen ? (
                  <IconChevronUp size={16} stroke={2.2} className="text-gold transition-transform" />
                ) : (
                  <IconChevronDown size={16} stroke={2.2} className="text-ink-muted transition-transform" />
                )}
              </Link>

              {jobDropdownOpen && (
                <JobMegaMenu
                  onClose={() => setJobDropdownOpen(false)}
                  onMouseEnter={handleJobMouseEnter}
                  onMouseLeave={handleJobMouseLeave}
                />
              )}
            </div>

            {/* 2. Menu Tạo CV + Dropdown */}
            <div
              className="relative"
              onMouseEnter={handleCvMouseEnter}
              onMouseLeave={handleCvMouseLeave}
            >
              <Link
                to="/cv/templates"
                className={`flex items-center gap-1.5 px-3.5 py-2.5 text-label font-semibold transition-all duration-200 ${cvDropdownOpen ? "text-gold" : "text-navy hover:text-gold"
                  }`}
              >
                <span>Tạo CV</span>
                {cvDropdownOpen ? (
                  <IconChevronUp size={16} stroke={2.2} className="text-gold transition-transform" />
                ) : (
                  <IconChevronDown size={16} stroke={2.2} className="text-ink-muted transition-transform" />
                )}
              </Link>

              {cvDropdownOpen && (
                <CvMegaMenu
                  onClose={() => setCvDropdownOpen(false)}
                  onMouseEnter={handleCvMouseEnter}
                  onMouseLeave={handleCvMouseLeave}
                />
              )}
            </div>
          </nav>
        </div>

        {/* Right: Auth / Actions */}
        <div className="hidden items-center gap-5 md:flex">
          {user ? (
            <>
              <button
                type="button"
                aria-label="Thông báo"
                className="relative text-navy transition-colors hover:text-gold"
              >
                <IconBell size={22} stroke={1.6} />
              </button>
              {user.role === "candidate" ? (
                <CandidateProfileMenu variant="light" />
              ) : (
                <div className="flex items-center gap-3">
                  <Avatar name={user.fullName || user.email || "U"} size="md" />
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="text-label text-ink-variant transition-colors hover:text-navy"
                  >
                    Đăng xuất
                  </button>
                </div>
              )}
              <div className="h-8 w-px bg-border-subtle" aria-hidden />
              {user.role === "employer" ? (
                <Link
                  to="/hr"
                  className="rounded-default bg-navy px-3.5 py-2 text-label font-bold !text-white transition-colors hover:bg-navy-secondary"
                >
                  Vào trang Tuyển Dụng »
                </Link>
              ) : user.role === "admin" ? (
                <Link
                  to="/admin"
                  className="rounded-default bg-navy px-3.5 py-2 text-label font-bold !text-white transition-colors hover:bg-navy-secondary"
                >
                  Vào trang Quản trị »
                </Link>
              ) : (
                <div className="flex flex-col items-start">
                  <span className="text-label-sm text-ink-variant">Bạn là nhà tuyển dụng?</span>
                  <Link
                    to="/login-employer"
                    className="text-label font-bold text-navy transition-colors hover:text-gold"
                  >
                    Đăng tuyển ngay »
                  </Link>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="flex flex-col items-start">
                <span className="text-label-sm text-ink-variant">Bạn là nhà tuyển dụng?</span>
                <Link
                  to="/register"
                  className="text-label font-bold text-navy transition-colors hover:text-gold"
                >
                  Đăng tuyển ngay »
                </Link>
              </div>
              <div className="h-8 w-px bg-border-subtle" aria-hidden />
              <Button variant="ghost" onClick={() => navigate("/login")}>
                Đăng nhập
              </Button>
              <Button variant="accent" onClick={() => navigate("/register")}>
                Đăng ký ngay
              </Button>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          type="button"
          className="text-navy md:hidden"
          aria-label={mobileOpen ? "Đóng menu" : "Mở menu"}
          aria-expanded={mobileOpen}
          onClick={() => setMobileOpen((v) => !v)}
        >
          {mobileOpen ? <IconX size={24} /> : <IconMenu2 size={24} />}
        </button>
      </div>

      <MobileNavDrawer
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        user={user}
        onLogout={handleLogout}
        onLoginClick={() => navigate("/login")}
        onRegisterClick={() => navigate("/register")}
      />
    </header>
  );
});
