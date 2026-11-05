/** Explicit CV identity per request: selection changes never reuse an old query closure. */
import { useMutation } from "@tanstack/react-query";
import { jobService } from "../services/jobService";
import { previewMatchMutationOptions } from "./previewMatchMutation";

export function usePreviewJobMatch(jobId: string) {
  return useMutation(previewMatchMutationOptions(jobId, (job, cv) => jobService().previewMatch(job, cv)));
}
