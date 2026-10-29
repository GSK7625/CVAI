import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from "react";
import { cn } from "~/lib/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  icon?: ReactNode;
  inputSize?: "sm" | "md" | "lg";
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, icon, inputSize = "md", ...props }, ref) => (
    <div
      className={cn(
        "flex items-center rounded-default border bg-white transition-all duration-200",
        error
          ? "border-danger focus-within:border-danger focus-within:ring-2 focus-within:ring-danger/20"
          : "border-border-strong focus-within:border-gold focus-within:ring-2 focus-within:ring-gold/20",
        className,
      )}
    >
      {icon && <span className="pl-3.5 text-ink-muted">{icon}</span>}
      <input
        ref={ref}
        aria-invalid={error ? true : undefined}
        className={cn(
          "w-full bg-transparent px-3.5 text-ink outline-none",
          "placeholder:text-ink-muted/70",
          inputSize === "sm" ? "h-9.5 text-label" : inputSize === "lg" ? "h-12 text-body" : "h-10.5 text-body",
          icon && "pl-2.5",
        )}
        {...props}
      />
    </div>
  ),
);
Input.displayName = "Input";

export interface FieldProps {
  label: string;
  htmlFor?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  children: ReactNode;
  className?: string;
}

/**
 * Field: label TRÊN, error DƯỚI (theo DESIGN.md).
 * Dùng kết hợp Input: `<Field label="Email" error={...}><Input ... /></Field>`
 */
export function Field({ label, htmlFor, error, hint, required, children, className }: FieldProps) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <label htmlFor={htmlFor} className="text-label font-medium text-ink">
        {label}
        {required && <span aria-hidden className="ml-0.5 text-danger">*</span>}
      </label>
      {children}
      {error ? (
        <p role="alert" className="text-label-sm text-danger">{error}</p>
      ) : hint ? (
        <p className="text-label-sm text-ink-muted">{hint}</p>
      ) : null}
    </div>
  );
}
