import { useMutation, useQueryClient } from "@tanstack/react-query";
import { candidateQueryKeys } from "~/features/candidate/queries/candidateQueryKeys";
import { candidateProfileApi } from "~/services/api/candidate.service";

export function useUploadCandidateAvatar() {
  const queryClient = useQueryClient();

  return useMutation<string, Error, File>({
    mutationFn: async (file: File) => {
      return await candidateProfileApi.uploadAvatar(file);
    },
    onSuccess: (newAvatarUrl) => {
      queryClient.setQueryData(candidateQueryKeys.profile, (old: unknown) => {
        if (!old || typeof old !== "object") return old;
        return { ...old, avatarUrl: newAvatarUrl };
      });
      queryClient.invalidateQueries({ queryKey: candidateQueryKeys.profile });
    },
  });
}
