/**
 * @file candidateCvService.ts
 * @description Candidate CV Service: Giao tiếp API quản lý CV của ứng viên (P3-UC01..P3-UC06).
 * @architecture Gọi API thật qua fetcher (auth: true). KHÔNG MOCK.
 * Đối soát: CandidateProfileController.cs, CandidateService.cs.
 */

import { fetcher } from "~/lib/fetcher";
import type { CvResponse } from "../types";
import type {
  CvAnalysisResponse,
  UpdateCvTitleRequest,
} from "../types/cv.types";

export const candidateCvService = {
  // ── List & Detail ───────────────────────────────────────────────────────────

  /** GET /api/candidate/cvs — Lấy toàn bộ danh sách CV */
  async list(signal?: AbortSignal): Promise<CvResponse[]> {
    return fetcher<CvResponse[]>("/api/candidate/cvs", {
      method: "GET",
      auth: true,
      signal,
    });
  },

  /** GET /api/candidate/cvs/{id} — Chi tiết một CV */
  async getById(id: string, signal?: AbortSignal): Promise<CvResponse> {
    return fetcher<CvResponse>(`/api/candidate/cvs/${id}`, {
      method: "GET",
      auth: true,
      signal,
    });
  },

  // ── Upload ──────────────────────────────────────────────────────────────────

  /**
   * POST /api/candidate/cvs — Tải lên CV mới (PDF ≤ 5MB).
   * Lưu ý: field tên "cv" (không phải "file"), title qua query param.
   */
  async upload(file: File, title?: string): Promise<CvResponse> {
    const formData = new FormData();
    formData.append("cv", file); // field đúng tên backend yêu cầu

    const url = title?.trim()
      ? `/api/candidate/cvs?title=${encodeURIComponent(title.trim())}`
      : "/api/candidate/cvs";

    return fetcher<CvResponse>(url, {
      method: "POST",
      auth: true,
      body: formData,
    });
  },

  // ── Mutations ───────────────────────────────────────────────────────────────

  /** PATCH /api/candidate/cvs/{id}/title - Đổi tên CV */
  async updateTitle(id: string, title: string): Promise<CvResponse> {
    return fetcher<CvResponse>(`/api/candidate/cvs/${id}/title`, {
      method: "PATCH",
      auth: true,
      body: { title } satisfies UpdateCvTitleRequest,
    });
  },

  /** DELETE /api/candidate/cvs/{id} — Xóa CV (soft-delete, 204) */
  async delete(id: string): Promise<void> {
    return fetcher<void>(`/api/candidate/cvs/${id}`, {
      method: "DELETE",
      auth: true,
    });
  },

  /** PUT /api/candidate/cvs/{id}/select — Đặt làm CV chính */
  async selectPrimary(id: string): Promise<CvResponse> {
    return fetcher<CvResponse>(`/api/candidate/cvs/${id}/select`, {
      method: "PUT",
      auth: true,
    });
  },

  // ── Analysis ────────────────────────────────────────────────────────────────

  /**
   * GET /api/candidate/cvs/{id}/analysis — Lấy điểm đánh giá CV.
   * BE tự chấm lần đầu nếu chưa có evaluation (rule-based, không cần polling).
   */
  async getAnalysis(id: string, signal?: AbortSignal): Promise<CvAnalysisResponse> {
    return fetcher<CvAnalysisResponse>(`/api/candidate/cvs/${id}/analysis`, {
      method: "GET",
      auth: true,
      signal,
    });
  },

  /**
   * POST /api/candidate/cvs/{id}/analyze — Chấm lại điểm CV (re-compute).
   * Gọi khi người dùng bấm nút "Chấm lại" sau khi cập nhật thông tin.
   */
  async analyze(id: string): Promise<CvAnalysisResponse> {
    return fetcher<CvAnalysisResponse>(`/api/candidate/cvs/${id}/analyze`, {
      method: "POST",
      auth: true,
    });
  },
};
