import { useEffect, useMemo, useState } from "react";
import { IconColumns, IconGripVertical, IconList, IconSearch, IconUsers } from "@tabler/icons-react";
import { useQueryClient } from "@tanstack/react-query";
import { Avatar, Button, Card, CardContent, EmptyState, Input, Skeleton } from "~/components/ui";
import { QueryBoundary } from "~/components/shared/QueryBoundary";
import { useDebounce } from "~/hooks/useDebounce";
import { useEmployerJobs } from "../hooks/useEmployerJobs";
import {
  useRecruiterApplications,
  useRecruitmentPipeline,
  useUpdateApplicationStatus,
} from "../hooks/useRecruiterApplications";
import { hrQueryKeys } from "../queries/hrQueryKeys";
import type {
  ApplicationStatus,
  PipelineCandidate,
  RecruiterApplicationFilters,
  RecruitmentPipeline,
  UpdatableApplicationStatus,
} from "../types";
import { ApplicationDetailsModal } from "./ApplicationDetailsModal";
import { ApplicationStatusBadge, applicationStatusLabels, updatableApplicationStatuses } from "./ApplicationStatusBadge";

type ViewMode = "pipeline" | "list";

export function RecruitmentPipelinePage() {
  const jobsQuery = useEmployerJobs({ pageIndex: 1, pageSize: 100 });
  const [jobId, setJobId] = useState("");
  const [view, setView] = useState<ViewMode>("pipeline");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [filters, setFilters] = useState<RecruiterApplicationFilters>({ pageIndex: 1, pageSize: 10 });
  const [applicationId, setApplicationId] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId && jobsQuery.data?.items[0]) setJobId(jobsQuery.data.items[0].id);
  }, [jobId, jobsQuery.data]);

  const effectiveFilters = useMemo(() => ({ ...filters, keyword: debouncedSearch }), [filters, debouncedSearch]);
  const pipelineQuery = useRecruitmentPipeline(view === "pipeline" ? jobId : "");
  const applicationsQuery = useRecruiterApplications(view === "list" ? jobId : "", effectiveFilters);
  const jobs = jobsQuery.data?.items ?? [];

  return (
    <section aria-labelledby="pipeline-title">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-label font-semibold text-gold">ỨNG VIÊN</p><h1 id="pipeline-title" className="mt-1 text-headline text-navy">Quy trình tuyển dụng</h1><p className="mt-2 text-ink-variant">Theo dõi và cập nhật ứng viên theo từng tin tuyển dụng.</p></div><div className="flex rounded-default border border-border-strong bg-surface p-1"><ViewButton active={view === "pipeline"} onClick={() => setView("pipeline")} icon={<IconColumns size={18} aria-hidden="true" />}>Quy trình</ViewButton><ViewButton active={view === "list"} onClick={() => setView("list")} icon={<IconList size={18} aria-hidden="true" />}>Danh sách</ViewButton></div></div>

      <QueryBoundary isLoading={jobsQuery.isLoading} error={jobsQuery.error} onRetry={() => jobsQuery.refetch()} skeleton={<Skeleton className="mt-6 h-20" />}>
        {jobs.length === 0 ? <EmptyState className="mt-6" icon={<IconUsers size={42} aria-hidden="true" />} title="Chưa có tin tuyển dụng" description="Tạo tin tuyển dụng trước khi quản lý ứng viên." /> : <>
          <div className="mt-6 rounded-default border border-border-subtle bg-surface p-4 shadow-surface"><label htmlFor="pipeline-job" className="mb-2 block text-label font-semibold text-ink">Tin tuyển dụng</label><select id="pipeline-job" value={jobId} onChange={(event) => { setJobId(event.target.value); setFilters((current) => ({ ...current, pageIndex: 1 })); }} className="h-11 w-full rounded-default border border-border-strong bg-white px-3.5 text-ink focus:border-gold">{jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}</select></div>
          {view === "pipeline" ? <PipelineView jobId={jobId} query={pipelineQuery} onOpen={setApplicationId} /> : <ApplicationListView search={search} setSearch={(value) => { setSearch(value); setFilters((current) => ({ ...current, pageIndex: 1 })); }} filters={filters} setFilters={setFilters} query={applicationsQuery} onOpen={setApplicationId} />}
        </>}
      </QueryBoundary>
      <ApplicationDetailsModal applicationId={applicationId} onClose={() => setApplicationId(null)} />
    </section>
  );
}

function ViewButton({ active, onClick, icon, children }: { active: boolean; onClick: () => void; icon: React.ReactNode; children: React.ReactNode }) {
  return <button type="button" aria-pressed={active} onClick={onClick} className={active ? "flex min-h-11 items-center gap-2 rounded-default bg-navy px-3 py-2 text-label font-semibold text-white" : "flex min-h-11 items-center gap-2 rounded-default px-3 py-2 text-label font-semibold text-ink-variant hover:bg-surface-low"}>{icon}{children}</button>;
}

function PipelineView({
  jobId,
  query,
  onOpen,
}: {
  jobId: string;
  query: ReturnType<typeof useRecruitmentPipeline>;
  onOpen: (id: string) => void;
}) {
  const queryClient = useQueryClient();
  const updateStatus = useUpdateApplicationStatus();
  const [draggedItem, setDraggedItem] = useState<{
    applicationId: string;
    fromStage: UpdatableApplicationStatus;
    candidate: PipelineCandidate;
  } | null>(null);
  const [activeDropStage, setActiveDropStage] = useState<UpdatableApplicationStatus | null>(null);
  const [updatingApplicationId, setUpdatingApplicationId] = useState<string | null>(null);

  const handleDragStart = (
    e: React.DragEvent,
    candidate: PipelineCandidate,
    fromStage: UpdatableApplicationStatus,
  ) => {
    const payload = { applicationId: candidate.applicationId, fromStage };
    e.dataTransfer.setData("application/json", JSON.stringify(payload));
    e.dataTransfer.effectAllowed = "move";
    setDraggedItem({ applicationId: candidate.applicationId, fromStage, candidate });
  };

  const handleDragEnd = () => {
    setDraggedItem(null);
    setActiveDropStage(null);
  };

  const handleDrop = async (
    e: React.DragEvent,
    targetStage: UpdatableApplicationStatus,
  ) => {
    e.preventDefault();
    setActiveDropStage(null);

    let candidate = draggedItem?.candidate;
    let applicationId = draggedItem?.applicationId;
    let fromStage = draggedItem?.fromStage;

    if (!applicationId || !fromStage) {
      try {
        const raw = e.dataTransfer.getData("application/json");
        if (raw) {
          const parsed = JSON.parse(raw);
          applicationId = parsed.applicationId;
          fromStage = parsed.fromStage;
        }
      } catch {
        // Ignore JSON parse error
      }
    }

    setDraggedItem(null);

    if (!applicationId || !fromStage || fromStage === targetStage) {
      return;
    }

    const queryKey = hrQueryKeys.applications.pipeline(jobId);
    const previousData = queryClient.getQueryData<RecruitmentPipeline>(queryKey);

    if (previousData) {
      if (!candidate) {
        for (const st of previousData.stages) {
          const found = st.candidates.find((c) => c.applicationId === applicationId);
          if (found) {
            candidate = found;
            break;
          }
        }
      }

      if (candidate) {
        const movingCandidate = candidate;
        queryClient.setQueryData<RecruitmentPipeline>(queryKey, {
          ...previousData,
          stages: previousData.stages.map((st) => {
            if (st.stage === fromStage) {
              return {
                ...st,
                count: Math.max(0, st.count - 1),
                candidates: st.candidates.filter((c) => c.applicationId !== applicationId),
              };
            }
            if (st.stage === targetStage) {
              return {
                ...st,
                count: st.count + 1,
                candidates: [movingCandidate, ...st.candidates],
              };
            }
            return st;
          }),
        });
      }
    }

    setUpdatingApplicationId(applicationId);
    try {
      await updateStatus.mutateAsync({
        id: applicationId,
        input: { newStatus: targetStage, reason: null },
      });
    } catch {
      if (previousData) {
        queryClient.setQueryData(queryKey, previousData);
      }
    } finally {
      setUpdatingApplicationId(null);
    }
  };

  return (
    <QueryBoundary
      isLoading={query.isLoading}
      error={query.error}
      onRetry={() => query.refetch()}
      skeleton={
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-56" />
          ))}
        </div>
      }
    >
      {query.data && (
        <>
          <p className="mt-5 text-label text-ink-muted">
            {query.data.totalCandidates} ứng viên trong quy trình
          </p>
          <div className="mt-3 grid items-start gap-4 md:grid-cols-2 xl:grid-cols-3">
            {query.data.stages.map((stage) => {
              const isDropTarget =
                activeDropStage === stage.stage && draggedItem?.fromStage !== stage.stage;
              const isCurrentSource = draggedItem?.fromStage === stage.stage;

              return (
                <Card
                  key={stage.stage}
                  onDragOver={(e) => {
                    e.preventDefault();
                    if (draggedItem && draggedItem.fromStage !== stage.stage) {
                      e.dataTransfer.dropEffect = "move";
                    }
                  }}
                  onDragEnter={(e) => {
                    e.preventDefault();
                    if (draggedItem && draggedItem.fromStage !== stage.stage) {
                      setActiveDropStage(stage.stage);
                    }
                  }}
                  onDragLeave={(e) => {
                    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
                      setActiveDropStage((current) => (current === stage.stage ? null : current));
                    }
                  }}
                  onDrop={(e) => handleDrop(e, stage.stage)}
                  className={`transition-all duration-200 ${
                    isDropTarget
                      ? "border-gold ring-2 ring-gold/40 bg-gold/[0.04] shadow-md"
                      : isCurrentSource
                        ? "border-border-strong opacity-90"
                        : ""
                  }`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <h2 className="font-semibold text-navy">
                        {applicationStatusLabels[stage.stage]}
                      </h2>
                      <span
                        className={`rounded-full px-2.5 py-1 text-label-sm font-semibold transition-colors ${
                          isDropTarget
                            ? "bg-gold text-white"
                            : "bg-navy/10 text-navy"
                        }`}
                      >
                        {stage.count}
                      </span>
                    </div>
                    <div className="mt-4 min-h-[5.5rem] space-y-3">
                      {isDropTarget && (
                        <div className="flex items-center justify-center rounded-default border-2 border-dashed border-gold/70 bg-gold/10 p-3 text-center text-label-sm font-semibold text-gold animate-pulse">
                          Thả để chuyển sang {applicationStatusLabels[stage.stage]}
                        </div>
                      )}
                      {stage.candidates.length ? (
                        stage.candidates.map((candidate) => (
                          <PipelineCandidateCard
                            key={candidate.applicationId}
                            candidate={candidate}
                            isDragging={draggedItem?.applicationId === candidate.applicationId}
                            isUpdating={updatingApplicationId === candidate.applicationId}
                            onOpen={onOpen}
                            onDragStart={(e) => handleDragStart(e, candidate, stage.stage)}
                            onDragEnd={handleDragEnd}
                          />
                        ))
                      ) : (
                        !isDropTarget && (
                          <p className="rounded-default border border-dashed border-border-subtle p-4 text-center text-label text-ink-muted">
                            Chưa có ứng viên
                          </p>
                        )
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </QueryBoundary>
  );
}

function PipelineCandidateCard({
  candidate,
  isDragging,
  isUpdating,
  onOpen,
  onDragStart,
  onDragEnd,
}: {
  candidate: PipelineCandidate;
  isDragging: boolean;
  isUpdating: boolean;
  onOpen: (id: string) => void;
  onDragStart: (e: React.DragEvent) => void;
  onDragEnd: () => void;
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      draggable={!isUpdating}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onClick={() => {
        if (!isUpdating) onOpen(candidate.applicationId);
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (!isUpdating) onOpen(candidate.applicationId);
        }
      }}
      className={`group relative flex min-h-16 w-full cursor-grab items-start gap-3 rounded-default border bg-surface-low p-3 text-left transition-all select-none hover:border-gold hover:shadow-sm focus-visible:ring-2 focus-visible:ring-gold active:cursor-grabbing ${
        isDragging
          ? "opacity-30 scale-95 border-dashed border-gold"
          : isUpdating
            ? "opacity-50 pointer-events-none border-border-subtle"
            : "border-border-subtle"
      }`}
    >
      <Avatar src={candidate.candidateAvatarUrl ?? undefined} name={candidate.candidateFullName} />
      <span className="min-w-0 flex-1">
        <span className="block truncate font-semibold text-ink group-hover:text-navy">
          {candidate.candidateFullName}
        </span>
        <span className="mt-1 block text-label text-ink-muted">
          Ứng tuyển {new Date(candidate.appliedAt).toLocaleDateString("vi-VN")}
        </span>
      </span>
      <IconGripVertical
        size={16}
        className="text-ink-muted/40 transition-colors group-hover:text-gold shrink-0 self-center"
        aria-hidden="true"
      />
    </div>
  );
}

function ApplicationListView({ search, setSearch, filters, setFilters, query, onOpen }: { search: string; setSearch: (value: string) => void; filters: RecruiterApplicationFilters; setFilters: React.Dispatch<React.SetStateAction<RecruiterApplicationFilters>>; query: ReturnType<typeof useRecruiterApplications>; onOpen: (id: string) => void }) {
  const applications = query.data?.items ?? [];
  return <div className="mt-5"><div className="grid gap-3 rounded-default border border-border-subtle bg-surface p-4 md:grid-cols-[minmax(0,1fr)_14rem]"><Input aria-label="Tìm ứng viên" icon={<IconSearch size={18} aria-hidden="true" />} placeholder="Tên ứng viên" value={search} onChange={(event) => setSearch(event.target.value)} /><select aria-label="Lọc trạng thái" value={filters.status ?? ""} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value as ApplicationStatus | "", pageIndex: 1 }))} className="h-11 rounded-default border border-border-strong bg-white px-3.5"><option value="">Mọi trạng thái</option>{[...updatableApplicationStatuses, "Withdrawn" as const].map((status) => <option key={status} value={status}>{applicationStatusLabels[status]}</option>)}</select></div>    <QueryBoundary isLoading={query.isLoading} error={query.error} onRetry={() => query.refetch()} skeleton={<Skeleton className="mt-4 h-72" />}>
      {applications.length ? (
        <>
          <div className="mt-4 grid gap-3">
            {applications.map((application) => (
              <button
                key={application.id}
                type="button"
                onClick={() => onOpen(application.id)}
                className="grid min-h-20 w-full gap-3 rounded-default border border-border-subtle bg-surface p-4 text-left shadow-surface hover:border-gold sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
              >
                <span className="flex min-w-0 items-center gap-3">
                  <Avatar src={application.candidateAvatarUrl ?? undefined} name={application.candidateFullName} />
                  <span className="min-w-0">
                    <span className="block truncate font-semibold text-navy">{application.candidateFullName}</span>
                    <span className="block truncate text-label text-ink-muted">
                      {application.candidatePhone ?? application.cvTitle ?? "CV ứng tuyển"}
                    </span>
                  </span>
                </span>
                <ApplicationStatusBadge status={application.status} />
              </button>
            ))}
          </div>
          <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-label text-ink-muted">
              {query.data?.totalCount ?? 0} ứng viên · Trang {query.data?.pageIndex ?? 1}/{Math.max(query.data?.totalPages ?? 1, 1)}
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={!query.data?.hasPreviousPage}
                onClick={() => setFilters((current) => ({ ...current, pageIndex: Math.max(1, (current.pageIndex ?? 1) - 1) }))}
              >
                Trang trước
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={!query.data?.hasNextPage}
                onClick={() => setFilters((current) => ({ ...current, pageIndex: (current.pageIndex ?? 1) + 1 }))}
              >
                Trang sau
              </Button>
            </div>
          </div>
        </>
      ) : (
        <EmptyState
          className="mt-4"
          icon={<IconUsers size={40} aria-hidden="true" />}
          title="Chưa có ứng viên"
          description="Không tìm thấy ứng viên phù hợp với bộ lọc hiện tại."
        />
      )}
    </QueryBoundary></div>;
}
