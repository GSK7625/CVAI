export function formatSalary(min?: number | null, max?: number | null, currency = "Triệu"): string {
  const toM = (v: number) => (v >= 1000 ? v / 1000 : v);
  if (min != null && max != null) return `${toM(min)} - ${toM(max)} ${currency}`;
  if (min != null) return `Từ ${toM(min)} ${currency}`;
  if (max != null) return `Lên đến ${toM(max)} ${currency}`;
  return "Thỏa thuận";
}

export function timeAgo(iso: string | Date): string {
  const date = typeof iso === "string" ? new Date(iso) : iso;
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return "Vừa đăng";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `Đăng ${minutes} phút trước`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Đăng ${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `Đăng ${days} ngày trước`;
  const weeks = Math.floor(days / 7);
  if (weeks < 5) return `Đăng ${weeks} tuần trước`;
  const months = Math.floor(days / 30);
  return `Đăng ${months} tháng trước`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("vi-VN").format(value);
}

// -----------------------------------------------------------------------------
// CV Utilities (FC-82, FC-81b)
// -----------------------------------------------------------------------------

export const CV_MAX_SIZE_BYTES = 5 * 1024 * 1024; // 5MB

/**
 * Kiểm tra tính hợp lệ của file CV (PDF, <= 5MB).
 * Trả về thông báo lỗi (string) nếu không hợp lệ, hoặc null nếu hợp lệ.
 */
export function validateCvFile(file: File): string | null {
  const ext = file.name.split(".").pop()?.toLowerCase();
  const isPdfExt = ext === "pdf";
  const isPdfMime = !file.type || file.type === "application/pdf";

  if (!isPdfExt || !isPdfMime) {
    return "Chỉ chấp nhận file định dạng PDF (.pdf).";
  }
  if (file.size > CV_MAX_SIZE_BYTES) {
    return "Dung lượng file CV không được vượt quá 5MB.";
  }
  return null;
}

/**
 * Trích xuất tiêu đề mặc định từ tên file CV (loại bỏ đuôi .pdf và ký tự gạch dưới).
 */
export function cvTitleFromFile(fileName: string): string {
  return fileName.replace(/\.pdf$/i, "").replace(/_/g, " ").trim();
}


