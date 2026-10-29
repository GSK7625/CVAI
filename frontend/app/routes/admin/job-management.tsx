import { useState } from "react";
import { IconSearch, IconCheck, IconX, IconEye } from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader } from "~/components/ui/Card";
import { Badge } from "~/components/ui/Badge";
import { Table, THead, TBody, TR, TH, TD } from "~/components/ui/Table";
import { Input } from "~/components/ui/Input";
import { Button } from "~/components/ui/Button";
import { Modal } from "~/components/ui/Modal";
import { adminService } from "~/features/admin/services/adminService";
import type { JobListResponse } from "~/features/admin/types";

export default function JobManagementPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [pageIndex, setPageIndex] = useState(1);
  const [moderateModalOpen, setModerateModalOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState<JobListResponse | null>(null);
  const [moderateAction, setModerateAction] = useState<"approve" | "reject">("approve");
  const [moderateNote, setModerateNote] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-jobs", searchQuery, selectedStatus, pageIndex],
    queryFn: () =>
      adminService().getJobs({
        search: searchQuery || undefined,
        approvalStatus: selectedStatus === "all" ? undefined : selectedStatus,
        pageIndex,
        pageSize: 10,
      }),
  });

  const moderateMutation = useMutation({
    mutationFn: (params: { jobId: string; isApproved: boolean; note?: string }) =>
      adminService().moderateJob(params.jobId, {
        isApproved: params.isApproved,
        rejectionReason: params.isApproved ? undefined : params.note,
        note: params.isApproved ? params.note : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-jobs"] });
      setModerateModalOpen(false);
      setModerateNote("");
      setSelectedJob(null);
    },
  });

  const handleModerate = (job: JobListResponse, action: "approve" | "reject") => {
    setSelectedJob(job);
    setModerateAction(action);
    setModerateModalOpen(true);
  };

  const confirmModerate = () => {
    if (!selectedJob) return;
    moderateMutation.mutate({
      jobId: selectedJob.id,
      isApproved: moderateAction === "approve",
      note: moderateNote || undefined,
    });
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: "success" | "gold" | "danger" | "neutral"; label: string }> = {
      Active: { variant: "success", label: "Đang tuyển" },
      Pending: { variant: "gold", label: "Chờ duyệt" },
      Rejected: { variant: "danger", label: "Từ chối" },
      Closed: { variant: "neutral", label: "Đã đóng" },
      Draft: { variant: "neutral", label: "Nháp" },
    };
    const { variant, label } = config[status] || { variant: "neutral" as const, label: status };
    return <Badge variant={variant}>{label}</Badge>;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("vi-VN");
  };

  const formatSalary = (min: number | null | undefined, max: number | null | undefined, currency: string | null | undefined) => {
    if (!min && !max) return "Thỏa thuận";
    const curr = currency || "VND";
    if (min && max) {
      return `${min.toLocaleString()} - ${max.toLocaleString()} ${curr}`;
    }
    if (min) return `Từ ${min.toLocaleString()} ${curr}`;
    if (max) return `Đến ${max.toLocaleString()} ${curr}`;
    return "Thỏa thuận";
  };

  if (error) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <p className="text-body-lg font-semibold text-danger">Lỗi tải dữ liệu</p>
          <p className="mt-2 text-body-sm text-ink-muted">
            {error instanceof Error ? error.message : "Đã xảy ra lỗi"}
          </p>
        </div>
      </div>
    );
  }

  const jobs = data?.items || [];
  const totalCount = data?.totalCount || 0;
  const totalPages = data?.totalPages || 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-headline-xl font-bold text-ink">Quản lý tin tuyển dụng</h1>
          <p className="mt-2 text-body-md text-ink-muted">
            Duyệt và quản lý các tin tuyển dụng trên hệ thống
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="relative flex-1 md:max-w-md">
              <IconSearch
                size={20}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"
              />
              <Input
                type="text"
                placeholder="Tìm kiếm theo tiêu đề công việc..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedStatus("all")}
                className={`rounded-full px-4 py-2 text-label-sm font-semibold transition-colors ${
                  selectedStatus === "all"
                    ? "bg-navy text-white"
                    : "bg-surface-high text-ink-muted hover:bg-surface-low"
                }`}
              >
                Tất cả
              </button>
              <button
                onClick={() => setSelectedStatus("Pending")}
                className={`rounded-full px-4 py-2 text-label-sm font-semibold transition-colors ${
                  selectedStatus === "Pending"
                    ? "bg-navy text-white"
                    : "bg-surface-high text-ink-muted hover:bg-surface-low"
                }`}
              >
                Chờ duyệt
              </button>
              <button
                onClick={() => setSelectedStatus("Approved")}
                className={`rounded-full px-4 py-2 text-label-sm font-semibold transition-colors ${
                  selectedStatus === "Approved"
                    ? "bg-navy text-white"
                    : "bg-surface-high text-ink-muted hover:bg-surface-low"
                }`}
              >
                Đang tuyển
              </button>
              <button
                onClick={() => setSelectedStatus("Rejected")}
                className={`rounded-full px-4 py-2 text-label-sm font-semibold transition-colors ${
                  selectedStatus === "Rejected"
                    ? "bg-navy text-white"
                    : "bg-surface-high text-ink-muted hover:bg-surface-low"
                }`}
              >
                Từ chối
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="py-12 text-center">
              <p className="text-body-md text-ink-muted">Đang tải dữ liệu...</p>
            </div>
          ) : (
            <>
              <Table className="border-0 shadow-none">
                <THead>
                  <TR>
                    <TH>Công việc</TH>
                    <TH>Công ty</TH>
                    <TH>Mức lương</TH>
                    <TH>Trạng thái</TH>
                    <TH>Ngày đăng</TH>
                    <TH className="text-right">Thao tác</TH>
                  </TR>
                </THead>
                <TBody>
                  {jobs.map((job) => (
                    <TR key={job.id}>
                      <TD>
                        <div>
                          <p className="font-medium text-ink">{job.title}</p>
                          <p className="mt-1 text-label-sm text-ink-muted">
                            {job.locationName || "Chưa cập nhật"}
                          </p>
                        </div>
                      </TD>
                      <TD className="text-ink-muted">{job.companyName || "Chưa có"}</TD>
                      <TD className="text-ink-muted">
                        {formatSalary(job.salaryMin, job.salaryMax, job.salaryCurrency)}
                      </TD>
                      <TD>{getStatusBadge(job.approvalStatus)}</TD>
                      <TD className="text-ink-muted">{formatDate(job.createdAt)}</TD>
                      <TD>
                        <div className="flex items-center justify-end gap-2">
                          {job.approvalStatus === "Pending" && (
                            <>
                              <button
                                onClick={() => handleModerate(job, "approve")}
                                disabled={moderateMutation.isPending}
                                className="rounded-default p-2 text-ink-muted transition-colors hover:bg-surface-low hover:text-success disabled:opacity-50"
                                title="Duyệt tin"
                              >
                                <IconCheck size={18} />
                              </button>
                              <button
                                onClick={() => handleModerate(job, "reject")}
                                disabled={moderateMutation.isPending}
                                className="rounded-default p-2 text-ink-muted transition-colors hover:bg-surface-low hover:text-danger disabled:opacity-50"
                                title="Từ chối tin"
                              >
                                <IconX size={18} />
                              </button>
                            </>
                          )}
                          <button
                            className="rounded-default p-2 text-ink-muted transition-colors hover:bg-surface-low hover:text-ink"
                            title="Xem chi tiết"
                          >
                            <IconEye size={18} />
                          </button>
                        </div>
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
              {jobs.length === 0 && (
                <div className="py-12 text-center">
                  <p className="text-body-md text-ink-muted">Không tìm thấy tin tuyển dụng nào</p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between text-body-sm text-ink-muted">
        <p>
          Hiển thị {jobs.length} trong tổng số {totalCount} tin tuyển dụng
        </p>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPageIndex((p) => Math.max(1, p - 1))}
            disabled={pageIndex === 1 || isLoading}
          >
            Trang trước
          </Button>
          <span className="flex items-center px-3 text-body-sm font-medium">
            {pageIndex} / {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPageIndex((p) => Math.min(totalPages, p + 1))}
            disabled={pageIndex === totalPages || isLoading}
          >
            Trang sau
          </Button>
        </div>
      </div>

      <Modal
        open={moderateModalOpen}
        onClose={() => setModerateModalOpen(false)}
        title={moderateAction === "approve" ? "Duyệt tin tuyển dụng" : "Từ chối tin tuyển dụng"}
      >
        <div className="space-y-4">
          <p className="text-body-md text-ink-muted">
            Bạn có chắc chắn muốn{" "}
            {moderateAction === "approve" ? "duyệt" : "từ chối"} tin tuyển dụng{" "}
            <strong>{selectedJob?.title}</strong>?
          </p>
          <div>
            <label htmlFor="moderateNote" className="mb-2 block text-label-sm font-semibold text-ink">
              Ghi chú {moderateAction === "reject" && <span className="text-danger">*</span>}
            </label>
            <textarea
              id="moderateNote"
              value={moderateNote}
              onChange={(e) => setModerateNote(e.target.value)}
              placeholder={
                moderateAction === "approve"
                  ? "Nhập ghi chú (tùy chọn)..."
                  : "Nhập lý do từ chối..."
              }
              className="min-h-24 w-full rounded-default border border-stroke bg-white px-3 py-2 text-body-md text-ink transition-colors focus:border-navy focus:outline-none focus:ring-2 focus:ring-navy/20"
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              size="md"
              onClick={() => setModerateModalOpen(false)}
              disabled={moderateMutation.isPending}
            >
              Hủy
            </Button>
            <Button
              variant={moderateAction === "approve" ? "primary" : "danger"}
              size="md"
              onClick={confirmModerate}
              disabled={
                (moderateAction === "reject" && !moderateNote.trim()) ||
                moderateMutation.isPending
              }
            >
              {moderateMutation.isPending
                ? "Đang xử lý..."
                : moderateAction === "approve"
                  ? "Xác nhận duyệt"
                  : "Xác nhận từ chối"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
