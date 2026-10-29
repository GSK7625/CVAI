/**
 * @file DeleteConfirmBanner.tsx
 * @description Khung xác nhận xóa CV an toàn, tích hợp useDeleteCv mutation và xử lý try/catch.
 * Design: Midnight & Gold, @tabler/icons-react.
 */

import { useState } from "react";
import { IconAlertCircle, IconLoader2 } from "@tabler/icons-react";
import { useDeleteCv } from "../../hooks/useCandidateCvs";

interface DeleteConfirmBannerProps {
  cvId: string;
  title: string;
  onCancel: () => void;
  onSuccess?: () => void;
}

export function DeleteConfirmBanner({
  cvId,
  title,
  onCancel,
  onSuccess,
}: DeleteConfirmBannerProps) {
  const deleteMutation = useDeleteCv();
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    setError(null);
    try {
      await deleteMutation.mutateAsync(cvId);
      onSuccess?.();
      onCancel();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Xóa hồ sơ thất bại.";
      setError(message);
    }
  };

  return (
    <div className="mt-3 rounded-2xl border border-danger/25 bg-danger/5 p-3.5 space-y-2.5">
      <div className="flex items-start gap-2">
        <IconAlertCircle size={16} className="text-danger shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-xs text-danger font-bold">
            Xác nhận xóa hồ sơ "{title || "CV này"}"?
          </p>
          <p className="text-[11px] text-ink-muted leading-relaxed mt-0.5">
            Lưu ý: Các đơn ứng tuyển đã nộp với CV này vẫn được lưu trữ an toàn trong lịch sử tuyển dụng.
          </p>
          {error && <p className="mt-1 text-[11px] text-danger font-medium">{error}</p>}
        </div>
      </div>
      <div className="flex items-center gap-2 pt-1">
        <button
          type="button"
          onClick={handleConfirm}
          disabled={deleteMutation.isPending}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-danger text-white text-xs font-bold hover:bg-danger/90 transition-colors active:scale-[0.97] disabled:opacity-60"
        >
          {deleteMutation.isPending && <IconLoader2 size={13} className="animate-spin" />}
          <span>{deleteMutation.isPending ? "Đang xóa..." : "Xác nhận xóa"}</span>
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={deleteMutation.isPending}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border-strong bg-surface text-xs font-semibold text-ink-variant hover:bg-surface-low transition-colors disabled:opacity-50"
        >
          Hủy
        </button>
      </div>
    </div>
  );
}
