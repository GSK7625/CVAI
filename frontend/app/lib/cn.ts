import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

const customTwMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [
        "text-display",
        "text-headline",
        "text-headline-md",
        "text-body-lg",
        "text-body",
        "text-label",
        "text-label-sm",
      ],
      "text-color": [
        "text-navy",
        "text-navy-secondary",
        "text-gold",
        "text-background",
        "text-surface",
        "text-surface-low",
        "text-surface-high",
        "text-border-subtle",
        "text-border-strong",
        "text-ink",
        "text-ink-variant",
        "text-ink-muted",
        "text-success",
        "text-danger",
        "text-warning",
      ],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return customTwMerge(clsx(inputs));
}
