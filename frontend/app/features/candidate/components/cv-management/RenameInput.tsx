/**
 * @file RenameInput.tsx
 * @description Form đổi tên CV inline với xử lý try/catch và phím tắt (Enter/Escape).
 * Design: Midnight & Gold, @tabler/icons-react.
 */

import { useState, useRef, useEffect } from "react";
import { IconCheck, IconX, IconLoader2 } from "@tabler/icons-react";
import { useRenameCv } from "../../hooks/useCandidateCvs";

interface RenameInputProps {
  initial: string;
  cvId: string;
  onDone: () => void;
}

export function RenameInput({ initial, cvId, onDone }: RenameInputProps) {
  const [value, setValue] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const renameMutation = useRenameCv();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  const handleSubmit = async () => {
    const trimmed = value.trim();
    if (!trimmed || trimmed === initial) {
      onDone();
      return;
    }

    setError(null);
    try {
      await renameMutation.mutateAsync({ id: cvId, title: trimmed });
      onDone();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Đổi tên thất bại.";
      setError(message);
    }
  };

  return (
    <div className="flex-1 min-w-0 space-y-1">
      <div className="flex items-center gap-2 min-w-0">
        <input
          ref={inputRef}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            if (error) setError(null);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSubmit();
            if (e.key === "Escape") onDone();
          }}
          placeholder="Nhập tên mới cho CV..."
          disabled={renameMutation.isPending}
          className="flex-1 min-w-0 rounded-xl border border-gold/50 bg-surface px-3 py-1.5 text-sm font-semibold text-ink focus:outline-none focus:ring-2 focus:ring-gold/30 disabled:opacity-50"
        />
        <button
          type="button"
          title="Lưu tên mới"
          onClick={handleSubmit}
          disabled={renameMutation.isPending}
          className="p-1.5 rounded-xl bg-success/15 text-success hover:bg-success/25 transition-colors disabled:opacity-50 shrink-0"
        >
          {renameMutation.isPending ? (
            <IconLoader2 size={16} className="animate-spin" />
          ) : (
            <IconCheck size={16} />
          )}
        </button>
        <button
          type="button"
          title="Hủy"
          onClick={onDone}
          disabled={renameMutation.isPending}
          className="p-1.5 rounded-xl bg-surface-high text-ink-muted hover:bg-border-strong transition-colors shrink-0"
        >
          <IconX size={16} />
        </button>
      </div>
      {error && <p className="text-[11px] text-danger font-medium px-1">{error}</p>}
    </div>
  );
}
