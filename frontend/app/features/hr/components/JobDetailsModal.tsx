import { IconBriefcase, IconCalendar, IconMapPin, IconUsers } from "@tabler/icons-react";
import { Badge, Button, Modal, Skeleton } from "~/components/ui";
import { QueryBoundary } from "~/components/shared/QueryBoundary";
import { useEmployerJob } from "../hooks/useEmployerJobs";

export function JobDetailsModal({ jobId, onClose, onEdit }: { jobId: string | null; onClose: () => void; onEdit: () => void }) {
  const jobQuery = useEmployerJob(jobId);
  const job = jobQuery.data;
  return (
    <Modal open={Boolean(jobId)} onClose={onClose} title="Chi tiết tin tuyển dụng" className="max-h-[92dvh] max-w-3xl overflow-y-auto" footer={job ? <Button onClick={onEdit}>Chỉnh sửa</Button> : undefined}>
      <QueryBoundary isLoading={jobQuery.isLoading} error={jobQuery.error} onRetry={() => jobQuery.refetch()} skeleton={<div className="space-y-3"><Skeleton className="h-8 w-2/3" /><Skeleton className="h-4 w-full" /><Skeleton className="h-32 w-full" /></div>}>
        {job && (
          <article>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={job.approvalStatus === "Approved" ? "success" : job.approvalStatus === "Rejected" ? "danger" : "gold"}>{job.approvalStatus === "Approved" ? "Đã duyệt" : job.approvalStatus === "Rejected" ? "Bị từ chối" : "Chờ duyệt"}</Badge>
              <Badge variant={job.isActive ? "navy" : "neutral"}>{job.isActive ? "Đang mở" : "Đã đóng"}</Badge>
            </div>
            <h3 className="mt-4 text-headline-md text-navy">{job.title}</h3>
            <div className="mt-4 grid gap-3 text-label text-ink-variant sm:grid-cols-2">
              <span className="flex items-center gap-2"><IconMapPin size={18} aria-hidden="true" />{job.locationName ?? "Chưa cập nhật địa điểm"}</span>
              <span className="flex items-center gap-2"><IconBriefcase size={18} aria-hidden="true" />{job.employmentTypeName ?? "Chưa cập nhật loại hình"}</span>
              <span className="flex items-center gap-2"><IconUsers size={18} aria-hidden="true" />{job.positionsCount} vị trí</span>
              <span className="flex items-center gap-2"><IconCalendar size={18} aria-hidden="true" />{job.deadline ? new Date(job.deadline).toLocaleDateString("vi-VN") : "Không giới hạn hạn nộp"}</span>
            </div>
            <DetailSection title="Mô tả công việc" content={job.description} />
            <DetailSection title="Yêu cầu" content={job.requirements} />
            <DetailSection title="Quyền lợi" content={job.benefits} />
            {job.skills.length > 0 && <section className="mt-6"><h4 className="font-semibold text-navy">Kỹ năng</h4><div className="mt-3 flex flex-wrap gap-2">{job.skills.map((skill) => <Badge key={skill.skillId} variant={skill.isRequired ? "solidNavy" : "neutral"}>{skill.skillName} · {skill.isRequired ? "Bắt buộc" : "Ưu tiên"}</Badge>)}</div></section>}
          </article>
        )}
      </QueryBoundary>
    </Modal>
  );
}

function DetailSection({ title, content }: { title: string; content: string | null }) {
  if (!content) return null;
  return <section className="mt-6"><h4 className="font-semibold text-navy">{title}</h4><p className="mt-2 whitespace-pre-wrap text-ink-variant">{content}</p></section>;
}
