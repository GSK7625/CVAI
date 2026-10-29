import { useState } from "react";
import { IconSearch, IconLock, IconLockOpen } from "@tabler/icons-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader } from "~/components/ui/Card";
import { Badge } from "~/components/ui/Badge";
import { Table, THead, TBody, TR, TH, TD } from "~/components/ui/Table";
import { Input } from "~/components/ui/Input";
import { Button } from "~/components/ui/Button";
import { Modal } from "~/components/ui/Modal";
import { adminService } from "~/features/admin/services/adminService";
import type { AdminUserResponse } from "~/features/admin/types";

export default function UserManagementPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRole, setSelectedRole] = useState<string>("all");
  const [pageIndex, setPageIndex] = useState(1);
  const [lockModalOpen, setLockModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUserResponse | null>(null);
  const [lockReason, setLockReason] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-users", searchQuery, selectedRole, pageIndex],
    queryFn: () =>
      adminService().getUsers({
        search: searchQuery || undefined,
        role: selectedRole === "all" ? undefined : selectedRole,
        pageIndex,
        pageSize: 10,
      }),
  });

  const lockMutation = useMutation({
    mutationFn: (params: { userId: string; reason: string }) =>
      adminService().lockUser(params.userId, { reason: params.reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setLockModalOpen(false);
      setLockReason("");
      setSelectedUser(null);
    },
  });

  const unlockMutation = useMutation({
    mutationFn: (userId: string) => adminService().unlockUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  const handleLockUser = (user: AdminUserResponse) => {
    setSelectedUser(user);
    setLockModalOpen(true);
  };

  const confirmLock = () => {
    if (!selectedUser || !lockReason.trim()) return;
    lockMutation.mutate({ userId: selectedUser.id, reason: lockReason });
  };

  const handleUnlockUser = (user: AdminUserResponse) => {
    if (confirm(`Bạn có chắc chắn muốn mở khóa tài khoản ${user.fullName || user.email}?`)) {
      unlockMutation.mutate(user.id);
    }
  };

  const getRoleBadge = (roles: string[]) => {
    if (roles.includes("Admin")) {
      return <Badge variant="danger">Admin</Badge>;
    }
    if (roles.includes("Employer")) {
      return <Badge variant="navy">Nhà tuyển dụng</Badge>;
    }
    if (roles.includes("Candidate")) {
      return <Badge variant="neutral">Ứng viên</Badge>;
    }
    return <Badge variant="neutral">Người dùng</Badge>;
  };

  const getStatusBadge = (isLockedOut: boolean, lockoutEnd: string | null) => {
    if (isLockedOut && lockoutEnd) {
      const isStillLocked = new Date(lockoutEnd) > new Date();
      if (isStillLocked) {
        return <Badge variant="danger">Bị khóa</Badge>;
      }
    }
    return <Badge variant="success">Hoạt động</Badge>;
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

  const users = data?.items || [];
  const totalCount = data?.totalCount || 0;
  const totalPages = data?.totalPages || 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-headline-xl font-bold text-ink">Quản lý người dùng</h1>
          <p className="mt-2 text-body-md text-ink-muted">
            Quản lý tài khoản và phân quyền người dùng trên hệ thống
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
                placeholder="Tìm kiếm theo tên hoặc email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedRole("all")}
                className={`rounded-full px-4 py-2 text-label-sm font-semibold transition-colors ${
                  selectedRole === "all"
                    ? "bg-navy text-white"
                    : "bg-surface-high text-ink-muted hover:bg-surface-low"
                }`}
              >
                Tất cả
              </button>
              <button
                onClick={() => setSelectedRole("Candidate")}
                className={`rounded-full px-4 py-2 text-label-sm font-semibold transition-colors ${
                  selectedRole === "Candidate"
                    ? "bg-navy text-white"
                    : "bg-surface-high text-ink-muted hover:bg-surface-low"
                }`}
              >
                Ứng viên
              </button>
              <button
                onClick={() => setSelectedRole("Employer")}
                className={`rounded-full px-4 py-2 text-label-sm font-semibold transition-colors ${
                  selectedRole === "Employer"
                    ? "bg-navy text-white"
                    : "bg-surface-high text-ink-muted hover:bg-surface-low"
                }`}
              >
                NTD
              </button>
              <button
                onClick={() => setSelectedRole("Admin")}
                className={`rounded-full px-4 py-2 text-label-sm font-semibold transition-colors ${
                  selectedRole === "Admin"
                    ? "bg-navy text-white"
                    : "bg-surface-high text-ink-muted hover:bg-surface-low"
                }`}
              >
                Admin
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
                    <TH>Người dùng</TH>
                    <TH>Email</TH>
                    <TH>Vai trò</TH>
                    <TH>Trạng thái</TH>
                    <TH>Ngày đăng ký</TH>
                    <TH className="text-right">Thao tác</TH>
                  </TR>
                </THead>
                <TBody>
                  {users.map((user) => (
                    <TR key={user.id}>
                      <TD>
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-navy/10 text-label-sm font-semibold text-navy">
                            {(user.fullName || user.email).charAt(0).toUpperCase()}
                          </div>
                          <span className="font-medium">{user.fullName || "Chưa cập nhật"}</span>
                        </div>
                      </TD>
                      <TD className="text-ink-muted">{user.email}</TD>
                      <TD>{getRoleBadge(user.roles)}</TD>
                      <TD>{getStatusBadge(user.isLockedOut, user.lockoutEnd)}</TD>
                      <TD className="text-ink-muted">{formatDate(user.createdAt)}</TD>
                      <TD>
                        <div className="flex items-center justify-end gap-2">
                          {user.isLockedOut && user.lockoutEnd && new Date(user.lockoutEnd) > new Date() ? (
                            <button
                              onClick={() => handleUnlockUser(user)}
                              disabled={unlockMutation.isPending}
                              className="rounded-default p-2 text-ink-muted transition-colors hover:bg-surface-low hover:text-success disabled:opacity-50"
                              title="Mở khóa tài khoản"
                            >
                              <IconLockOpen size={18} />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleLockUser(user)}
                              disabled={lockMutation.isPending}
                              className="rounded-default p-2 text-ink-muted transition-colors hover:bg-surface-low hover:text-danger disabled:opacity-50"
                              title="Khóa tài khoản"
                            >
                              <IconLock size={18} />
                            </button>
                          )}
                        </div>
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
              {users.length === 0 && (
                <div className="py-12 text-center">
                  <p className="text-body-md text-ink-muted">Không tìm thấy người dùng nào</p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between text-body-sm text-ink-muted">
        <p>
          Hiển thị {users.length} trong tổng số {totalCount} người dùng
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
        open={lockModalOpen}
        onClose={() => setLockModalOpen(false)}
        title="Khóa tài khoản"
      >
        <div className="space-y-4">
          <p className="text-body-md text-ink-muted">
            Bạn có chắc chắn muốn khóa tài khoản{" "}
            <strong>{selectedUser?.fullName || selectedUser?.email}</strong>?
          </p>
          <div>
            <label htmlFor="lockReason" className="mb-2 block text-label-sm font-semibold text-ink">
              Lý do khóa <span className="text-danger">*</span>
            </label>
            <textarea
              id="lockReason"
              value={lockReason}
              onChange={(e) => setLockReason(e.target.value)}
              placeholder="Nhập lý do khóa tài khoản..."
              className="min-h-24 w-full rounded-default border border-stroke bg-white px-3 py-2 text-body-md text-ink transition-colors focus:border-navy focus:outline-none focus:ring-2 focus:ring-navy/20"
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              size="md"
              onClick={() => setLockModalOpen(false)}
              disabled={lockMutation.isPending}
            >
              Hủy
            </Button>
            <Button
              variant="danger"
              size="md"
              onClick={confirmLock}
              disabled={!lockReason.trim() || lockMutation.isPending}
            >
              {lockMutation.isPending ? "Đang xử lý..." : "Xác nhận khóa"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
