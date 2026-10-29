import { useMemo, useState } from "react";
import { IconAlertTriangle, IconBriefcase, IconChevronLeft, IconChevronRight, IconEdit, IconEye, IconPlus, IconPower, IconSearch, IconTrash } from "@tabler/icons-react";
import { Badge, Button, EmptyState, Input, Modal, Skeleton } from "~/components/ui";
import { QueryBoundary } from "~/components/shared/QueryBoundary";
import { useDebounce } from "~/hooks/useDebounce";
import { useUIStore } from "~/stores/useUIStore";
import { useDeleteEmployerJob, useEmployerJob, useEmployerJobs, useToggleEmployerJob } from "../hooks/useEmployerJobs";
import type { ApprovalStatus, EmployerJobFilters, JobSummary } from "../types";
import { JobDetailsModal } from "./JobDetailsModal";
import { JobFormModal } from "./JobFormModal";

const approvalLabels: Record<ApprovalStatus, string> = { Pending: "Chờ duyệt", Approved: "Đã duyệt", Rejected: "Bị từ chối" };

function ApprovalBadge({ status }: { status: ApprovalStatus }) {
  return <Badge variant={status === "Approved" ? "success" : status === "Rejected" ? "danger" : "gold"}>{approvalLabels[status]}</Badge>;
}

function formatSalary(job: JobSummary) {
  if (job.salaryMin === null && job.salaryMax === null) return "Thỏa thuận";
  const formatter = new Intl.NumberFormat("vi-VN");
  if (job.salaryMin !== null && job.salaryMax !== null) return `${formatter.format(job.salaryMin)}–${formatter.format(job.salaryMax)} ${job.salaryCurrency}`;
  return `${formatter.format(job.salaryMin ?? job.salaryMax ?? 0)} ${job.salaryCurrency}`;
}

export function EmployerJobsPage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [filters, setFilters] = useState<EmployerJobFilters>({ pageIndex: 1, pageSize: 10 });
  const [createOpen, setCreateOpen] = useState(false);
  const [detailsId, setDetailsId] = useState<string | null>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<JobSummary | null>(null);
  const showToast = useUIStore((state) => state.showToast);
  const effectiveFilters = useMemo(() => ({ ...filters, keyword: debouncedSearch }), [filters, debouncedSearch]);
  const jobsQuery = useEmployerJobs(effectiveFilters);
  const editJobQuery = useEmployerJob(editId);
  const toggleJob = useToggleEmployerJob();
  const deleteJob = useDeleteEmployerJob();

  const setFilter = <K extends keyof EmployerJobFilters>(key: K, value: EmployerJobFilters[K]) => {
    setFilters((current) => ({ ...current, [key]: value, pageIndex: 1 }));
  };

  const handleToggle = async (job: JobSummary) => {
    try { await toggleJob.mutateAsync(job.id); }
    catch (error) { showToast(error instanceof Error ? error.message : "Không thể đổi trạng thái tin", "error"); }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteJob.mutateAsync(deleteTarget.id);
      setDeleteTarget(null);
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Không thể xóa tin tuyển dụng", "error");
    }
  };

  const jobs = jobsQuery.data?.items ?? [];
  return (
    <section aria-labelledby="jobs-title">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="text-label font-semibold text-gold">TUYỂN DỤNG</p><h1 id="jobs-title" className="mt-1 text-headline text-navy">Tin tuyển dụng</h1><p className="mt-2 text-ink-variant">Quản lý toàn bộ tin tuyển dụng thuộc công ty của bạn.</p></div>
        <Button onClick={() => setCreateOpen(true)} className="w-full sm:w-auto"><IconPlus size={19} aria-hidden="true" />Tạo tin tuyển dụng</Button>
      </div>

      <div className="mb-5 grid gap-3 rounded-default border border-border-subtle bg-surface p-4 shadow-surface md:grid-cols-[minmax(0,1fr)_13rem_13rem]">
        <Input aria-label="Tìm kiếm tin tuyển dụng" icon={<IconSearch size={18} aria-hidden="true" />} placeholder="Tìm theo tiêu đề" value={search} onChange={(event) => setSearch(event.target.value)} />
        <select aria-label="Lọc theo trạng thái duyệt" value={filters.approvalStatus ?? ""} onChange={(event) => setFilter("approvalStatus", event.target.value as ApprovalStatus | "")} className="h-11 rounded-default border border-border-strong bg-white px-3.5 text-ink focus:border-gold"><option value="">Mọi trạng thái duyệt</option><option value="Pending">Chờ duyệt</option><option value="Approved">Đã duyệt</option><option value="Rejected">Bị từ chối</option></select>
        <select aria-label="Lọc theo trạng thái hoạt động" value={filters.isActive === undefined ? "" : String(filters.isActive)} onChange={(event) => setFilter("isActive", event.target.value === "" ? undefined : event.target.value === "true")} className="h-11 rounded-default border border-border-strong bg-white px-3.5 text-ink focus:border-gold"><option value="">Đang mở và đã đóng</option><option value="true">Đang mở</option><option value="false">Đã đóng</option></select>
      </div>

      <QueryBoundary isLoading={jobsQuery.isLoading} error={jobsQuery.error} onRetry={() => jobsQuery.refetch()} skeleton={<JobsSkeleton />}>
        {jobs.length === 0 ? (
          <EmptyState icon={<IconBriefcase size={42} aria-hidden="true" />} title="Chưa có tin tuyển dụng" description="Tạo tin đầu tiên hoặc thay đổi điều kiện tìm kiếm." action={<Button onClick={() => setCreateOpen(true)}>Tạo tin tuyển dụng</Button>} />
        ) : (
          <>
            <div className="hidden overflow-x-auto rounded-default border border-border-subtle bg-surface shadow-surface lg:block">
              <table className="w-full text-left">
                <thead className="bg-surface-low text-label-sm uppercase tracking-wider text-ink-muted"><tr><th className="px-4 py-3">Vị trí</th><th className="px-4 py-3">Trạng thái</th><th className="px-4 py-3">Lương</th><th className="px-4 py-3">Hạn nộp</th><th className="px-4 py-3 text-right">Thao tác</th></tr></thead>
                <tbody className="divide-y divide-border-subtle">
                  {jobs.map((job) => <tr key={job.id} className="hover:bg-surface-low">
                    <td className="px-4 py-4"><button type="button" onClick={() => setDetailsId(job.id)} className="text-left"><span className="block font-semibold text-navy hover:text-gold">{job.title}</span><span className="mt-1 block text-label text-ink-muted">{job.locationName ?? "Chưa có địa điểm"} · {job.viewCount} lượt xem</span></button></td>
                    <td className="px-4 py-4"><div className="flex flex-wrap gap-2"><ApprovalBadge status={job.approvalStatus} /><Badge variant={job.isActive ? "navy" : "neutral"}>{job.isActive ? "Đang mở" : "Đã đóng"}</Badge></div></td>
                    <td className="px-4 py-4 text-label font-medium tabular-nums text-ink">{formatSalary(job)}</td>
                    <td className="px-4 py-4 text-label tabular-nums text-ink-variant">{job.deadline ? new Date(job.deadline).toLocaleDateString("vi-VN") : "Không giới hạn"}</td>
                    <td className="px-4 py-4"><JobActions job={job} busy={toggleJob.isPending || deleteJob.isPending} onView={() => setDetailsId(job.id)} onEdit={() => setEditId(job.id)} onToggle={() => void handleToggle(job)} onDelete={() => setDeleteTarget(job)} /></td>
                  </tr>)}
                </tbody>
              </table>
            </div>

            <div className="grid gap-4 lg:hidden">
              {jobs.map((job) => <article key={job.id} className="rounded-default border border-border-subtle bg-surface p-4 shadow-surface">
                <div className="flex flex-wrap gap-2"><ApprovalBadge status={job.approvalStatus} /><Badge variant={job.isActive ? "navy" : "neutral"}>{job.isActive ? "Đang mở" : "Đã đóng"}</Badge></div>
                <button type="button" onClick={() => setDetailsId(job.id)} className="mt-3 text-left text-body-lg font-semibold text-navy">{job.title}</button>
                <dl className="mt-3 grid grid-cols-2 gap-3 text-label"><div><dt className="text-ink-muted">Địa điểm</dt><dd className="mt-1 text-ink">{job.locationName ?? "Chưa cập nhật"}</dd></div><div><dt className="text-ink-muted">Mức lương</dt><dd className="mt-1 break-words text-ink">{formatSalary(job)}</dd></div></dl>
                <div className="mt-4 border-t border-border-subtle pt-3"><JobActions job={job} busy={toggleJob.isPending || deleteJob.isPending} onView={() => setDetailsId(job.id)} onEdit={() => setEditId(job.id)} onToggle={() => void handleToggle(job)} onDelete={() => setDeleteTarget(job)} /></div>
              </article>)}
            </div>

            <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><p className="text-label text-ink-muted">{jobsQuery.data?.totalCount ?? 0} tin · Trang {jobsQuery.data?.pageIndex ?? 1}/{Math.max(jobsQuery.data?.totalPages ?? 1, 1)}</p><div className="flex gap-2"><Button variant="secondary" size="sm" disabled={!jobsQuery.data?.hasPreviousPage} onClick={() => setFilters((current) => ({ ...current, pageIndex: Math.max(1, (current.pageIndex ?? 1) - 1) }))}><IconChevronLeft size={17} aria-hidden="true" />Trước</Button><Button variant="secondary" size="sm" disabled={!jobsQuery.data?.hasNextPage} onClick={() => setFilters((current) => ({ ...current, pageIndex: (current.pageIndex ?? 1) + 1 }))}>Sau<IconChevronRight size={17} aria-hidden="true" /></Button></div></div>
          </>
        )}
      </QueryBoundary>

      <JobFormModal open={createOpen} onClose={() => setCreateOpen(false)} />
      <JobDetailsModal jobId={detailsId} onClose={() => setDetailsId(null)} onEdit={() => { setEditId(detailsId); setDetailsId(null); }} />
      {editJobQuery.data && <JobFormModal open={Boolean(editId)} onClose={() => setEditId(null)} job={editJobQuery.data} />}

      <Modal
        open={Boolean(deleteTarget)}
        onClose={() => {
          if (!deleteJob.isPending) setDeleteTarget(null);
        }}
        title="Xác nhận xóa tin tuyển dụng"
        footer={
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => setDeleteTarget(null)}
              disabled={deleteJob.isPending}
            >
              Hủy
            </Button>
            <Button
              variant="danger"
              onClick={() => void handleConfirmDelete()}
              disabled={deleteJob.isPending}
            >
              {deleteJob.isPending ? "Đang xóa..." : "Xác nhận xóa"}
            </Button>
          </div>
        }
      >
        <div className="flex items-start gap-3.5">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-danger/10 text-danger">
            <IconAlertTriangle size={22} aria-hidden="true" />
          </div>
          <div>
            <p className="text-body text-ink">
              Bạn có chắc chắn muốn xóa tin tuyển dụng{" "}
              <strong className="font-semibold text-navy">“{deleteTarget?.title}”</strong> không?
            </p>
            <p className="mt-1 text-label text-ink-muted">
              Thao tác này không thể hoàn tác. Mọi thông tin ứng tuyển của tin này có thể bị ảnh hưởng.
            </p>
          </div>
        </div>
      </Modal>
    </section>
  );
}

function JobActions({ job, busy, onView, onEdit, onToggle, onDelete }: { job: JobSummary; busy: boolean; onView: () => void; onEdit: () => void; onToggle: () => void; onDelete: () => void }) {
  return <div className="flex justify-end gap-1"><button type="button" aria-label={`Xem ${job.title}`} onClick={onView} className="flex h-10 w-10 items-center justify-center rounded-default text-navy hover:bg-navy/10"><IconEye size={18} aria-hidden="true" /></button><button type="button" aria-label={`Sửa ${job.title}`} onClick={onEdit} className="flex h-10 w-10 items-center justify-center rounded-default text-navy hover:bg-navy/10"><IconEdit size={18} aria-hidden="true" /></button><button type="button" aria-label={job.isActive ? `Đóng ${job.title}` : `Mở ${job.title}`} onClick={onToggle} disabled={busy} className="flex h-10 w-10 items-center justify-center rounded-default text-warning hover:bg-warning/10 disabled:opacity-50"><IconPower size={18} aria-hidden="true" /></button><button type="button" aria-label={`Xóa ${job.title}`} onClick={onDelete} disabled={busy} className="flex h-10 w-10 items-center justify-center rounded-default text-danger hover:bg-danger/10 disabled:opacity-50"><IconTrash size={18} aria-hidden="true" /></button></div>;
}

function JobsSkeleton() {
  return <div className="space-y-3 rounded-default border border-border-subtle bg-surface p-4">{Array.from({ length: 5 }).map((_, index) => <div key={index} className="grid grid-cols-[2fr_1fr_1fr] gap-4 border-b border-border-subtle py-3 last:border-0"><Skeleton className="h-6" /><Skeleton className="h-6" /><Skeleton className="h-6" /></div>)}</div>;
}
