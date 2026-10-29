/**
 * @file CvAnalysisPanel.tsx
 * @description Panel hiển thị điểm phân tích chất lượng CV (FC-82, Screen 2).
 * - Gọi GET /cvs/{id}/analysis (BE tự chấm lần đầu, rule-based, không polling AI).
 * - Nút "Chấm lại" gọi POST /cvs/{id}/analyze.
 * - KHÔNG gọi là "AI" hay "ATS match" trên giao diện.
 */

import {
  IconChartBar,
  IconRefresh,
  IconShieldCheck,
  IconAlertTriangle,
  IconBulb,
  IconTags,
  IconInfoCircle,
} from "@tabler/icons-react";
import { useCvAnalysis, useAnalyzeCv } from "../../hooks/useCandidateCvs";
import { Skeleton } from "~/components/ui";

interface CvAnalysisPanelProps {
  cvId: string;
}

function ScoreRing({ score }: { score: number }) {
  const size = 96;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color =
    score >= 80
      ? "#2e7d6b" // success
      : score >= 60
        ? "#c8963e" // gold/warning
        : "#ba1a1a"; // danger

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-border-strong"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-ink" style={{ color }}>
          {score}
        </span>
        <span className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">
          /100
        </span>
      </div>
    </div>
  );
}

function AnalysisSkeleton() {
  return (
    <div className="space-y-5 animate-pulse">
      <div className="flex items-center gap-4">
        <Skeleton className="w-24 h-24 rounded-full shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-56" />
        </div>
      </div>
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-4/5" />
        </div>
      ))}
    </div>
  );
}

function TagChip({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-navy/8 text-navy border border-navy/15">
      {label}
    </span>
  );
}

function SectionBlock({
  icon,
  label,
  items,
  colorClass,
  bgClass,
}: {
  icon: React.ReactNode;
  label: string;
  items: string[];
  colorClass: string;
  bgClass: string;
}) {
  if (!items || items.length === 0) return null;
  return (
    <div className={`rounded-xl border p-4 space-y-2.5 ${bgClass}`}>
      <div className={`flex items-center gap-2 text-xs font-bold uppercase tracking-wider ${colorClass}`}>
        {icon}
        <span>{label}</span>
      </div>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-ink-variant leading-relaxed">
            <span className={`mt-1.5 w-1.5 h-1.5 rounded-full shrink-0 ${colorClass.replace("text-", "bg-")}`} />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function CvAnalysisPanel({ cvId }: CvAnalysisPanelProps) {
  const { data: analysis, isLoading, isError } = useCvAnalysis(cvId);
  const analyzeMutation = useAnalyzeCv(cvId);

  if (isLoading) return <AnalysisSkeleton />;

  if (isError || !analysis) {
    return (
      <div className="flex flex-col items-center gap-3 py-8 text-center">
        <IconAlertTriangle size={32} className="text-danger opacity-60" />
        <p className="text-sm text-ink-variant">Không thể tải dữ liệu phân tích.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Score summary */}
      <div className="flex items-center gap-5 pb-4 border-b border-border-subtle">
        <ScoreRing score={analysis.cvScore} />
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-bold text-ink leading-tight">
            Điểm chất lượng hồ sơ
          </h3>
          <button
            type="button"
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending}
            className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border-strong bg-surface-low text-xs font-semibold text-ink-variant hover:bg-surface hover:text-navy transition-all active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <IconRefresh
              size={13}
              className={analyzeMutation.isPending ? "animate-spin" : ""}
            />
            {analyzeMutation.isPending ? "Đang chấm lại..." : "Chấm lại"}
          </button>
        </div>
      </div>

      {/* 4 blocks */}
      <SectionBlock
        icon={<IconShieldCheck size={13} />}
        label="Điểm mạnh"
        items={analysis.strengths}
        colorClass="text-success"
        bgClass="bg-success/5 border-success/20"
      />
      <SectionBlock
        icon={<IconAlertTriangle size={13} />}
        label="Điểm yếu"
        items={analysis.weaknesses}
        colorClass="text-danger"
        bgClass="bg-danger/5 border-danger/20"
      />
      <SectionBlock
        icon={<IconBulb size={13} />}
        label="Gợi ý cải thiện"
        items={analysis.improvements}
        colorClass="text-warning"
        bgClass="bg-warning/5 border-warning/20"
      />

      {analysis.missingSkills && analysis.missingSkills.length > 0 && (
        <div className="rounded-xl border border-navy/15 bg-navy/4 p-4 space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-navy">
            <IconTags size={13} />
            <span>Kỹ năng nên bổ sung</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {analysis.missingSkills.map((skill) => (
              <TagChip key={skill} label={skill} />
            ))}
          </div>
        </div>
      )}

      <div className="flex items-start gap-2 rounded-lg bg-surface-low border border-border-subtle p-3">
        <IconInfoCircle size={14} className="text-ink-muted mt-0.5 shrink-0" />
        <p className="text-[11px] text-ink-muted leading-relaxed">
          Cập nhật lần cuối:{" "}
          {new Date(analysis.generatedAt).toLocaleString("vi-VN")}. Sau khi
          chỉnh sửa thông tin CV, bấm "Chấm lại" để cập nhật điểm mới nhất.
        </p>
      </div>
    </div>
  );
}
