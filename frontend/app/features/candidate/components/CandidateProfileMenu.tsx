/**
 * @file CandidateProfileMenu.tsx
 * @description Component hoàn chỉnh gồm Avatar Trigger + Dropdown Menu.
 * Mũi tên nằm bên trong avatar, lướt chuột qua (hover) là mở menu ngay lập tức.
 */

import { useState, useRef, useEffect } from "react";
import { AnimatePresence } from "motion/react";
import { IconChevronDown } from "@tabler/icons-react";
import { Avatar } from "~/components/ui/Avatar";
import { useCandidateProfile } from "~/features/candidate/hooks/useCandidateProfile";
import { cn } from "~/lib/cn";
import { CandidateProfileDropdown } from "./CandidateProfileDropdown";

export interface CandidateProfileMenuProps {
  variant?: "navy" | "light";
  className?: string;
}

export function CandidateProfileMenu({
  variant = "navy",
  className,
}: CandidateProfileMenuProps) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { displayName, avatarUrl } = useCandidateProfile();

  const isNavy = variant === "navy";

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setOpen(true);
  };

  const handleMouseLeave = () => {
    timeoutRef.current = setTimeout(() => setOpen(false), 200);
  };

  useEffect(() => () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  }, []);

  return (
    <div
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={cn("relative inline-block", className)}
    >
      <button
        ref={triggerRef}
        type="button"
        id="candidate-profile-menu-button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Menu hồ sơ của ${displayName}`}
        onClick={() => setOpen((v) => !v)}
        className="group relative flex items-center justify-center rounded-full outline-none transition-transform focus-visible:ring-2 focus-visible:ring-gold"
      >
        <Avatar
          src={avatarUrl}
          name={displayName}
          size="md"
          className={cn(
            "transition-transform group-hover:scale-105",
            isNavy ? "border border-white/20 shadow-sm" : "border border-border-subtle shadow-sm",
          )}
        />
        <div
          className={cn(
            "absolute -bottom-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full shadow-sm transition-colors duration-200",
            isNavy ? "bg-navy-secondary text-white/90 border border-navy" : "bg-surface text-ink-muted border border-border-subtle",
            open && "text-gold",
          )}
        >
          <IconChevronDown size={11} stroke={2.5} />
        </div>
      </button>

      <AnimatePresence>
        {open && (
          <CandidateProfileDropdown onClose={() => setOpen(false)} triggerRef={triggerRef} />
        )}
      </AnimatePresence>
    </div>
  );
}
