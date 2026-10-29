/**
 * @file useCandidateCvs.ts
 * @description Hooks đầy đủ cho quản lý CV: query + mutations (FC-82, Phase 1).
 * @architecture TanStack Query, invalidate candidateQueryKeys.cvs.all sau mỗi mutation.
 * Pattern: disabled per-item khi isPending, toast từ hook, KHÔNG mock.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { candidateCvService } from "../services/candidateCvService";
import { candidateQueryKeys } from "../queries/candidateQueryKeys";
import { useAuthStore } from "~/stores/useAuthStore";
import { useUIStore } from "~/stores/useUIStore";

// ── Read Queries ──────────────────────────────────────────────────────────────

/** Danh sách tất cả CV của ứng viên. Key: cvs.all */
export function useCandidateCvs() {
  const user = useAuthStore((s) => s.user);

  return useQuery({
    queryKey: candidateQueryKeys.cvs.all,
    queryFn: ({ signal }) => candidateCvService.list(signal),
    enabled: !!user && user.role === "candidate",
    staleTime: 2 * 60 * 1000,
  });
}

/** Điểm phân tích chất lượng CV. Key: cvs.analysis(id) */
export function useCvAnalysis(cvId: string | null) {
  return useQuery({
    queryKey: candidateQueryKeys.cvs.analysis(cvId ?? ""),
    queryFn: ({ signal }) => candidateCvService.getAnalysis(cvId!, signal),
    enabled: !!cvId,
    staleTime: 5 * 60 * 1000,
  });
}

// ── Mutations ─────────────────────────────────────────────────────────────────

/** Tải lên CV mới (PDF ≤ 5MB). Invalidate cvs.all khi thành công. */
export function useUploadCandidateCv() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: ({ file, title }: { file: File; title?: string }) =>
      candidateCvService.upload(file, title),
    onSuccess: (newCv) => {
      showToast(`Đã tải lên CV "${newCv.title || "mới"}" thành công`, "success");
      queryClient.invalidateQueries({ queryKey: candidateQueryKeys.cvs.all });
    },
    onError: (err: Error) => {
      showToast(`Tải lên CV thất bại: ${err.message}`, "error");
    },
  });
}

/** Đổi tên CV inline (PATCH). Optimistic invalidate. */
export function useRenameCv() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      candidateCvService.updateTitle(id, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: candidateQueryKeys.cvs.all });
    },
    onError: (err: Error) => {
      showToast(`Đổi tên CV thất bại: ${err.message}`, "error");
    },
  });
}

/** Xóa CV (soft-delete, 204). Invalidate cvs.all sau thành công. */
export function useDeleteCv() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: (id: string) => candidateCvService.delete(id),
    onSuccess: () => {
      showToast("Đã xóa CV khỏi kho hồ sơ.", "success");
      queryClient.invalidateQueries({ queryKey: candidateQueryKeys.cvs.all });
    },
    onError: (err: Error) => {
      showToast(`Xóa CV thất bại: ${err.message}`, "error");
    },
  });
}

/** Đặt CV làm CV chính (PUT). Invalidate cvs.all. */
export function useSelectPrimaryCv() {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: (id: string) => candidateCvService.selectPrimary(id),
    onSuccess: (cv) => {
      showToast(`Đã đặt "${cv.title || "CV"}" làm hồ sơ chính.`, "success");
      queryClient.invalidateQueries({ queryKey: candidateQueryKeys.cvs.all });
    },
    onError: (err: Error) => {
      showToast(`Cập nhật CV chính thất bại: ${err.message}`, "error");
    },
  });
}

/** Chấm lại điểm CV (POST /analyze). Invalidate cvs.analysis(id). */
export function useAnalyzeCv(cvId: string) {
  const queryClient = useQueryClient();
  const showToast = useUIStore((s) => s.showToast);

  return useMutation({
    mutationFn: () => candidateCvService.analyze(cvId),
    onSuccess: (result) => {
      queryClient.setQueryData(candidateQueryKeys.cvs.analysis(cvId), result);
      showToast("Đã chấm lại điểm CV thành công.", "success");
    },
    onError: (err: Error) => {
      showToast(`Chấm lại điểm thất bại: ${err.message}`, "error");
    },
  });
}

