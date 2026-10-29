import { useEffect, type ReactNode } from "react";
import { IconX as X } from "@tabler/icons-react";
import { cn } from "~/lib/cn";
import { Button } from "./Button";

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, children, footer, className }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-overlay flex items-center justify-center bg-navy/40 p-4 backdrop-blur-[12px]"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          "z-modal w-full max-w-lg rounded-2xl border border-border-subtle bg-surface shadow-overlay max-h-[calc(100dvh-2.5rem)] flex flex-col my-auto overflow-hidden",
          className,
        )}
      >
        <div className="flex items-center justify-between border-b border-border-subtle px-6 py-4 shrink-0 bg-surface">
          <h2 className="text-headline-md text-navy">{title}</h2>
          <Button variant="ghost" size="icon" aria-label="Đóng" onClick={onClose}>
            <X size={20} />
          </Button>
        </div>
        <div className="px-6 py-5 overflow-y-auto flex-1 min-h-0 overscroll-contain">{children}</div>
        {footer && (
          <div className="flex justify-end gap-3 border-t border-border-subtle px-6 py-4 shrink-0 bg-surface">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
