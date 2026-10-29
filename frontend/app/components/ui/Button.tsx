import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "~/lib/cn";

const buttonVariants = cva(
  cn(
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-default font-label font-semibold",
    "transition-all duration-200 select-none",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy",
    "disabled:pointer-events-none disabled:opacity-50",
    "active:scale-[0.98]",
  ),
  {
    variants: {
      variant: {
        primary: "bg-navy text-white hover:bg-navy-secondary shadow-sm hover:shadow-md",
        secondary:
          "bg-transparent border border-navy text-navy hover:bg-navy hover:text-white",
        accent: "bg-gold text-white hover:bg-[#b08233] shadow-sm hover:shadow-md",
        ghost: "bg-transparent text-navy hover:bg-navy/5",
        danger: "bg-danger text-white hover:bg-[#93000a]",
      },
      size: {
        sm: "h-9 px-4 text-label-sm",
        md: "h-11 px-6",
        lg: "h-12 px-8 text-body",
        icon: "h-10 w-10 p-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
  VariantProps<typeof buttonVariants> { }

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, type = "button", ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  ),
);
Button.displayName = "Button";

export { buttonVariants };
