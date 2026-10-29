import { useMutation, useQueryClient } from "@tanstack/react-query";
import { candidateQueryKeys } from "~/features/candidate/queries/candidateQueryKeys";
import { candidateProfileApi } from "~/services/api/candidate.service";
import type { UpdateCandidateProfileDto, CandidateProfileDto } from "~/types/api";

export function useUpdateCandidateProfile() {
  const queryClient = useQueryClient();

  return useMutation<CandidateProfileDto, Error, UpdateCandidateProfileDto>({
    mutationFn: async (dto: UpdateCandidateProfileDto) => {
      return await candidateProfileApi.updateProfile(dto);
    },
    onSuccess: (updatedData) => {
      queryClient.setQueryData(candidateQueryKeys.profile, updatedData);
      queryClient.invalidateQueries({ queryKey: candidateQueryKeys.profile });
    },
  });
}
