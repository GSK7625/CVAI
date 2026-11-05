import type { EvidenceReview } from "../../types";

const labels = { met: "Đáp ứng", partial: "Đáp ứng một phần", not_evidenced: "Chưa có bằng chứng", needs_review: "Cần đối chiếu thêm" };
const priorityLabels = { mandatory: "Bắt buộc", standard: "Yêu cầu thông thường", preferred: "Ưu tiên" };
const issueMessages: Record<string, string> = {
  unrecognized_requirement: "Đã giữ lại yêu cầu này nhưng chưa tách được tiêu chí cụ thể để chấm tự động.",
  unknown_list_member: "Danh sách còn kỹ năng chưa được nhận diện; cần đối chiếu cả câu gốc.",
  invalid_duration: "Khoảng kinh nghiệm trong JD chưa hợp lệ hoặc không rõ ràng.",
  unmodeled_terms: "Hệ thống chưa hiểu đầy đủ điều kiện nghiệp vụ trong câu này.",
  alternative_or_group: "Câu có nhiều lựa chọn; hệ thống chưa xác định được cách đánh giá chung.",
  unsupported_constraint: "Mức độ hoặc khoảng kinh nghiệm này cần được đối chiếu trực tiếp.",
  skill_specific_duration: "Cần kiểm tra thời gian kinh nghiệm của riêng kỹ năng được yêu cầu.",
  unsupported_number: "Cần đối chiếu điều kiện số lượng, chứng chỉ hoặc phiên bản trong câu này.",
  ambiguous_role_or_duration: "Chưa xác định chắc vai trò hoặc thời gian kinh nghiệm được yêu cầu.",
  mixed_skill_levels: "Cần xác định riêng mức kinh nghiệm yêu cầu cho từng kỹ năng.",
  mixed_priority: "Cần tách rõ yêu cầu bắt buộc và yêu cầu ưu tiên.",
  mixed_negation: "Cần xác định rõ điều kiện nào là bắt buộc và điều kiện nào không bắt buộc.",
  conflicting_priority: "JD nêu các mức ưu tiên khác nhau cho cùng một yêu cầu.",
  too_many_requirements: "JD có hơn 20 yêu cầu, vượt giới hạn đánh giá hiện tại.",
};

export function EvidenceReviewPanel({ review, busy, stale, onRetry }: {
  review: EvidenceReview; busy: boolean; stale?: boolean; onRetry: () => void;
}) {
  const issues = review.jd_profile?.unresolved.filter(issue =>
    issue.code !== "no_requirements" || review.jd_profile?.unresolved.length === 1) ?? [];
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
        : review.status === "unavailable" ? "Chưa thể đánh giá" : "Chưa có điểm tổng"}</p>
      {!busy && !stale && <p className="mt-2 text-sm text-ink-variant">{review.summary}</p>}
    </div>
    {!busy && !stale && !!review.skill_mentions?.length && <div className="space-y-3">
      <h4 className="font-semibold text-navy">Đối chiếu tên kỹ năng trong JD và CV</h4>
      <p className="text-sm text-ink-variant">Việc CV nhắc tới kỹ năng chưa xác nhận mức thành thạo, thời gian hoặc kinh nghiệm làm việc mà JD yêu cầu.</p>
      {review.skill_mentions.map(item => <details key={item.skill} className="rounded-lg border border-navy/10 p-3 text-sm">
        <summary className="cursor-pointer font-medium">{item.skill} · {item.contexts.length ? "Có nhắc trong CV" : "Chưa tìm thấy tên kỹ năng trong CV"}</summary>
        {item.contexts.map((context, i) => <blockquote key={i} className="mt-2 border-l-2 border-amber-400 pl-3 whitespace-pre-wrap break-words">{context.text}</blockquote>)}
      </details>)}
    </div>}
    {!busy && !stale && issues.length > 0 && <details className="border-t border-navy/10 pt-4 text-sm">
      <summary className="cursor-pointer font-semibold text-navy">Xem {issues.length} yêu cầu JD cần đối chiếu thêm</summary>
      <ul className="mt-3 space-y-3">{issues.map((issue, i) => <li key={i} className="border-t border-navy/10 pt-3">
        {issue.text && <blockquote className="whitespace-pre-wrap break-words text-navy">{issue.text}</blockquote>}
        <p className="mt-1 text-ink-variant">{issueMessages[issue.code] ?? "Yêu cầu này chưa được hỗ trợ tự động; hãy đối chiếu với CV gốc."}</p>
      </li>)}</ul>
    </details>}
    {!busy && !stale && !!review.assessments.length && review.jd_profile?.unresolved.length ? <h4 className="font-semibold text-navy">Kết quả cho các yêu cầu đã đọc được</h4> : null}
    {!busy && !stale && <ol className="space-y-4">{review.assessments.map(a => <li key={a.id} className="border-t border-navy/10 pt-4">
      <div className="flex flex-wrap justify-between gap-2"><h4 className="font-semibold text-navy break-words">{a.requirement_text}</h4>
        <span className="text-sm text-ink-variant">{a.priority ? priorityLabels[a.priority] : `Mức ưu tiên: ${a.weight}`}</span></div>
      <p className="mt-2 text-sm font-semibold">{a.evidence_signals?.review_reasons.length ? "Cần đối chiếu bằng chứng" : labels[a.status]}</p>
      <p className="mt-1 text-sm text-ink-variant">{a.comment}</p>
      {!!a.jd_sources?.length && <details className="mt-2 text-sm"><summary className="cursor-pointer font-medium">Xem câu JD gốc</summary>
        {a.jd_sources.map((source, i) => <blockquote key={i} className="mt-2 border-l-2 border-navy/20 pl-3 whitespace-pre-wrap break-words">{source.text}</blockquote>)}
      </details>}
      {!!a.evidence_signals?.contexts.length && <details className="mt-2 text-sm"><summary className="cursor-pointer font-medium">Xem đoạn CV liên quan</summary>
        {a.evidence_signals.contexts.map((context, i) => <blockquote key={i} className="mt-2 border-l-2 border-amber-400 pl-3 whitespace-pre-wrap break-words">{context.text}</blockquote>)}
      </details>}
    </li>)}</ol>}
    {!busy && !stale && review.jd_profile?.ignored?.some(item => item.reason === "explicitly_not_required") && <details className="border-t border-navy/10 pt-4 text-sm">
      <summary className="cursor-pointer font-medium">Điều kiện không bắt buộc, đã loại khỏi đánh giá</summary>
      {review.jd_profile.ignored.filter(item => item.reason === "explicitly_not_required").map((item, i) =>
        <blockquote key={i} className="mt-2 border-l-2 border-navy/20 pl-3 whitespace-pre-wrap break-words">{item.text}</blockquote>)}
    </details>}
  </section>;
}
