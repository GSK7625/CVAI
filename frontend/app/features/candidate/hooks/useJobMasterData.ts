/**
 * @file useJobMasterData.ts
 * @description Hook lấy master data cho các bộ lọc việc làm (categories, levels, employment types, locations).
 * @architecture Tuân thủ caching dài hạn (staleTime: 30m) để dropdown không bao giờ bị giật lag khi chuyển trang.
 */

import { useQuery } from "@tanstack/react-query";
import { jobService } from "../services/jobService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";

export function useJobMasterData() {
  return useQuery({
    queryKey: candidateQueryKeys.jobs.masterData,
    queryFn: ({ signal }) => jobService().getMasterData(signal),
    staleTime: 30 * 60 * 1000, // 30 phút
    gcTime: 24 * 60 * 60 * 1000, // 24 giờ
  });
}
