import { IconUsers, IconBriefcase, IconBuildingSkyscraper, IconFileText } from "@tabler/icons-react";
import { Card, CardContent, CardHeader } from "~/components/ui/Card";
import { Badge } from "~/components/ui/Badge";
import { useEffect, useState } from "react";
import { adminService } from "~/features/admin/services/adminService";
import type { AdminDashboardStatsResponse } from "~/features/admin/types";
import { toast } from "sonner";

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  trend?: string;
  trendUp?: boolean;
}

function StatCard({ icon, label, value, trend, trendUp }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex items-start gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-navy/10 text-navy">
          {icon}
        </div>
        <div className="flex-1">
          <p className="text-label-sm text-ink-muted">{label}</p>
          <p className="mt-1 text-headline-lg font-bold text-ink">{value}</p>
          {trend && (
            <p className={`mt-1 text-label-sm ${trendUp ? "text-success" : "text-danger"}`}>
              {trendUp ? "↑" : "↓"} {trend}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminDashboardStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminService().getDashboardStats();
        console.log("Dashboard stats received:", data);
        setStats(data);
      } catch (err: any) {
        const errorMsg = err?.message || "Không thể tải thống kê. Vui lòng thử lại.";
        setError(errorMsg);
        toast.error(errorMsg);
        console.error("Error fetching dashboard stats:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-navy/20 border-t-navy mx-auto" />
          <p className="text-body-md text-ink-muted">Đang tải dữ liệu...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <p className="text-body-md text-danger">{error || "Không có dữ liệu"}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 rounded-md bg-navy px-4 py-2 text-white hover:bg-navy/90"
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-headline-xl font-bold text-ink">Tổng quan hệ thống</h1>
        <p className="mt-2 text-body-md text-ink-muted">
          Theo dõi hoạt động và thống kê của nền tảng FutureCV
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<IconUsers size={24} />}
          label="Tổng người dùng"
          value={stats.users.totalUsers.toLocaleString()}
          trend={stats.users.newUsersLast30Days > 0 ? `+${stats.users.newUsersLast30Days} trong 30 ngày` : undefined}
          trendUp={stats.users.newUsersLast30Days > 0}
        />
        <StatCard
          icon={<IconBuildingSkyscraper size={24} />}
          label="Nhà tuyển dụng"
          value={stats.users.totalEmployers.toLocaleString()}
        />
        <StatCard
          icon={<IconBriefcase size={24} />}
          label="Việc làm đang hoạt động"
          value={stats.jobs.activeJobsCount.toLocaleString()}
        />
        <StatCard
          icon={<IconFileText size={24} />}
          label="Ứng viên"
          value={stats.users.totalCandidates.toLocaleString()}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-headline-md font-semibold text-ink">Thống kê công ty</h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <span className="text-body-md text-ink-muted">Tổng công ty</span>
                <span className="text-headline-sm font-semibold text-ink">{stats.companies.totalCompanies}</span>
              </div>
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <span className="text-body-md text-ink-muted">Đã xác minh</span>
                <Badge variant="success" shape="pill">
                  {stats.companies.verifiedCompaniesCount}
                </Badge>
              </div>
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <span className="text-body-md text-ink-muted">Chờ xác minh</span>
                <Badge variant="gold" shape="pill">
                  {stats.companies.pendingVerificationCount}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-body-md text-ink-muted">Đã từ chối</span>
                <Badge variant="danger" shape="pill">
                  {stats.companies.rejectedCompaniesCount}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-headline-md font-semibold text-ink">Thống kê tin tuyển dụng</h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <span className="text-body-md text-ink-muted">Tổng tin đăng</span>
                <span className="text-headline-sm font-semibold text-ink">{stats.jobs.totalJobs}</span>
              </div>
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <span className="text-body-md text-ink-muted">Đang hoạt động</span>
                <Badge variant="success" shape="pill">
                  {stats.jobs.activeJobsCount}
                </Badge>
              </div>
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <span className="text-body-md text-ink-muted">Chờ duyệt</span>
                <Badge variant="gold" shape="pill">
                  {stats.jobs.pendingApprovalCount}
                </Badge>
              </div>
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <span className="text-body-md text-ink-muted">Đã từ chối</span>
                <Badge variant="danger" shape="pill">
                  {stats.jobs.rejectedJobsCount}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-body-md text-ink-muted">Hết hạn</span>
                <Badge variant="neutral" shape="pill">
                  {stats.jobs.expiredJobsCount}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-headline-md font-semibold text-ink">Thống kê ứng tuyển</h2>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-default border border-border-subtle bg-surface-low p-4">
              <p className="text-label-sm text-ink-muted">Tổng ứng tuyển</p>
              <p className="mt-2 text-headline-lg font-bold text-ink">{stats.applications.totalApplications.toLocaleString()}</p>
            </div>
            <div className="rounded-default border border-border-subtle bg-surface-low p-4">
              <p className="text-label-sm text-ink-muted">Đã ứng tuyển</p>
              <p className="mt-2 text-headline-lg font-bold text-ink">{stats.applications.appliedCount.toLocaleString()}</p>
            </div>
            <div className="rounded-default border border-border-subtle bg-surface-low p-4">
              <p className="text-label-sm text-ink-muted">Đang sàng lọc</p>
              <p className="mt-2 text-headline-lg font-bold text-ink">{stats.applications.screeningCount.toLocaleString()}</p>
            </div>
            <div className="rounded-default border border-border-subtle bg-surface-low p-4">
              <p className="text-label-sm text-ink-muted">Phỏng vấn</p>
              <p className="mt-2 text-headline-lg font-bold text-ink">{stats.applications.interviewCount.toLocaleString()}</p>
            </div>
            <div className="rounded-default border border-border-subtle bg-surface-low p-4">
              <p className="text-label-sm text-ink-muted">Đã tuyển</p>
              <p className="mt-2 text-headline-lg font-bold text-success">{stats.applications.hiredCount.toLocaleString()}</p>
            </div>
            <div className="rounded-default border border-border-subtle bg-surface-low p-4">
              <p className="text-label-sm text-ink-muted">Từ chối</p>
              <p className="mt-2 text-headline-lg font-bold text-danger">{stats.applications.rejectedCount.toLocaleString()}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {stats.monthlyTrends.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-headline-md font-semibold text-ink">Xu hướng theo tháng</h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.monthlyTrends.slice(0, 6).map((trend, index) => (
                <div key={index} className="border-b border-border-subtle pb-4 last:border-0 last:pb-0">
                  <div className="flex items-center justify-between">
                    <span className="text-body-md font-semibold text-ink">{trend.month}</span>
                    <div className="flex gap-3">
                      <Badge variant="navy" shape="pill">
                        {trend.newUsers} người dùng
                      </Badge>
                      <Badge variant="success" shape="pill">
                        {trend.newJobs} việc làm
                      </Badge>
                      <Badge variant="gold" shape="pill">
                        {trend.newApplications} ứng tuyển
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

