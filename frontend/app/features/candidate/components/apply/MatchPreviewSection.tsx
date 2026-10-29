import {
  IconSparkles,
  IconLoader2,
  IconRefresh,
  IconBriefcase,
  IconSchool,
  IconCheck,
  IconAlertCircle,
} from "@tabler/icons-react";
import type { JobMatchPreviewResponse } from "../../types";
import { Skeleton } from "~/components/ui";

interface MatchPreviewSectionProps {
  preview: JobMatchPreviewResponse | null | undefined;
  isLoading: boolean;
  hasAnalyzed: boolean;
  onAnalyze: () => void;
  selectedCvTitle?: string | null;
  isCvChangedAfterAnalysis?: boolean;
}

export function MatchPreviewSection({
  preview,
  isLoading,
  hasAnalyzed,
  onAnalyze,
  selectedCvTitle,
  isCvChangedAfterAnalysis,
}: MatchPreviewSectionProps) {
  // Determine badge color and rating label based on match score
  const getScoreMeta = (score: number) => {
    if (score >= 80) {
      return {
        badgeBg: "bg-emerald-600 text-white",
        barGradient: "from-emerald-500 to-teal-500",
        label: "Rất phù hợp",
        cardBorder: "border-emerald-200/60 bg-emerald-500/5",
      };
    }
    if (score >= 50) {
      return {
        badgeBg: "bg-amber-600 text-white",
        barGradient: "from-amber-500 to-emerald-500",
        label: "Khá tiềm năng",
        cardBorder: "border-amber-400/20 bg-amber-500/10",
      };
    }
    return {
      badgeBg: "bg-rose-600 text-white",
      barGradient: "from-rose-500 to-amber-500",
      label: "Cần cân nhắc",
      cardBorder: "border-rose-300/30 bg-rose-500/5",
    };
  };

  const scoreMeta = preview ? getScoreMeta(preview.matchScore) : null;

  return (
    <div
      className={`p-1.5 rounded-[2rem] border transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] ${scoreMeta ? scoreMeta.cardBorder : "border-amber-400/20 bg-amber-500/10"
        }`}
    >
      <div className="p-6 sm:p-8 bg-white rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.8)]">
        {/* Card Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-navy/5 pb-4 mb-4 gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-100/80 border border-amber-300/40 flex items-center justify-center text-amber-700 shrink-0 shadow-2xs">
              <IconSparkles size={19} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-navy">
                  Độ phù hợp hồ sơ (AI Match Preview)
                </h3>
                {selectedCvTitle && (
                  <span className="hidden md:inline-block px-2 py-0.5 rounded-full bg-navy/5 text-navy text-[10px] font-semibold truncate max-w-[200px]">
                    {selectedCvTitle}
                  </span>
                )}
              </div>
              <p className="text-xs text-ink-variant">
                Phân tích đối chiếu toàn diện kỹ năng, kinh nghiệm và học vấn với yêu cầu vị trí
              </p>
            </div>
          </div>

          {isLoading ? (
            <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-800 bg-amber-50 px-3.5 py-1.5 rounded-full border border-amber-200 self-start sm:self-auto shadow-2xs">
              <IconLoader2 size={14} className="animate-spin text-amber-700" />
              <span>Đang phân tích...</span>
            </div>
          ) : hasAnalyzed && preview ? (
            <div className="flex items-center gap-2 self-start sm:self-auto">
              <div
                className={`px-3.5 py-1 rounded-full text-xs font-bold shadow-xs transition-all ${scoreMeta?.badgeBg || "bg-navy text-white"
                  }`}
              >
                {preview.matchScore}% Phù hợp • {scoreMeta?.label}
              </div>
              <button
                type="button"
                onClick={onAnalyze}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-navy hover:text-gold hover:bg-navy/5 transition-colors cursor-pointer"
                title="Phân tích lại"
              >
                <IconRefresh size={13} />
                <span>Quét lại</span>
              </button>
            </div>
          ) : null}
        </div>

        {/* State 1: Scanning / Loading */}
        {isLoading ? (
          <div className="py-2 space-y-4">
            <div className="flex items-center gap-2 text-xs font-medium text-amber-800 animate-pulse">
              <IconSparkles size={15} className="text-gold shrink-0" />
              <span>
                AI đang trích xuất dữ liệu, đối chiếu đa tiêu chí và tính toán mức độ tương thích...
              </span>
            </div>
            <div className="w-full bg-navy/5 h-2 rounded-full overflow-hidden relative">
              <div className="h-full bg-gradient-to-r from-amber-500 via-teal-500 to-emerald-500 rounded-full w-3/4 animate-pulse" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
              <Skeleton className="h-20 w-full rounded-xl" />
              <Skeleton className="h-20 w-full rounded-xl" />
              <Skeleton className="h-20 w-full rounded-xl" />
            </div>
          </div>
        ) : !hasAnalyzed ? (
          /* State 2: Ready / Prompt to Scan */
          <div className="py-1">
            <p className="text-xs text-ink-variant leading-relaxed">
              Bạn có thể sử dụng AI để kiểm tra nhanh mức độ phù hợp của bản CV{" "}
              {selectedCvTitle ? (
                <strong className="text-navy font-semibold">"{selectedCvTitle}"</strong>
              ) : (
                "đang chọn"
              )}{" "}
              với các tiêu chí tuyển dụng trước khi nộp hồ sơ.
            </p>
            <div className="mt-4 flex items-center justify-start">
              <button
                type="button"
                onClick={onAnalyze}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-navy text-white text-xs font-semibold hover:bg-navy-secondary transition-all shadow-xs cursor-pointer active:scale-[0.98]"
              >
                <IconSparkles size={15} className="text-gold" />
                <span>Phân tích độ phù hợp với AI</span>
              </button>
            </div>
          </div>
        ) : preview ? (
          /* State 3: Enhanced Analysis Result */
          <div className="space-y-4">
            {/* Banner cảnh báo nếu ứng viên vừa đổi CV khác (fallback nếu auto-sync chưa hoàn tất) */}
            {isCvChangedAfterAnalysis && (
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl bg-amber-50 border border-amber-200/70 text-xs">
                <span className="text-amber-900 font-medium">
                  Bạn vừa chọn một bản CV khác. Bấm cập nhật để xem phân tích cho bản CV mới.
                </span>
                <button
                  type="button"
                  onClick={onAnalyze}
                  className="px-3 py-1 rounded-lg bg-navy text-white font-semibold hover:bg-navy-secondary transition-colors shrink-0 inline-flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
                >
                  <IconRefresh size={13} />
                  <span>Cập nhật phân tích</span>
                </button>
              </div>
            )}

            {/* Match Score Bar */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-navy">Chỉ số tương thích tổng thể</span>
                <span className="font-bold text-navy">{preview.matchScore}/100</span>
              </div>
              <div className="w-full bg-navy/5 h-2.5 rounded-full overflow-hidden">
                <div
                  className={`h-full bg-gradient-to-r ${scoreMeta?.barGradient || "from-amber-500 to-emerald-500"
                    } rounded-full transition-all duration-1000 ease-[cubic-bezier(0.32,0.72,0,1)]`}
                  style={{ width: `${Math.min(100, Math.max(0, preview.matchScore))}%` }}
                />
              </div>
            </div>

            {/* Criteria Breakdown: 3 Columns Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
              {/* 1. Kỹ năng tương thích */}
              <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200/60 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <div className="w-5 h-5 rounded-full bg-emerald-200/80 text-emerald-800 flex items-center justify-center shrink-0">
                      <IconCheck size={12} stroke={3} />
                    </div>
                    <span className="text-[11px] uppercase tracking-wider font-bold text-emerald-900">
                      Kỹ năng khớp ({preview.matchedSkills?.length || 0})
                    </span>
                  </div>
                  {preview.matchedSkills && preview.matchedSkills.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {preview.matchedSkills.map((sk) => (
                        <span
                          key={sk}
                          className="px-2 py-0.5 rounded-md bg-white border border-emerald-300/60 text-emerald-800 text-[11px] font-medium shadow-2xs"
                        >
                          {sk}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-ink-muted italic">Chưa ghi nhận kỹ năng khớp trực tiếp</p>
                  )}
                </div>

                {/* Kỹ năng còn thiếu */}
                {preview.missingSkills && preview.missingSkills.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-emerald-200/50">
                    <span className="text-[10px] uppercase tracking-wider font-semibold text-amber-800 block mb-1">
                      Cần bổ sung ({preview.missingSkills.length}):
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {preview.missingSkills.map((sk) => (
                        <span
                          key={sk}
                          className="px-1.5 py-0.5 rounded bg-amber-100/80 border border-amber-300/60 text-amber-900 text-[10px] font-medium"
                        >
                          {sk}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* 2. Kinh nghiệm thực tế */}
              <div className="p-3.5 rounded-xl bg-navy/5 border border-navy/10 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <div className="w-5 h-5 rounded-full bg-navy/10 text-navy flex items-center justify-center shrink-0">
                      <IconBriefcase size={12} stroke={2.5} />
                    </div>
                    <span className="text-[11px] uppercase tracking-wider font-bold text-navy">
                      Kinh nghiệm làm việc
                    </span>
                  </div>
                  <p className="text-xs text-ink-variant leading-relaxed">
                    {preview.experienceComparison ||
                      "Đã đối chiếu số năm kinh nghiệm thực tế với yêu cầu của vị trí."}
                  </p>
                </div>
              </div>

              {/* 3. Trình độ học vấn & Bằng cấp */}
              <div className="p-3.5 rounded-xl bg-navy/5 border border-navy/10 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <div className="w-5 h-5 rounded-full bg-navy/10 text-navy flex items-center justify-center shrink-0">
                      <IconSchool size={12} stroke={2.5} />
                    </div>
                    <span className="text-[11px] uppercase tracking-wider font-bold text-navy">
                      Trình độ học vấn
                    </span>
                  </div>
                  <p className="text-xs text-ink-variant leading-relaxed">
                    {preview.educationComparison ||
                      "Đáp ứng yêu cầu học vấn và chuyên ngành đào tạo."}
                  </p>
                </div>
              </div>
            </div>

            {/* AI Explanation & Recommendations */}
            {preview.explanationDetails ? (
              <div className="bg-surface-low/90 p-4 rounded-xl border border-navy/10 space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-bold text-navy">
                  <IconSparkles size={14} className="text-amber-600" />
                  <span>Đánh giá chuyên sâu & Lời khuyên từ AI:</span>
                </div>
                <p className="text-xs text-ink leading-relaxed font-medium">
                  {preview.explanationDetails.summary}
                </p>

                {preview.explanationDetails.strengths && preview.explanationDetails.strengths.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[10px] uppercase tracking-wider font-bold text-emerald-800 block">
                      Điểm mạnh có bằng chứng xác thực:
                    </span>
                    <div className="space-y-1">
                      {preview.explanationDetails.strengths.map((st, idx) => (
                        <div key={idx} className="flex items-start gap-1.5 text-xs text-ink-variant">
                          <span className="text-emerald-600 mt-0.5">•</span>
                          <span>
                            <strong className="text-navy">{st.item}</strong>: {st.statement}{" "}
                            {st.evidence_source && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                                {st.evidence_source}
                              </span>
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {preview.explanationDetails.gaps && preview.explanationDetails.gaps.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[10px] uppercase tracking-wider font-bold text-amber-800 block">
                      Khoảng cách yêu cầu & rủi ro:
                    </span>
                    <div className="space-y-1">
                      {preview.explanationDetails.gaps.map((gap, idx) => (
                        <div key={idx} className="flex items-start gap-1.5 text-xs text-ink-variant">
                          <span className="text-amber-600 mt-0.5">•</span>
                          <span>
                            <strong className="text-navy">{gap.requirement}</strong>: {gap.statement}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {preview.explanationDetails.recommendations && preview.explanationDetails.recommendations.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[10px] uppercase tracking-wider font-bold text-navy block">
                      Khuyến nghị cải thiện hồ sơ:
                    </span>
                    <div className="space-y-1">
                      {preview.explanationDetails.recommendations.map((rec, idx) => (
                        <div key={idx} className="flex items-start gap-1.5 text-xs text-ink-variant">
                          <span className="text-navy mt-0.5 font-semibold">{idx + 1}.</span>
                          <span>{rec}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : preview.explanation ? (
              <div className="bg-surface-low/90 p-4 rounded-xl border border-navy/10 space-y-1.5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-navy">
                  <IconSparkles size={14} className="text-amber-600" />
                  <span>Đánh giá chuyên sâu & Lời khuyên từ AI:</span>
                </div>
                <p className="text-xs text-ink-variant leading-relaxed whitespace-pre-line">
                  {preview.explanation}
                </p>
              </div>
            ) : null}
          </div>
        ) : (
          <p className="text-xs text-ink-muted italic py-1">
            Không thể tải thông tin phân tích độ phù hợp. Bạn vẫn có thể nộp hồ sơ bình thường.
          </p>
        )}
      </div>
    </div>
  );
}
