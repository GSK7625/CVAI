/**
 * @file CandidateProfileDropdown.tsx
 * @description Component Menu Dropdown hồ sơ ứng viên trên Header.
 */

import { useState, useRef, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import {
  IconBriefcase,
  IconFileText,
  IconMailCog,
  IconUserShield,
  IconChevronDown,
  IconShieldCheck,
  IconArrowRight,
  IconCamera,
  IconLoader2,
} from "@tabler/icons-react";
import { Avatar } from "~/components/ui/Avatar";
import { useAuthStore } from "~/stores/useAuthStore";
import { useUIStore } from "~/stores/useUIStore";
import { authService } from "~/features/auth/services/authService";
import { queryClient } from "~/lib/queryClient";
import { useCandidateProfile } from "~/features/candidate/hooks/useCandidateProfile";
import { useUploadCandidateAvatar } from "~/features/candidate/hooks/useUploadCandidateAvatar";
import { cn } from "~/lib/cn";

export interface CandidateProfileDropdownProps {
  onClose: () => void;
  className?: string;
  triggerRef?: React.RefObject<HTMLElement | null>;
}

// 4 danh mục theo candidate-profile-dropdown-spec.md
const SECTIONS = [
  {
    id: "jobs",
    title: "Quản lý tìm việc",
    icon: IconBriefcase,
    items: [
      { label: "Việc làm đã lưu", href: "/candidate/saved-jobs" },
      { label: "Việc làm đã ứng tuyển", href: "/candidate/applications" },
    ],
  },
  {
    id: "cv",
    title: "Quản lý CV & Cover letter",
    icon: IconFileText,
    items: [
      { label: "CV của tôi", href: "/candidate/cvs" },
    ],
  },
  {
    id: "notifications",
    title: "Cài đặt email & thông báo",
    icon: IconMailCog,
    items: [
      { label: "Cài đặt thông báo việc làm", href: "/candidate/notifications" },
      { label: "Cài đặt email từ nhà tuyển dụng", href: "/candidate/email-settings" },
    ],
  },
  {
    id: "security",
    title: "Cá nhân & Bảo mật",
    icon: IconUserShield,
    items: [
      { label: "Cài đặt thông tin cá nhân", href: "/candidate/personal-info" },
      { label: "Cài đặt bảo mật", href: "/candidate/security" },
      { label: "Đổi mật khẩu", href: "/candidate/change-password" },
    ],
  },
];

export function CandidateProfileDropdown({
  onClose,
  className,
  triggerRef,
}: CandidateProfileDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const showToast = useUIStore((s) => s.showToast);
  const uploadAvatarMutation = useUploadCandidateAvatar();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { displayName, email, avatarUrl, candidateId, isLoading } = useCandidateProfile();

  // Nhóm 1 & 2 mặc định MỞ, Nhóm 3 & 4 mặc định ĐÓNG
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    jobs: true,
    cv: true,
  });

  const toggleSection = (id: string) => {
    setOpenSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Kích hoạt chọn file avatar
  const handleAvatarClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (uploadAvatarMutation.isPending) return;
    fileInputRef.current?.click();
  };

  // Xử lý upload ảnh đại diện qua API thật
  const handleAvatarFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset input value để có thể chọn lại file cùng tên nếu muốn
    e.target.value = "";

    // Validate loại file: chỉ cho phép JPG, JPEG, PNG
    const validMimeTypes = ["image/jpeg", "image/png", "image/jpg"];
    const validExtensions = [".jpg", ".jpeg", ".png"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!validMimeTypes.includes(file.type.toLowerCase()) && !validExtensions.includes(ext)) {
      showToast("Ảnh đại diện phải có định dạng JPG hoặc PNG.", "error");
      return;
    }

    // Validate dung lượng file: tối đa 5MB (theo backend ApiControllerBase)
    const maxSizeBytes = 5 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      showToast("Kích thước ảnh đại diện không được vượt quá 5MB.", "error");
      return;
    }

    try {
      await uploadAvatarMutation.mutateAsync(file);
      showToast("Cập nhật ảnh đại diện thành công!", "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Tải ảnh đại diện thất bại";
      showToast(message, "error");
    }
  };

  // Đóng khi click ngoài hoặc bấm phím Escape
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      const target = e.target as Node;
      if (triggerRef?.current?.contains(target)) return;
      if (dropdownRef.current && !dropdownRef.current.contains(target)) onClose();
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();

    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [onClose, triggerRef]);

  const handleLogout = async () => {
    onClose();
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

  const idFormatted = candidateId
    ? candidateId.replace(/[^a-zA-Z0-9]/g, "").slice(0, 8).toUpperCase()
    : null;

  return (
    <motion.div
      ref={dropdownRef}
      role="menu"
      initial={{ opacity: 0, y: 8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 6, scale: 0.98 }}
      transition={{ duration: 0.2, ease: [0.32, 0.72, 0, 1] }}
      className={cn(
        "absolute right-0 top-full z-dropdown mt-2 w-[330px] p-1.5",
        "rounded-2xl bg-surface/95 backdrop-blur-2xl ring-1 ring-navy/10 shadow-overlay",
        className,
      )}
    >
      <div className="flex max-h-[min(90vh,700px)] flex-col overflow-hidden rounded-[calc(1rem-2px)] bg-surface shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
        {/* Header Block */}
        <div className="border-b border-border-subtle bg-gradient-to-b from-surface-low/80 to-surface p-4">
          <div className="flex items-start gap-3">
            {/* Avatar with Upload Capability */}
            <div className="relative group/avatar shrink-0">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/jpg"
                className="hidden"
                onChange={handleAvatarFileChange}
              />
              <button
                type="button"
                onClick={handleAvatarClick}
                disabled={uploadAvatarMutation.isPending}
                title="Nhấp để thay đổi ảnh đại diện (JPG/PNG, tối đa 5MB)"
                aria-label="Thay đổi ảnh đại diện"
                className={cn(
                  "relative block rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-gold",
                  uploadAvatarMutation.isPending ? "cursor-wait" : "cursor-pointer",
                )}
              >
                <Avatar
                  src={avatarUrl}
                  name={displayName}
                  size="md"
                  className="border border-border-subtle shadow-sm transition-all duration-200 group-hover/avatar:brightness-90"
                />

                {/* Hover & Loading Overlay */}
                <div
                  className={cn(
                    "absolute inset-0 flex items-center justify-center rounded-full bg-navy/60 text-white transition-opacity duration-200",
                    uploadAvatarMutation.isPending
                      ? "opacity-100"
                      : "opacity-0 group-hover/avatar:opacity-100",
                  )}
                >
                  {uploadAvatarMutation.isPending ? (
                    <IconLoader2 size={18} className="animate-spin text-gold" />
                  ) : (
                    <IconCamera size={18} stroke={1.8} />
                  )}
                </div>

                {/* Camera Badge Icon on bottom-right */}
                <div
                  className={cn(
                    "absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-surface text-navy shadow-sm ring-1 ring-border-subtle transition-all duration-200 group-hover/avatar:bg-gold group-hover/avatar:text-white",
                    uploadAvatarMutation.isPending && "bg-gold text-white",
                  )}
                >
                  <IconCamera size={11} stroke={2} />
                </div>
              </button>
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-body font-semibold text-navy" title={displayName}>
                {displayName}
              </p>
              <div className="mt-1 flex items-center">
                <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success ring-1 ring-success/25">
                  <IconShieldCheck size={13} stroke={2} />
                  Tài khoản đã xác thực
                </span>
              </div>
              <div className="mt-2 flex items-center gap-1.5 text-label-sm text-ink-muted">
                {idFormatted && (
                  <>
                    <span className="shrink-0 rounded border border-border-subtle bg-surface px-1.5 py-0.5 font-mono text-[10.5px] font-medium text-ink-variant">
                      ID {idFormatted}
                    </span>
                    <span className="select-none text-border-strong">|</span>
                  </>
                )}
                <span className="truncate text-[12px] text-ink-variant" title={email}>
                  {email || (isLoading ? "Đang tải..." : "Chưa có email")}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Menu Sections */}
        <div className="flex-1 overflow-y-auto overscroll-contain p-2 scrollbar-thin">
          <div className="space-y-1">
            {SECTIONS.map((section) => {
              const SectionIcon = section.icon;
              const isOpen = Boolean(openSections[section.id]);

              return (
                <div key={section.id} className="rounded-xl">
                  <button
                    type="button"
                    onClick={() => toggleSection(section.id)}
                    aria-expanded={isOpen}
                    className={cn(
                      "group flex w-full items-center justify-between px-3 py-2 text-left rounded-xl transition-all duration-200",
                      isOpen ? "bg-surface-low/70" : "hover:bg-surface-low/50",
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <div
                        className={cn(
                          "flex h-7 w-7 items-center justify-center rounded-lg transition-colors duration-200",
                          isOpen ? "bg-gold/15 text-gold" : "bg-navy/5 text-navy group-hover:bg-navy/10",
                        )}
                      >
                        <SectionIcon size={16} stroke={1.6} />
                      </div>
                      <span className="text-label font-semibold text-navy">{section.title}</span>
                    </div>
                    <IconChevronDown
                      size={16}
                      stroke={2}
                      className={cn(
                        "text-ink-muted transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)]",
                        isOpen && "rotate-180 text-gold",
                      )}
                    />
                  </button>

                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.22, ease: [0.32, 0.72, 0, 1] }}
                        className="overflow-hidden"
                      >
                        <div className="space-y-0.5 py-1 pl-9 pr-1">
                          {section.items.map((item) => {
                            const isActive = location.pathname === item.href;

                            return (
                              <Link
                                key={item.label}
                                to={item.href}
                                onClick={onClose}
                                className={cn(
                                  "group/link flex items-center justify-between rounded-lg px-2.5 py-1.5 text-label-sm transition-all duration-200",
                                  isActive
                                    ? "bg-gold/10 font-semibold text-gold ring-1 ring-gold/25"
                                    : "text-ink-variant hover:bg-surface-low hover:text-navy hover:translate-x-0.5",
                                )}
                              >
                                <span>{item.label}</span>
                                {isActive ? (
                                  <span className="h-1.5 w-1.5 rounded-full bg-gold" />
                                ) : (
                                  <IconArrowRight
                                    size={12}
                                    stroke={2}
                                    className="text-ink-muted/0 transition-all group-hover/link:translate-x-0.5 group-hover/link:text-ink-muted"
                                  />
                                )}
                              </Link>
                            );
                          })}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer Action: Nút Đăng xuất ở giữa, không icon */}
        <div className="border-t border-border-subtle bg-surface-low/30 p-2.5">
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center justify-center rounded-xl border border-danger/20 bg-danger/5 py-2 text-center text-label font-semibold text-danger transition-all duration-150 hover:bg-danger hover:text-white"
          >
            Đăng xuất
          </button>
        </div>
      </div>
    </motion.div>
  );
}
