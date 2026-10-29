/**
 * @file useCvVaultSave.ts
 * @description Hook thực hiện đóng gói A4 PDF và lưu trực tiếp vào Kho CV ứng viên (POST /api/candidate/cvs).
 * @architecture Single Source of Truth cho thao tác lưu CV từ Builder vào Kho hồ sơ.
 * Phân tầng lỗi rõ ràng: Lỗi Client (Render PDF) vs Lỗi Server (API Upload qua useUploadCandidateCv).
 */

import { useState, useCallback } from "react";
import { useNavigate } from "react-router";
import { useUploadCandidateCv } from "./useCandidateCvs";
import { generateCvPdf, sanitizePdfFilename } from "../utils/cvPdfExport";
import { useAuthStore } from "~/stores/useAuthStore";
import { useUIStore } from "~/stores/useUIStore";

export const CV_VAULT_SAVE_LABELS = {
  idle: "Lưu vào Kho CV",
  generating: "Đang kết xuất PDF...",
  uploading: "Đang tải lên...",
  done: "Đã lưu vào Kho CV",
} as const;

export type CvVaultSaveState = keyof typeof CV_VAULT_SAVE_LABELS;

export function useCvVaultSave(fullName?: string) {
  const [state, setState] = useState<CvVaultSaveState>("idle");
  const uploadMutation = useUploadCandidateCv();
  const showToast = useUIStore((s) => s.showToast);
  const navigate = useNavigate();

  const trigger = useCallback(async () => {
    if (state !== "idle") return;

    // 1. Kiểm tra xác thực & đúng Role Ứng viên
    const user = useAuthStore.getState().user;
    if (!user) {
      showToast("Vui lòng đăng nhập tài khoản ứng viên để lưu CV vào Kho hồ sơ.", "info");
      navigate(`/login?returnTo=${encodeURIComponent(window.location.pathname)}`);
      return;
    }

    if (user.role !== "candidate") {
      showToast("Chỉ tài khoản Ứng viên mới có quyền lưu hồ sơ vào Kho CV.", "error");
      return;
    }

    // 2. Tầng 1 (Client): Tìm DOM và kết xuất file PDF chuẩn A4
    let pdfFile: File;
    try {
      setState("generating");

      const element = document.getElementById("cv-preview-paper");
      if (!element) {
        showToast("Không tìm thấy bản xem trước CV. Vui lòng thử lại.", "error");
        setState("idle");
        return;
      }

      const filename = sanitizePdfFilename(fullName || "UngVien");
      const { file } = await generateCvPdf(element, { filename });
      pdfFile = file;
    } catch (renderErr) {
      console.error("Lỗi khi kết xuất PDF:", renderErr);
      showToast("Không thể kết xuất tệp PDF. Vui lòng thử lại.", "error");
      setState("idle");
      return;
    }

    // 3. Tầng 2 (Server): Upload file PDF lên Backend
    // useUploadCandidateCv đã có sẵn onError và toast chuẩn -> Không bắn toast trùng lặp tại đây
    try {
      setState("uploading");
      const today = new Date().toLocaleDateString("vi-VN").replace(/\//g, "-");
      const title = `CV từ Builder - ${today}`;

      await uploadMutation.mutateAsync({ file: pdfFile, title });
      setState("done");

      showToast("Đã lưu CV thành công vào Kho hồ sơ!", "success");
      setTimeout(() => {
        setState("idle");
        navigate("/candidate/cvs");
      }, 1500);
    } catch {
      // uploadMutation.onError đã hiển thị thông báo lỗi chi tiết từ máy chủ
      setState("idle");
    }
  }, [state, fullName, uploadMutation, showToast, navigate]);

  return {
    state,
    trigger,
    isBusy: state !== "idle",
  };
}
