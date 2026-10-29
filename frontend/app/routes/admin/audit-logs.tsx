import { useState } from "react";
import { IconSearch, IconFilter } from "@tabler/icons-react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader } from "~/components/ui/Card";
import { Badge } from "~/components/ui/Badge";
import { Table, THead, TBody, TR, TH, TD } from "~/components/ui/Table";
import { Input } from "~/components/ui/Input";
import { Button } from "~/components/ui/Button";
import { adminService } from "~/features/admin/services/adminService";

export default function AuditLogsPage() {
  const [searchAction, setSearchAction] = useState("");
  const [pageIndex, setPageIndex] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-audit-logs", searchAction, pageIndex],
    queryFn: () =>
      adminService().getAuditLogs({
        action: searchAction || undefined,
        pageIndex,
        pageSize: 20,
      }),
  });

  const getActionBadge = (action: string) => {
    const config: Record<string, { variant: "success" | "navy" | "gold" | "danger" | "neutral"; label: string }> = {
      "User.Created": { variant: "success", label: "Tạo người dùng" },
      "User.Updated": { variant: "navy", label: "Cập nhật người dùng" },
      "User.Locked": { variant: "danger", label: "Khóa người dùng" },
      "User.Unlocked": { variant: "success", label: "Mở khóa người dùng" },
      "Company.StatusChanged": { variant: "gold", label: "Đổi trạng thái công ty" },
      "Job.Approved": { variant: "success", label: "Duyệt tin tuyển dụng" },
      "Job.Rejected": { variant: "danger", label: "Từ chối tin tuyển dụng" },
      "Admin.Login": { variant: "navy", label: "Đăng nhập Admin" },
    };
    const { variant, label } = config[action] || { variant: "neutral" as const, label: action };
    return <Badge variant={variant}>{label}</Badge>;
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("vi-VN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const parsePayload = (payloadJson: string | null) => {
    if (!payloadJson) return null;
    try {
      return JSON.parse(payloadJson);
    } catch {
      return null;
    }
  };

  const renderPayloadSummary = (payloadJson: string | null) => {
    const payload = parsePayload(payloadJson);
    if (!payload) return <span className="text-ink-muted">—</span>;

    const entries = Object.entries(payload).slice(0, 2);
    return (
      <div className="text-label-sm">
        {entries.map(([key, value]) => (
          <div key={key} className="text-ink-muted">
            <span className="font-medium">{key}:</span>{" "}
            {String(value).length > 30 ? String(value).substring(0, 30) + "..." : String(value)}
          </div>
        ))}
      </div>
    );
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

  const logs = data?.items || [];
  const totalCount = data?.totalCount || 0;
  const totalPages = data?.totalPages || 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-headline-xl font-bold text-ink">Nhật ký hoạt động</h1>
          <p className="mt-2 text-body-md text-ink-muted">
            Theo dõi các hoạt động quản trị trên hệ thống
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="relative flex-1 md:max-w-md">
              <IconFilter
                size={20}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"
              />
              <Input
                type="text"
                placeholder="Lọc theo hành động (vd: User.Created)..."
                value={searchAction}
                onChange={(e) => setSearchAction(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="text-body-sm text-ink-muted">
              Tổng số: <strong>{totalCount}</strong> bản ghi
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
                    <TH>Thời gian</TH>
                    <TH>Hành động</TH>
                    <TH>Người thực hiện</TH>
                    <TH>Đối tượng</TH>
                    <TH>Chi tiết</TH>
                    <TH>IP</TH>
                  </TR>
                </THead>
                <TBody>
                  {logs.map((log) => (
                    <TR key={log.id}>
                      <TD className="text-ink-muted">{formatDateTime(log.createdAt)}</TD>
                      <TD>{getActionBadge(log.action)}</TD>
                      <TD>
                        <span className="text-ink-muted">{log.userId || "Hệ thống"}</span>
                      </TD>
                      <TD>
                        {log.entityType && log.entityId ? (
                          <div className="text-label-sm">
                            <div className="font-medium text-ink">{log.entityType}</div>
                            <div className="text-ink-muted">{log.entityId.substring(0, 8)}...</div>
                          </div>
                        ) : (
                          <span className="text-ink-muted">—</span>
                        )}
                      </TD>
                      <TD>{renderPayloadSummary(log.payloadJson)}</TD>
                      <TD className="text-ink-muted">{log.ipAddress || "—"}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
              {logs.length === 0 && (
                <div className="py-12 text-center">
                  <p className="text-body-md text-ink-muted">Không tìm thấy nhật ký nào</p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between text-body-sm text-ink-muted">
        <p>
          Hiển thị {logs.length} trong tổng số {totalCount} bản ghi
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
    </div>
  );
}
