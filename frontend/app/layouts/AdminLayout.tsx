import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { 
  IconLayoutDashboard, 
  IconUsers, 
  IconBuildingSkyscraper, 
  IconBriefcase, 
  IconFileText, 
  IconSettings, 
  IconLogout,
  IconMenu2,
  IconX,
} from "@tabler/icons-react";
import { requireRole } from "~/guards/requireRole";
import { useAuthStore } from "~/stores/useAuthStore";
import { Avatar } from "~/components/ui/Avatar";
import { cn } from "~/lib/cn";
import { useQueryClient } from "@tanstack/react-query";
import { authService } from "~/features/auth/services/authService";
import { useUIStore } from "~/stores/useUIStore";

export const clientLoader = () => {
  return requireRole(["admin"]);
};

const navItems = [
  { to: "/admin", label: "Tổng quan", icon: IconLayoutDashboard, end: true },
  { to: "/admin/users", label: "Người dùng", icon: IconUsers },
  { to: "/admin/companies", label: "Công ty", icon: IconBuildingSkyscraper },
  { to: "/admin/jobs", label: "Tin tuyển dụng", icon: IconBriefcase },
  { to: "/admin/audit-logs", label: "Nhật ký", icon: IconFileText },
  { to: "/admin/config", label: "Cấu hình", icon: IconSettings },
];

/** Layout cho khu vực Admin */
export default function AdminLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const showToast = useUIStore((state) => state.showToast);
  const [loggingOut, setLoggingOut] = useState(false);

  const handleLogout = async () => {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      await authService().logout(useAuthStore.getState().refreshToken);
      logout();
      queryClient.clear();
      navigate("/login-admin", { replace: true });
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Không thể đăng xuất. Vui lòng thử lại.", "error");
      if (!useAuthStore.getState().user) navigate("/login-admin", { replace: true });
    } finally {
      setLoggingOut(false);
    }
  };

  const navigation = (
    <nav aria-label="Điều hướng Admin" className="flex flex-col gap-1">
      {navItems.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={() => setMobileOpen(false)}
          className={({ isActive }) =>
            cn(
              "flex min-h-11 items-center gap-3 rounded-default px-3 py-2.5 text-label font-semibold transition-colors",
              isActive ? "bg-gold text-white" : "text-white/75 hover:bg-white/10 hover:text-white",
            )
          }
        >
          <Icon size={20} stroke={1.7} aria-hidden="true" />
          {label}
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className="min-h-dvh bg-background lg:grid lg:grid-cols-[17rem_minmax(0,1fr)]">
      {/* Desktop Sidebar */}
      <aside className="hidden min-h-dvh flex-col bg-navy px-4 py-5 text-white lg:sticky lg:top-0 lg:flex lg:h-dvh">
        <NavLink to="/admin" className="flex items-center gap-3 px-2 py-2">
          <img src="/Logo-icon.png" alt="" className="h-10 w-10 rounded-default bg-white object-contain p-1" />
          <div>
            <p className="text-body-lg font-bold">FutureCV</p>
            <p className="text-label-sm text-white/60">Quản trị viên</p>
          </div>
        </NavLink>
        <div className="mt-8 flex-1">{navigation}</div>
        <div className="border-t border-white/10 pt-4">
          <NavLink to="/admin" className="flex items-center gap-3 rounded-default px-2 py-2 hover:bg-white/10">
            <Avatar name={user?.fullName || user?.email || "Admin"} size="md" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-label font-semibold">{user?.fullName || "Quản trị viên"}</p>
              <p className="truncate text-label-sm text-white/55">{user?.email}</p>
            </div>
          </NavLink>
          <button
            type="button"
            onClick={handleLogout}
            disabled={loggingOut}
            className="mt-2 flex min-h-11 w-full items-center gap-3 rounded-default px-3 py-2 text-label font-semibold text-white/70 transition-colors hover:bg-white/10 hover:text-white disabled:opacity-50"
          >
            <IconLogout size={20} stroke={1.7} aria-hidden="true" />
            {loggingOut ? "Đang đăng xuất..." : "Đăng xuất"}
          </button>
        </div>
      </aside>

      {/* Mobile Header & Content */}
      <div className="min-w-0">
        <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b border-border-subtle bg-surface/95 px-margin-mobile backdrop-blur lg:hidden">
          <NavLink to="/admin" className="flex items-center gap-2 font-bold text-navy">
            <img src="/Logo-icon.png" alt="" className="h-9 w-9 object-contain" />
            FutureCV Admin
          </NavLink>
          <button
            type="button"
            aria-label="Mở menu Admin"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen(true)}
            className="flex h-11 w-11 items-center justify-center rounded-default text-navy hover:bg-surface-low"
          >
            <IconMenu2 size={24} aria-hidden="true" />
          </button>
        </header>

        {/* Mobile Menu Overlay */}
        {mobileOpen && (
          <div className="fixed inset-0 z-overlay bg-navy/45 lg:hidden" onMouseDown={() => setMobileOpen(false)}>
            <aside
              aria-label="Menu Admin"
              className="ml-auto flex h-full w-[min(88vw,20rem)] flex-col bg-navy p-4 text-white shadow-overlay"
              onMouseDown={(event) => event.stopPropagation()}
            >
              <div className="mb-6 flex items-center justify-between">
                <span className="text-body-lg font-bold">Quản trị viên</span>
                <button
                  type="button"
                  aria-label="Đóng menu"
                  onClick={() => setMobileOpen(false)}
                  className="flex h-11 w-11 items-center justify-center rounded-default hover:bg-white/10"
                >
                  <IconX size={22} aria-hidden="true" />
                </button>
              </div>
              <div className="flex-1">{navigation}</div>
              <button
                type="button"
                onClick={handleLogout}
                disabled={loggingOut}
                className="flex min-h-11 items-center gap-3 rounded-default px-3 py-2 text-label font-semibold text-white/75 hover:bg-white/10 disabled:opacity-50"
              >
                <IconLogout size={20} aria-hidden="true" />
                {loggingOut ? "Đang đăng xuất..." : "Đăng xuất"}
              </button>
            </aside>
          </div>
        )}

        {/* Main Content */}
        <main id="admin-main" key={location.pathname} className="mx-auto w-full max-w-[90rem] px-margin-mobile py-6 md:px-margin-desktop md:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
