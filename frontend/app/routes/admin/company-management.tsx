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
import type { CompanyProfileResponse } from "~/features/admin/types";

export default function CompanyManagementPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [pageIndex, setPageIndex] = useState(1);
  const [approveModalOpen, setApproveModalOpen] = useState(false);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<CompanyProfileResponse | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-companies", searchQuery, selectedStatus, pageIndex],
    queryFn: () =>
      adminService().getCompanies({
        search: searchQuery || undefined,
        status: selectedStatus === "all" ? undefined : selectedStatus,
        pageIndex,
        pageSize: 10,
      }),
  });

  const approveMutation = useMutation({
    mutationFn: (companyId: string) => adminService().approveCompany(companyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-companies"] });
      setApproveModalOpen(false);
      setSelectedCompany(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (params: { companyId: string; reason: string }) =>
      adminService().rejectCompany(params.companyId, params.reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-companies"] });
      setRejectModalOpen(false);
      setRejectReason("");
      setSelectedCompany(null);
    },
  });

  const handleApprove = (company: CompanyProfileResponse) => {
    setSelectedCompany(company);
    setApproveModalOpen(true);
  };

  const handleReject = (company: CompanyProfileResponse) => {
    setSelectedCompany(company);
    setRejectModalOpen(true);
  };

  const confirmApprove = () => {
    if (!selectedCompany) return;
    approveMutation.mutate(selectedCompany.id);
  };

  const confirmReject = () => {
    if (!selectedCompany || !rejectReason.trim()) return;
    rejectMutation.mutate({
      companyId: selectedCompany.id,
      reason: rejectReason,
    });
  };

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: "success" | "gold" | "danger"; label: string }> = {
      Verified: { variant: "success", label: "Đã xác thực" },
      Pending: { variant: "gold", label: "Chờ duyệt" },
      Rejected: { variant: "danger", label: "Từ chối" },
    };
    const { variant, label } = config[status] || { variant: "gold" as const, label: status };
    return <Badge variant={variant}>{label}</Badge>;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("vi-VN");
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

  const companies = data?.items || [];
  const totalCount = data?.totalCount || 0;
  const totalPages = data?.totalPages || 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-headline-xl font-bold text-ink">Quản lý công ty</h1>
          <p className="mt-2 text-body-md text-ink-muted">
            Xác thực và quản lý thông tin các công ty trên hệ thống
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
                placeholder="Tìm kiếm theo tên công ty..."
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
                onClick={() => setSelectedStatus("Verified")}
                className={`rounded-full px-4 py-2 text-label-sm font-semibold transition-colors ${
                  selectedStatus === "Verified"
                    ? "bg-navy text-white"
                    : "bg-surface-high text-ink-muted hover:bg-surface-low"
                }`}
              >
                Đã xác thực
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
                    <TH>Công ty</TH>
                    <TH>Email</TH>
                    <TH>Ngành</TH>
                    <TH>Trạng thái</TH>
                    <TH>Ngày tạo</TH>
                    <TH className="text-right">Thao tác</TH>
                  </TR>
                </THead>
                <TBody>
                  {companies.map((company) => (
                    <TR key={company.id}>
                      <TD>
                        <div className="flex items-center gap-3">
                          {company.logoUrl ? (
                            <img
                              src={company.logoUrl}
                              alt={company.companyName}
                              className="h-10 w-10 rounded-full object-cover"
                            />
                          ) : (
                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-navy/10 text-label-sm font-semibold text-navy">
                              {company.companyName?.charAt(0).toUpperCase() || "C"}
                            </div>
                          )}
                          <div>
                            <p className="font-medium text-ink">{company.companyName || "Chưa đặt tên"}</p>
                            {company.companySize && (
                              <p className="text-label-sm text-ink-muted">{company.companySize}</p>
                            )}
                          </div>
                        </div>
                      </TD>
                      <TD className="text-ink-muted">{company.email}</TD>
                      <TD className="text-ink-muted">{company.industry || "Chưa cập nhật"}</TD>
                      <TD>{getStatusBadge(company.status)}</TD>
                      <TD className="text-ink-muted">{formatDate(company.createdAt)}</TD>
                      <TD>
                        <div className="flex items-center justify-end gap-2">
                          {company.status === "Pending" && (
                            <>
                              <button
                                onClick={() => handleApprove(company)}
                                disabled={approveMutation.isPending || rejectMutation.isPending}
                                className="rounded-default p-2 text-ink-muted transition-colors hover:bg-surface-low hover:text-success disabled:opacity-50"
                                title="Duyệt công ty"
                              >
                                <IconCheck size={18} />
                              </button>
                              <button
                                onClick={() => handleReject(company)}
                                disabled={approveMutation.isPending || rejectMutation.isPending}
                                className="rounded-default p-2 text-ink-muted transition-colors hover:bg-surface-low hover:text-danger disabled:opacity-50"
                                title="Từ chối công ty"
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
              {companies.length === 0 && (
                <div className="py-12 text-center">
                  <p className="text-body-md text-ink-muted">Không tìm thấy công ty nào</p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between text-body-sm text-ink-muted">
        <p>
          Hiển thị {companies.length} trong tổng số {totalCount} công ty
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
        open={approveModalOpen}
        onClose={() => setApproveModalOpen(false)}
        title="Duyệt công ty"
      >
        <div className="space-y-4">
          <p className="text-body-md text-ink-muted">
            Bạn có chắc chắn muốn <strong className="text-success">duyệt</strong> công ty{" "}
            <strong>{selectedCompany?.companyName}</strong>?
          </p>
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              size="md"
              onClick={() => setApproveModalOpen(false)}
              disabled={approveMutation.isPending}
            >
              Hủy
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={confirmApprove}
              disabled={approveMutation.isPending}
            >
              {approveMutation.isPending ? "Đang xử lý..." : "Xác nhận"}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        open={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        title="Từ chối công ty"
      >
        <div className="space-y-4">
          <p className="text-body-md text-ink-muted">
            Bạn có chắc chắn muốn <strong className="text-danger">từ chối</strong> công ty{" "}
            <strong>{selectedCompany?.companyName}</strong>?
          </p>
          <div>
            <label htmlFor="rejectReason" className="mb-2 block text-label-sm font-semibold text-ink">
              Lý do từ chối <span className="text-danger">*</span>
            </label>
            <textarea
              id="rejectReason"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Nhập lý do từ chối..."
              className="min-h-24 w-full rounded-default border border-stroke bg-white px-3 py-2 text-body-md text-ink transition-colors focus:border-navy focus:outline-none focus:ring-2 focus:ring-navy/20"
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              size="md"
              onClick={() => setRejectModalOpen(false)}
              disabled={rejectMutation.isPending}
            >
              Hủy
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={confirmReject}
              disabled={!rejectReason.trim() || rejectMutation.isPending}
            >
              {rejectMutation.isPending ? "Đang xử lý..." : "Xác nhận"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
