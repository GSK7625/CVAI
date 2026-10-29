import type { HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "~/lib/cn";

const badgeVariants = cva(
  cn("inline-flex items-center gap-1 px-2 py-1 rounded-tag text-label-sm font-semibold"),
  {
    variants: {
      variant: {
        navy: "bg-navy-secondary/10 text-navy",
        gold: "bg-gold/15 text-gold",
        neutral: "bg-surface-high text-ink-variant",
        success: "bg-success/10 text-success",
        danger: "bg-danger/10 text-danger",
        solidNavy: "bg-navy text-white",
        solidGold: "bg-gold text-white",
      },
      shape: {
        tag: "rounded-tag",
        pill: "rounded-full",
      },
    },
    defaultVariants: {
      variant: "neutral",
      shape: "tag",
    },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, shape, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, shape }), className)} {...props} />;
}
