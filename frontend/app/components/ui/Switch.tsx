import { motion } from "motion/react";
import { cn } from "~/lib/cn";

export interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  id?: string;
  name?: string;
  ariaLabel?: string;
  className?: string;
  size?: "sm" | "md";
}

export function Switch({
  checked,
  onChange,
  disabled = false,
  id,
  name,
  ariaLabel,
  className,
  size = "md",
}: SwitchProps) {
  const isSm = size === "sm";

  return (
    <button
      type="button"
      role="switch"
      id={id}
      name={name}
      aria-checked={checked}
      aria-label={ariaLabel}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      className={cn(
        "group relative inline-flex shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2",
        isSm ? "h-5 w-9 p-0.5" : "h-6 w-11 p-0.5",
        checked ? "bg-gold" : "bg-navy/20 hover:bg-navy/30",
        disabled && "cursor-not-allowed opacity-50",
        className,
      )}
    >
      <motion.span
        layout
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
        className={cn(
          "pointer-events-none block rounded-full bg-white shadow-sm ring-0 transition-transform",
          isSm ? "h-4 w-4" : "h-5 w-5",
          checked
            ? isSm
              ? "translate-x-4"
              : "translate-x-5"
            : "translate-x-0",
        )}
      />
    </button>
  );
}
