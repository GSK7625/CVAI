import { Badge } from "~/components/ui";
import type { ApplicationStatus, UpdatableApplicationStatus } from "../types";

export const applicationStatusLabels: Record<ApplicationStatus, string> = {
  Applied: "Đã ứng tuyển",
  Screening: "Sàng lọc",
  Interview: "Phỏng vấn",
  Offer: "Đề nghị",
  Hired: "Đã tuyển",
  Rejected: "Từ chối",
  Withdrawn: "Đã rút",
};

export const updatableApplicationStatuses: UpdatableApplicationStatus[] = [
  "Applied",
  "Screening",
  "Interview",
  "Offer",
  "Hired",
  "Rejected",
];

export function ApplicationStatusBadge({ status }: { status: ApplicationStatus }) {
  const variant = status === "Hired" ? "success" : status === "Rejected" || status === "Withdrawn" ? "danger" : status === "Offer" ? "gold" : "navy";
  return <Badge variant={variant}>{applicationStatusLabels[status]}</Badge>;
}
