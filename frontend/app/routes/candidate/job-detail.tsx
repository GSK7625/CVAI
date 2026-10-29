/**
 * @file job-detail.tsx
 * @description Route xem chi tiết việc làm ứng viên.
 * @architecture Thin Route Pattern (≤ 20 dòng): Ủy quyền toàn bộ UI cho JobDetailView.
 */

import { useParams } from "react-router";
import { JobDetailView } from "~/features/candidate/components/job-detail/JobDetailView";

export default function JobDetailPage() {
  const { jobId = "" } = useParams();
  return <JobDetailView jobId={jobId} />;
}
