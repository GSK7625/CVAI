/**
 * @file CvUploadZone.tsx
 * @description Vùng kéo-thả hoặc bấm chọn để tải lên CV PDF (FC-82).
 * - Validate: chỉ .pdf, ≤ 5MB (khớp với backend ValidateCvFile).
 * - Hiển thị lỗi inline, không toast riêng cho validation.
 */

import { useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router";
import { IconCloudUpload, IconFileTypePdf, IconX } from "@tabler/icons-react";
import { useUploadCandidateCv } from "../../hooks/useCandidateCvs";
import { validateCvFile, cvTitleFromFile } from "~/utils";
import { useAuthStore } from "~/stores/useAuthStore";
import { useUIStore } from "~/stores/useUIStore";
import type { CvResponse } from "../../types";

interface CvUploadZoneProps {
  onUploaded?: (cv?: CvResponse) => void;
}

export function CvUploadZone({ onUploaded }: CvUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selected, setSelected] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const navigate = useNavigate();
  const showToast = useUIStore((s) => s.showToast);
  const uploadMutation = useUploadCandidateCv();

  const handleFile = useCallback((file: File | null) => {
    if (!file) return;
    const error = validateCvFile(file);
    if (error) {
      setValidationError(error);
      setSelected(null);
      return;
    }
    setValidationError(null);
    setSelected(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      handleFile(file);
    },
    [handleFile]
  );

  const handleUpload = async () => {
    if (!selected) return;

    const user = useAuthStore.getState().user;
    if (!user) {
      showToast("Vui lòng đăng nhập tài khoản ứng viên để tải lên CV.", "info");
      navigate(`/login?returnTo=${encodeURIComponent(window.location.pathname)}`);
      return;
    }

    if (user.role !== "candidate") {
      showToast("Chỉ tài khoản Ứng viên mới có quyền tải lên CV ứng tuyển.", "error");
      return;
    }

    const title = cvTitleFromFile(selected.name);
    try {
      const uploaded = await uploadMutation.mutateAsync({ file: selected, title });
      setSelected(null);
      onUploaded?.(uploaded);
    } catch {
      // Toast thông báo lỗi đã được useUploadCandidateCv quản lý
    }
  };

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Khu vực tải lên CV PDF"
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`group relative flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-200 py-10 px-6 text-center
          ${dragOver
            ? "border-gold bg-gold/8 scale-[1.01]"
            : "border-border-strong bg-surface-low hover:border-navy/30 hover:bg-surface"
          }`}
      >
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-colors
          ${dragOver ? "bg-gold/20" : "bg-surface-high group-hover:bg-navy/8"}`}>
          <IconCloudUpload
            size={24}
            className={`transition-colors ${dragOver ? "text-gold" : "text-ink-muted group-hover:text-navy"}`}
          />
        </div>
        <div>
          <p className="text-sm font-semibold text-ink">
            Kéo thả file vào đây hoặc{" "}
            <span className="text-gold underline underline-offset-2">bấm chọn file</span>
          </p>
          <p className="mt-1 text-xs text-ink-muted">Chỉ file PDF, tối đa 5MB</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="sr-only"
          onChange={(e) => {
            handleFile(e.target.files?.[0] ?? null);
            e.target.value = "";
          }}
          aria-hidden="true"
        />
      </div>

      {/* Validation error */}
      {validationError && (
        <p className="text-xs text-danger font-medium px-1">{validationError}</p>
      )}

      {/* Selected file preview */}
      {selected && (
        <div className="flex items-center gap-3 rounded-xl border border-border-strong bg-surface p-3">
          <IconFileTypePdf size={20} className="text-danger shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-ink truncate">{selected.name}</p>
            <p className="text-[11px] text-ink-muted">
              {(selected.size / 1024).toFixed(0)} KB
            </p>
          </div>
          <button
            type="button"
            onClick={() => setSelected(null)}
            className="p-1 rounded-md text-ink-muted hover:text-danger hover:bg-danger/8 transition-colors"
          >
            <IconX size={14} />
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={uploadMutation.isPending}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-navy text-white text-xs font-bold hover:bg-navy-secondary transition-colors active:scale-[0.97] disabled:opacity-60 whitespace-nowrap"
          >
            {uploadMutation.isPending ? "Đang tải lên..." : "Tải lên"}
          </button>
        </div>
      )}
    </div>
  );
}
