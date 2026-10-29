import { useEffect, useState, type FormEvent } from "react";
import { IconExternalLink, IconFileText, IconHistory } from "@tabler/icons-react";
import { Avatar, Button, Modal, Skeleton } from "~/components/ui";
import { QueryBoundary } from "~/components/shared/QueryBoundary";
import { useUIStore } from "~/stores/useUIStore";
import {
  toSafeDocumentUrl,
  toStatusUpdateRequest,
  validateStatusReason,
} from "../contracts/hrContracts";
import {
  useRecruiterApplication,
  useUpdateApplicationStatus,
} from "../hooks/useRecruiterApplications";
import type { UpdatableApplicationStatus } from "../types";
import { ApplicationStatusBadge, applicationStatusLabels, updatableApplicationStatuses } from "./ApplicationStatusBadge";

export function ApplicationDetailsModal({ applicationId, onClose }: { applicationId: string | null; onClose: () => void }) {
  const applicationQuery = useRecruiterApplication(applicationId);
  const updateStatus = useUpdateApplicationStatus();
  const showToast = useUIStore((state) => state.showToast);
  const [status, setStatus] = useState<UpdatableApplicationStatus>("Screening");
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState<string>();

  useEffect(() => {
    const application = applicationQuery.data;
    if (!application) return;
    if (application.status !== "Withdrawn") setStatus(application.status);
    setReason("");
    setReasonError(undefined);
  }, [applicationQuery.data]);

  const saveStatus = async (event: FormEvent) => {
    event.preventDefault();
    const error = validateStatusReason(reason);
    setReasonError(error);
    if (error || !applicationId) return;
    if (status === applicationQuery.data?.status) {
      showToast("Hãy chọn trạng thái khác trạng thái hiện tại", "error");
      return;
    }
    try {
      await updateStatus.mutateAsync({ id: applicationId, input: toStatusUpdateRequest(status, reason) });
    } catch (mutationError) {
      showToast(mutationError instanceof Error ? mutationError.message : "Không thể cập nhật trạng thái", "error");
    }
  };

  const application = applicationQuery.data;
  const cvUrl = toSafeDocumentUrl(application?.cvFileUrl);
  return (
    <Modal open={Boolean(applicationId)} onClose={onClose} title="Chi tiết ứng viên" className="max-w-xl">
      <QueryBoundary isLoading={applicationQuery.isLoading} error={applicationQuery.error} onRetry={() => applicationQuery.refetch()} skeleton={<div className="space-y-3"><Skeleton className="h-16" /><Skeleton className="h-28" /><Skeleton className="h-28" /></div>}>
        {application && (
          <div className="space-y-4">
            {/* Header: Candidate Info & Badge */}
            <div className="flex items-start justify-between gap-3 pb-3 border-b border-border-subtle">
              <div className="flex items-center gap-3 min-w-0">
                <Avatar src={application.candidateAvatarUrl ?? undefined} name={application.candidateFullName} size="md" />
                <div className="min-w-0">
                  <h3 className="font-bold text-base text-navy truncate">{application.candidateFullName}</h3>
                  <div className="flex flex-wrap items-center gap-x-2 text-xs text-ink-variant mt-0.5">
                    <span>{application.candidatePhone ?? "Chưa có số điện thoại"}</span>
                    {application.candidateEmail && (
                      <>
                        <span className="text-ink-muted">•</span>
                        <span className="text-ink-muted truncate">{application.candidateEmail}</span>
                      </>
                    )}
                  </div>
                  <p className="text-xs text-ink-muted mt-0.5 truncate">
                    Ứng tuyển <span className="font-medium text-navy">{application.jobTitle}</span> · {new Date(application.appliedAt).toLocaleDateString("vi-VN")}
                  </p>
                </div>
              </div>
              <div className="shrink-0 pt-0.5">
                <ApplicationStatusBadge status={application.status} />
              </div>
            </div>

            {/* CV & Cover Letter */}
            <div className="rounded-default border border-border-subtle bg-surface-low/60 p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-default bg-navy/10 text-navy">
                    <IconFileText size={18} aria-hidden="true" />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-xs font-semibold text-navy">
                      {application.cvTitle ?? "CV ứng tuyển"}
                    </p>
                    <p className="text-[11px] text-ink-muted">Tài liệu hồ sơ</p>
                  </div>
                </div>
                {cvUrl ? (
                  <a
                    href={cvUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-default border border-border-strong bg-white px-2.5 py-1 text-xs font-semibold text-navy shadow-xs hover:border-gold hover:text-gold transition-colors"
                  >
                    <span>Mở CV</span>
                    <IconExternalLink size={14} aria-hidden="true" />
                  </a>
                ) : (
                  <span className="text-xs text-ink-muted italic">Không tìm thấy file CV</span>
                )}
              </div>

              {application.coverLetter?.trim() ? (
                <div className="mt-2.5 border-t border-border-subtle pt-2">
                  <p className="text-[11px] font-medium text-ink-muted mb-1">Thư ứng tuyển:</p>
                  <p className="max-h-24 overflow-y-auto rounded bg-white p-2 text-xs leading-relaxed text-ink-variant border border-border-subtle/60 whitespace-pre-wrap">
                    {application.coverLetter}
                  </p>
                </div>
              ) : (
                <p className="mt-2 border-t border-border-subtle pt-1.5 text-[11px] text-ink-muted italic">
                  Ứng viên không gửi thư ứng tuyển.
                </p>
              )}
            </div>

            {/* Status Update Form */}
            <form onSubmit={saveStatus} className="rounded-default border border-border-subtle bg-surface p-3.5 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-navy uppercase tracking-wider">Cập nhật trạng thái</h4>
                {application.status === "Withdrawn" && (
                  <span className="text-xs text-rose-500 font-medium">Đã rút hồ sơ</span>
                )}
              </div>

              {application.status === "Withdrawn" ? (
                <p className="text-xs text-ink-muted">Ứng viên đã rút hồ sơ nên không thể cập nhật trạng thái.</p>
              ) : (
                <div className="space-y-2.5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div>
                      <label htmlFor="application-status" className="block text-[11px] font-medium text-ink mb-1">
                        Trạng thái mới
                      </label>
                      <select
                        id="application-status"
                        value={status}
                        onChange={(event) => setStatus(event.target.value as UpdatableApplicationStatus)}
                        className="h-9 w-full rounded-default border border-border-strong bg-white px-2.5 text-xs text-ink focus:border-gold outline-none"
                      >
                        {updatableApplicationStatuses.map((value) => (
                          <option key={value} value={value}>
                            {applicationStatusLabels[value]}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label htmlFor="application-reason" className="block text-[11px] font-medium text-ink mb-1">
                        Lý do / ghi chú <span className="text-ink-muted">(tùy chọn)</span>
                      </label>
                      <input
                        id="application-reason"
                        type="text"
                        maxLength={500}
                        placeholder="Nhập lý do thay đổi..."
                        value={reason}
                        onChange={(event) => setReason(event.target.value)}
                        className="h-9 w-full rounded-default border border-border-strong bg-white px-2.5 text-xs text-ink focus:border-gold outline-none"
                      />
                    </div>
                  </div>

                  {reasonError && (
                    <p role="alert" className="text-xs text-danger">{reasonError}</p>
                  )}

                  <div className="flex justify-end pt-0.5">
                    <Button
                      type="submit"
                      size="sm"
                      disabled={updateStatus.isPending}
                      className="text-white"
                    >
                      {updateStatus.isPending ? "Đang cập nhật..." : "Cập nhật trạng thái"}
                    </Button>
                  </div>
                </div>
              )}
            </form>

            {/* Timeline */}
            <div className="pt-1">
              <div className="flex items-center gap-1.5 mb-2">
                <IconHistory size={15} className="text-ink-muted" aria-hidden="true" />
                <h4 className="text-xs font-bold text-navy uppercase tracking-wider">Lịch sử trạng thái</h4>
              </div>

              {application.timeline.length ? (
                <ol className="max-h-36 overflow-y-auto space-y-2 border-l border-border-subtle pl-3 ml-1.5 text-xs">
                  {application.timeline.map((item, index) => {
                    const reason = formatTimelineReason(item.reason);
                    return (
                      <li key={`${item.changedAt}-${index}`} className="relative">
                        <span className="absolute -left-[15px] top-1.5 h-1.5 w-1.5 rounded-full bg-navy/40" />
                        <div className="flex flex-wrap items-center gap-x-2">
                          <span className="font-semibold text-navy">{applicationStatusLabels[item.toStatus]}</span>
                          <span className="text-[11px] text-ink-muted">{new Date(item.changedAt).toLocaleString("vi-VN")}</span>
                        </div>
                        {reason && <p className="text-[11px] text-ink-variant mt-0.5">{reason}</p>}
                      </li>
                    );
                  })}
                </ol>
              ) : (
                <p className="text-xs text-ink-muted italic pl-1">Chưa có lịch sử thay đổi.</p>
              )}
            </div>
          </div>
        )}
      </QueryBoundary>
    </Modal>
  );
}

function formatTimelineReason(reason?: string | null): string | null {
  if (!reason?.trim()) return null;
  const trimmed = reason.trim();
  if (["initial application submission", "candidate withdrew application"].includes(trimmed.toLowerCase())) return null;
  return /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(trimmed) ? trimmed : null;
}
