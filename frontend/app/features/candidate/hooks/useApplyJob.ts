/**
 * @file useApplyJob.ts
 * @description Hook nộp hồ sơ ứng tuyển vị trí việc làm (FC-81a, P3-UC01).
 * @architecture Gửi request POST /api/candidate/jobs/{jobId}/apply với { cvId, coverLetter },
 * tự động invalidate danh sách ứng tuyển sau khi nộp thành công.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { jobService } from "../services/jobService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";
import { useUIStore } from "~/stores/useUIStore";
import type { ApplyJobRequest, ApplyJobResponse } from "../types";

export function useApplyJob(jobId: string) {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation<ApplyJobResponse, Error, ApplyJobRequest>({
    mutationKey: ["apply-job", jobId],
    mutationFn: (req: ApplyJobRequest) => jobService().apply(jobId, req),
    onSuccess: async () => {
      showToast("Đã gửi hồ sơ ứng tuyển thành công!", "success");
      await queryClient.invalidateQueries({
        queryKey: candidateQueryKeys.applications.all,
      });
    },
  });
}
