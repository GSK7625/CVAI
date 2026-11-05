import type { EvidenceReview } from "../../types";

const labels = { met: "Đáp ứng", partial: "Đáp ứng một phần", not_evidenced: "Chưa có bằng chứng" };
export function EvidenceReviewPanel({ review, busy, stale, onRetry }: {
  review: EvidenceReview; busy: boolean; stale?: boolean; onRetry: () => void;
}) {
  const ready = !busy && !stale && review.status === "ready" && review.score !== null;
  return <section className="rounded-2xl border border-navy/10 bg-white p-6 space-y-5" aria-busy={busy}>
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div><h3 className="font-bold text-navy">Đối chiếu CV với yêu cầu tuyển dụng</h3>
        <p className="text-sm text-ink-variant mt-1">Đánh giá thử nghiệm, cần đối chiếu với hồ sơ gốc.</p></div>
      <button type="button" onClick={onRetry} disabled={busy}
        className="rounded-lg border border-navy/20 px-3 py-2 text-sm font-semibold disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2">
        {busy ? "Đang phân tích…" : "Phân tích lại"}
      </button>
    </div>
    <div role="status" aria-live="polite" className="rounded-xl bg-navy/5 p-4">
      <p className="text-lg font-bold text-navy">{busy ? "Đang đối chiếu hồ sơ…" : stale ? "Bạn đã đổi CV. Hãy phân tích lại." : ready
        ? `${review.score?.toLocaleString("vi-VN", { maximumFractionDigits: 2 })}/100 điểm theo yêu cầu`
        : review.status === "unavailable" ? "Chưa thể đánh giá" : "Cần kiểm tra thủ công"}</p>
      {!busy && !stale && <p className="mt-2 text-sm text-ink-variant">{review.summary}</p>}
    </div>
    {!busy && !stale && <ol className="space-y-4">{review.assessments.map(a => <li key={a.id} className="border-t border-navy/10 pt-4">
      <div className="flex flex-wrap justify-between gap-2"><h4 className="font-semibold text-navy break-words">{a.requirement_text}</h4>
        <span className="text-sm text-ink-variant">Mức ưu tiên: {a.weight}</span></div>
      <p className="mt-2 text-sm font-semibold">{a.evidence_signals?.review_reasons.length ? "Cần đối chiếu bằng chứng" : labels[a.status]}</p>
      <p className="mt-1 text-sm text-ink-variant">{a.comment}</p>
      {!!a.evidence_signals?.contexts.length && <details className="mt-2 text-sm"><summary className="cursor-pointer font-medium">Xem đoạn CV liên quan</summary>
        {a.evidence_signals.contexts.map((context, i) => <blockquote key={i} className="mt-2 border-l-2 border-amber-400 pl-3 whitespace-pre-wrap break-words">{context.text}</blockquote>)}
      </details>}
    </li>)}</ol>}
  </section>;
}
