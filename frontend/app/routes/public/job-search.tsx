/**
 * @file job-search.tsx
 * @description Route công khai tìm kiếm danh sách việc làm (/jobs).
 * @architecture Thin Route Pattern (≤ 20 dòng): Ủy quyền toàn bộ UI cho JobListView.
 */

import { JobListView } from "~/features/candidate/components/job-list/JobListView";

export default function JobListPage() {
  return <JobListView />;
}
