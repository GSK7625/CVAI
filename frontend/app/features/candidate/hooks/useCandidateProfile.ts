import { useQuery } from "@tanstack/react-query";
import { candidateQueryKeys } from "~/features/candidate/queries/candidateQueryKeys";
import { candidateProfileApi } from "~/services/api/candidate.service";
import { useAuthStore } from "~/stores/useAuthStore";
import type { CandidateProfileDto } from "~/types/api";

export function useCandidateProfile() {
  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);

  const isCandidate = user?.role === "candidate" && Boolean(accessToken);

  const query = useQuery<CandidateProfileDto, Error>({
    queryKey: candidateQueryKeys.profile,
    queryFn: async () => {
      return await candidateProfileApi.getProfile();
    },
    enabled: isCandidate,
    staleTime: 1000 * 60 * 5, // 5 phút
    retry: 1,
  });

  return {
    ...query,
    profile: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    // Fallback thông tin khi profile chưa load xong hoặc offline
    displayName: query.data?.fullName || user?.fullName || "",
    email: query.data?.email || user?.email || "",
    avatarUrl: query.data?.avatarUrl,
    candidateId: query.data?.id || user?.id || null,
  };
}
