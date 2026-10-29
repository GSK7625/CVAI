import { Badge, type BadgeProps } from "~/components/ui/Badge";
import { cn } from "~/lib/cn";

type Tone = "success" | "info" | "warning" | "danger" | "neutral";

const toneMap: Record<Tone, BadgeProps["variant"]> = {
  success: "success",
  info: "navy",
  warning: "gold",
  danger: "danger",
  neutral: "neutral",
};

const labels: Record<Tone, string> = {
  success: "Đang hoạt động",
  info: "Đang diễn ra",
  warning: "Chờ xử lý",
  danger: "Đã kết thúc",
  neutral: "Nháp",
};

export function StatusBadge({
  tone,
  label,
  className,
}: {
  tone: Tone;
  label?: string;
  className?: string;
}) {
  return (
    <Badge variant={toneMap[tone]} shape="pill" className={cn(className)}>
      {label ?? labels[tone]}
    </Badge>
  );
}
