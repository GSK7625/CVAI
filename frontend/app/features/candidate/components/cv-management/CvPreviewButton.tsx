import { useState, type ReactNode } from "react";
import { useUIStore } from "~/stores/useUIStore";
import { candidateCvService } from "../../services/candidateCvService";

export function CvPreviewButton({ cvId, className, children }: {
  cvId: string; className?: string; children: ReactNode;
}) {
  const [busy, setBusy] = useState(false);
  const showToast = useUIStore(state => state.showToast);

  async function preview() {
    // Open during the click so awaiting authentication does not trigger popup blocking.
    const tab = window.open("", "_blank");
    if (!tab) {
      showToast("Hãy cho phép mở tab mới để xem trước CV.", "error");
      return;
    }
    tab.opener = null;
    setBusy(true);
    try {
      const url = await candidateCvService.getPreviewUrl(cvId);
      if (!tab.closed) tab.location.replace(url);
    } catch (error) {
      tab.close();
      showToast(error instanceof Error ? error.message : "Không mở được CV. Vui lòng thử lại.", "error");
    } finally {
      setBusy(false);
    }
  }

  return <button type="button" className={className} disabled={busy}
    title="Xem trước CV PDF" aria-label="Xem trước CV PDF" aria-busy={busy}
    onKeyDown={event => event.stopPropagation()}
    onClick={event => { event.stopPropagation(); void preview(); }}>
    {busy ? "Đang mở…" : children}
  </button>;
}
