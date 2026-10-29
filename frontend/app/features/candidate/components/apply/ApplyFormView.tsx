/**
 * @file ApplyFormView.tsx
 * @description View quản lý toàn bộ luồng nộp hồ sơ ứng tuyển vị trí việc làm (FC-81a, P3-UC01).
 * @architecture
 * - Quản lý toàn bộ state, queries, submit mutation và kiểm tra lỗi 409 (err instanceof ApiError && err.status === 409).
 * - Kết hợp các section component con: CandidateInfoSection, CvPickerSection, MatchPreviewSection, CoverLetterSection, ApplySuccess, AlreadyAppliedModal.
 */

import { useState, useEffect, useRef, type FormEvent, type ChangeEvent } from "react";
import { Link, useNavigate } from "react-router";
import {
  IconArrowLeft,
  IconArrowRight,
  IconBuilding,
  IconMapPin,
  IconAlertCircle,
  IconLoader2,
  IconCoin,
} from "@tabler/icons-react";
import { useJobDetail } from "../../hooks/useJobDetail";
import { useCandidateCvs, useUploadCandidateCv } from "../../hooks/useCandidateCvs";
import { usePreviewJobMatch } from "../../hooks/usePreviewJobMatch";
import { useApplyJob } from "../../hooks/useApplyJob";
import { useCandidateProfile } from "../../hooks/useCandidateProfile";
import { CandidateInfoSection } from "./CandidateInfoSection";
import { CvPickerSection } from "./CvPickerSection";
import { MatchPreviewSection } from "./MatchPreviewSection";
import { CoverLetterSection } from "./CoverLetterSection";
import { ApplySuccess } from "./ApplySuccess";
import { AlreadyAppliedModal } from "./AlreadyAppliedModal";
import { useAuthStore } from "~/stores/useAuthStore";
import { useUIStore } from "~/stores/useUIStore";
import { ApiError } from "~/lib/fetcher";
import { Skeleton } from "~/components/ui";
import { validateCvFile, cvTitleFromFile } from "~/utils";

interface ApplyFormViewProps {
  jobId: string;
}

export function ApplyFormView({ jobId }: ApplyFormViewProps) {
  const navigate = useNavigate();
  const showToast = useUIStore((s) => s.showToast);
  const user = useAuthStore((s) => s.user);

  const { email: profileEmail, profile, isLoading: isProfileLoading } = useCandidateProfile();

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Queries
  const { data: job, isLoading: isJobLoading, isError: isJobError } = useJobDetail(jobId);
  const { data: cvs = [], isLoading: isCvsLoading } = useCandidateCvs();
  const uploadCvMutation = useUploadCandidateCv();
  const applyMutation = useApplyJob(jobId);

  // Form states
  const [selectedCvId, setSelectedCvId] = useState<string>("");
  const [coverLetter, setCoverLetter] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [alreadyAppliedModal, setAlreadyAppliedModal] = useState(false);
  const [isUploadingInline, setIsUploadingInline] = useState(false);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [analyzedCvId, setAnalyzedCvId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Tự động chọn CV chính hoặc CV đầu tiên khi load danh sách
  useEffect(() => {
    if (cvs.length > 0 && !selectedCvId) {
      const primaryCv = cvs.find((c) => c.isPrimary) ?? cvs[0];
      setSelectedCvId(primaryCv.id);
    }
  }, [cvs, selectedCvId]);

  // On-demand AI Match Preview Query (Option A)
  const {
    data: matchPreview,
    isLoading: isMatchQueryLoading,
    refetch: refetchMatch,
  } = usePreviewJobMatch(
    jobId,
    selectedCvId || undefined,
    hasAnalyzed,
  );

  // Kích hoạt phân tích độ phù hợp với hiệu ứng quét thời gian thực
  const handleAnalyze = async (targetCvId?: string) => {
    const cvToAnalyze = targetCvId || selectedCvId;
    if (!cvToAnalyze) {
      showToast("Vui lòng chọn hoặc tải lên một bản CV trước khi phân tích.", "error");
      return;
    }

    setIsAnalyzing(true);
    setHasAnalyzed(true);
    setAnalyzedCvId(cvToAnalyze);

    try {
      await Promise.all([
        refetchMatch(),
        new Promise((resolve) => setTimeout(resolve, 500)),
      ]);
    } catch {
      // Error được phản hồi trong query/preview
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Tự động phân tích lại mượt mà ngay khi ứng viên click chọn bản CV khác
  const handleSelectCv = (id: string) => {
    if (id === selectedCvId) return;
    setSelectedCvId(id);
    if (hasAnalyzed) {
      handleAnalyze(id);
    }
  };

  const selectedCv = cvs.find((c) => c.id === selectedCvId);
  const isCvChangedAfterAnalysis =
    hasAnalyzed && analyzedCvId !== null && analyzedCvId !== selectedCvId;

  // Xử lý upload file CV trực tiếp ngay tại trang apply
  const handleInlineFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validationError = validateCvFile(file);
    if (validationError) {
      showToast(validationError, "error");
      return;
    }

    setIsUploadingInline(true);
    try {
      const newCv = await uploadCvMutation.mutateAsync({
        file,
        title: cvTitleFromFile(file.name),
      });
      setSelectedCvId(newCv.id);
      if (hasAnalyzed) {
        handleAnalyze(newCv.id);
      }
    } catch {
      // Error đã được handle trong hook toast
    } finally {
      setIsUploadingInline(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!selectedCvId) {

      showToast("Vui lòng chọn hoặc tải lên một bản CV để ứng tuyển.", "error");
      return;
    }

    applyMutation.mutate(
      {
        cvId: selectedCvId,
        coverLetter: coverLetter.trim() || undefined,
      },
      {
        onSuccess: () => {
          setSubmitted(true);
        },
        onError: (err) => {
          if (err instanceof ApiError && err.status === 409) {
            setAlreadyAppliedModal(true);
          } else {
            showToast(err.message || "Nộp hồ sơ thất bại. Vui lòng kiểm tra lại.", "error");
          }
        },
      },
    );
  };

  // State: Loading Job Data
  if (isJobLoading) {
    return (
      <div className="mx-auto max-w-4xl py-12 px-4 sm:px-6">
        <div className="space-y-6">
          <Skeleton className="h-6 w-48 rounded-full" />
          <Skeleton className="h-12 w-3/4 rounded-2xl" />
          <div className="p-1.5 rounded-[2rem] bg-navy/5 border border-navy/10">
            <div className="p-8 bg-white rounded-[calc(2rem-0.375rem)] space-y-4">
              <Skeleton className="h-8 w-1/2 rounded-lg" />
              <Skeleton className="h-20 w-full rounded-xl" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // State: Job Not Found or Error
  if (isJobError || !job) {
    return (
      <div className="mx-auto max-w-xl py-20 px-4 text-center">
        <div className="p-1.5 rounded-[2rem] bg-navy/5 border border-navy/10 shadow-sm">
          <div className="p-10 bg-white rounded-[calc(2rem-0.375rem)] flex flex-col items-center">
            <div className="w-14 h-14 rounded-full bg-rose-50 flex items-center justify-center text-rose-500 mb-4">
              <IconAlertCircle size={32} stroke={1.5} />
            </div>
            <h2 className="text-xl font-bold text-navy">Không tìm thấy thông tin việc làm</h2>
            <p className="mt-2 text-ink-variant text-sm">
              Tin tuyển dụng này có thể đã hết hạn hoặc không tồn tại.
            </p>
            <Link
              to="/jobs"
              className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-full bg-navy text-white text-sm font-medium hover:bg-navy-secondary transition-all"
            >
              <IconArrowLeft size={16} /> Quay lại danh sách việc làm
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // State: Submitted Successfully
  if (submitted) {
    return <ApplySuccess jobTitle={job.title} companyName={job.company} />;
  }

  return (
    <div className="min-h-[100dvh] pb-24 pt-4 sm:pt-6">
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        {/* Breadcrumb navigation */}
        <nav className="mb-6 flex items-center gap-2 text-xs font-medium text-ink-variant" aria-label="Breadcrumb">
          <Link to="/jobs" className="hover:text-navy transition-colors">
            Việc làm
          </Link>
          <span className="text-ink-muted">/</span>
          <Link to={`/jobs/${jobId}`} className="hover:text-navy line-clamp-1 max-w-[200px] transition-colors">
            {job.title}
          </Link>
          <span className="text-ink-muted">/</span>
          <span className="text-navy font-semibold">Ứng tuyển trực tuyến</span>
        </nav>

        {/* Header summary card with double-bezel */}
        <div className="p-1.5 rounded-[2rem] bg-navy/5 border border-navy/10 shadow-sm mb-8 transition-all">
          <div className="p-6 sm:p-8 bg-white rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.8)]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                {job.companyLogo ? (
                  <img
                    src={job.companyLogo}
                    alt={job.company}
                    className="w-16 h-16 rounded-2xl object-cover border border-navy/10 shadow-xs"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-2xl bg-navy/5 border border-navy/10 flex items-center justify-center text-navy font-bold text-xl">
                    <IconBuilding size={28} stroke={1.5} />
                  </div>
                )}
                <div>
                  <div className="inline-flex items-center gap-2 rounded-full px-2.5 py-0.5 bg-navy/5 text-navy text-[10px] uppercase tracking-[0.15em] font-semibold mb-1">
                    Đang tuyển dụng
                  </div>
                  <h1 className="text-xl sm:text-2xl font-bold text-navy leading-tight">
                    {job.title}
                  </h1>
                  <p className="text-sm font-medium text-ink-variant mt-0.5 flex items-center gap-2">
                    <span>{job.company}</span>
                    <span className="text-ink-muted">•</span>
                    <span className="inline-flex items-center gap-1 text-xs">
                      <IconMapPin size={14} className="text-ink-muted" />
                      {job.location}
                    </span>
                  </p>
                </div>
              </div>

              {/* Salary badge */}
              <div className="self-start sm:self-center px-4 py-2 rounded-2xl bg-amber-50/70 border border-amber-200/50 text-right">
                <p className="text-[11px] font-medium text-amber-800 uppercase tracking-wider flex items-center gap-1">
                  <IconCoin size={14} /> Mức lương
                </p>
                <p className="text-base font-bold text-navy">
                  {job.salaryMin && job.salaryMax
                    ? `${job.salaryMin} - ${job.salaryMax} triệu`
                    : job.salaryMin
                      ? `Từ ${job.salaryMin} triệu`
                      : job.salaryMax
                        ? `Đến ${job.salaryMax} triệu`
                        : "Thương lượng"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Application Form */}
        <form onSubmit={handleSubmit} noValidate className="space-y-8">
          {/* Section 1: Thông tin ứng viên */}
          <CandidateInfoSection
            fullName={profile?.fullName || user?.fullName}
            email={profile?.email || profileEmail || user?.email}
            phone={profile?.phone}
            isLoading={isProfileLoading}
          />

          {/* Section 2: Chọn CV ứng tuyển */}
          <CvPickerSection
            cvs={cvs}
            selectedCvId={selectedCvId}
            onSelectCv={handleSelectCv}
            isLoading={isCvsLoading}
            isUploadingInline={isUploadingInline}
            onUploadFile={handleInlineFileUpload}
            fileInputRef={fileInputRef}
          />

          {/* Section 3: On-Demand AI Match Preview (Option A) */}
          {selectedCvId && (
            <MatchPreviewSection
              preview={matchPreview}
              isLoading={isAnalyzing || isMatchQueryLoading}
              hasAnalyzed={hasAnalyzed}
              onAnalyze={handleAnalyze}
              selectedCvTitle={selectedCv?.title}
              isCvChangedAfterAnalysis={isCvChangedAfterAnalysis}
            />
          )}

          {/* Section 4: Thư giới thiệu */}
          <CoverLetterSection value={coverLetter} onChange={setCoverLetter} />

          {/* Form Actions: Button-in-button trailing icon */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
            <Link
              to={`/jobs/${jobId}`}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full text-sm font-semibold text-ink-variant hover:text-navy hover:bg-navy/5 transition-all"
            >
              <IconArrowLeft size={16} /> Quay lại chi tiết việc làm
            </Link>

            <button
              type="submit"
              disabled={applyMutation.isPending || !selectedCvId}
              className="group w-full sm:w-auto inline-flex items-center justify-between gap-5 rounded-full bg-navy px-8 py-3.5 text-sm font-semibold text-white shadow-lg hover:bg-navy-secondary active:scale-[0.98] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>{applyMutation.isPending ? "Đang gửi hồ sơ..." : "Xác nhận nộp đơn"}</span>
              <span className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center transition-transform duration-300 group-hover:translate-x-1">
                {applyMutation.isPending ? (
                  <IconLoader2 size={15} className="animate-spin" />
                ) : (
                  <IconArrowRight size={15} />
                )}
              </span>
            </button>
          </div>
        </form>
      </div>

      {/* Modal báo lỗi 409: Đã ứng tuyển trước đó */}
      <AlreadyAppliedModal
        open={alreadyAppliedModal}
        onClose={() => setAlreadyAppliedModal(false)}
        jobTitle={job.title}
        onNavigateApplications={() => {
          setAlreadyAppliedModal(false);
          navigate("/candidate/applications");
        }}
      />
    </div>
  );
}
