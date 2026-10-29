import type { ReactNode } from "react";
import { cn } from "~/lib/cn";

export interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-default border border-dashed border-border-strong bg-surface px-6 py-16 text-center",
        className,
      )}
    >
      {icon && <div className="mb-4 text-ink-muted">{icon}</div>}
      <h3 className="text-headline-md text-navy">{title}</h3>
      {description && <p className="mt-2 max-w-md text-ink-variant">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
