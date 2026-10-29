import type { ReactNode } from "react";
import { Link } from "react-router";
import { IconArrowRight, IconBriefcase, IconBuilding, IconCircleCheck, IconClock, IconPower } from "@tabler/icons-react";
import { buttonVariants, Card, CardContent, Skeleton } from "~/components/ui";
import { QueryBoundary } from "~/components/shared/QueryBoundary";
import { cn } from "~/lib/cn";
import { useAuthStore } from "~/stores/useAuthStore";
import { useCompanyProfile } from "~/features/hr/hooks/useCompanyProfile";
import { useEmployerJobs } from "~/features/hr/hooks/useEmployerJobs";

export default function Page() {
  const user = useAuthStore((state) => state.user);
  const companyQuery = useCompanyProfile();
  const allJobs = useEmployerJobs({ pageIndex: 1, pageSize: 1 });
  const activeJobs = useEmployerJobs({ isActive: true, pageIndex: 1, pageSize: 1 });
  const pendingJobs = useEmployerJobs({ approvalStatus: "Pending", pageIndex: 1, pageSize: 1 });
  const approvedJobs = useEmployerJobs({ approvalStatus: "Approved", pageIndex: 1, pageSize: 1 });
  const queries = [allJobs, activeJobs, pendingJobs, approvedJobs];
  const firstError = queries.find((query) => query.error)?.error;

  return (
    <section aria-labelledby="dashboard-title">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-label font-semibold text-gold">TỔNG QUAN</p>
          <h1 id="dashboard-title" className="mt-1 text-headline text-navy">Xin chào, {user?.fullName || "Nhà tuyển dụng"}</h1>
          <p className="mt-2 text-ink-variant">Theo dõi tin tuyển dụng và hoàn thiện thông tin doanh nghiệp.</p>
        </div>
        <Link to="/hr/jobs" className={cn(buttonVariants({ variant: "primary", size: "md" }), "w-full sm:w-auto")}>Quản lý tin tuyển dụng<IconArrowRight size={18} aria-hidden="true" /></Link>
      </div>

      <QueryBoundary isLoading={queries.some((query) => query.isLoading)} error={firstError} onRetry={() => void Promise.all(queries.map((query) => query.refetch()))} skeleton={<div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }).map((_, index) => <Skeleton key={index} className="h-32" />)}</div>}>
        <div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Tổng tin tuyển dụng" value={allJobs.data?.totalCount ?? 0} icon={<IconBriefcase size={22} aria-hidden="true" />} />
          <StatCard label="Tin đang mở" value={activeJobs.data?.totalCount ?? 0} icon={<IconPower size={22} aria-hidden="true" />} />
          <StatCard label="Tin chờ duyệt" value={pendingJobs.data?.totalCount ?? 0} icon={<IconClock size={22} aria-hidden="true" />} />
          <StatCard label="Tin đã duyệt" value={approvedJobs.data?.totalCount ?? 0} icon={<IconCircleCheck size={22} aria-hidden="true" />} />
        </div>
      </QueryBoundary>

      <div className="mt-7 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <QueryBoundary
          isLoading={companyQuery.isLoading}
          error={companyQuery.error}
          onRetry={() => companyQuery.refetch()}
          skeleton={<Skeleton className="h-48" />}
        >
          <Card><CardContent className="p-6"><p className="text-label font-semibold text-gold">HỒ SƠ DOANH NGHIỆP</p><div className="mt-4 flex items-start gap-4"><div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-default bg-navy/10 text-navy">{companyQuery.data?.logoUrl ? <img src={companyQuery.data.logoUrl} alt={`Logo ${companyQuery.data.name}`} className="h-full w-full object-cover" /> : <IconBuilding size={25} aria-hidden="true" />}</div><div className="min-w-0"><h2 className="text-body-lg font-semibold text-navy">{companyQuery.data?.name ?? "Chưa có hồ sơ công ty"}</h2><p className="mt-1 text-label text-ink-muted">{companyQuery.data ? `${companyQuery.data.industry ?? "Chưa cập nhật ngành nghề"} · ${companyQuery.data.verifiedStatus === "Verified" ? "Đã xác minh" : "Chưa xác minh"}` : "Tạo hồ sơ công ty trước khi quản lý thông tin doanh nghiệp."}</p><Link to="/hr/company" className="mt-4 inline-flex items-center gap-2 text-label font-semibold text-navy hover:text-gold">{companyQuery.data ? "Cập nhật hồ sơ" : "Tạo hồ sơ công ty"}<IconArrowRight size={17} aria-hidden="true" /></Link></div></div></CardContent></Card>
        </QueryBoundary>
        <Card><CardContent className="p-6"><p className="text-label font-semibold text-gold">ỨNG TUYỂN VÀ QUY TRÌNH</p><h2 className="mt-4 text-body-lg font-semibold text-navy">Quản lý ứng viên theo từng tin tuyển dụng</h2><p className="mt-2 text-label text-ink-variant">Xem hồ sơ ứng viên và theo dõi cập nhật trạng thái tuyển dụng theo quy trình.</p><Link to="/hr/pipeline" className="mt-4 inline-flex items-center gap-2 text-label font-semibold text-navy hover:text-gold">Mở quy trình tuyển dụng<IconArrowRight size={17} aria-hidden="true" /></Link></CardContent></Card>
      </div>
    </section>
  );
}

function StatCard({ label, value, icon }: { label: string; value: number; icon: ReactNode }) {
  return <Card><CardContent className="p-5"><div className="flex items-center justify-between"><p className="text-label font-medium text-ink-muted">{label}</p><span className="flex h-10 w-10 items-center justify-center rounded-default bg-navy/10 text-navy">{icon}</span></div><p className="mt-4 text-headline tabular-nums text-navy">{new Intl.NumberFormat("vi-VN").format(value)}</p></CardContent></Card>;
}
