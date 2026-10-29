/**
 * @file cvPdfExport.ts
 * @description Trình xuất và tạo file PDF chất lượng cao từ DOM phần tử CV.
 * Sử dụng `html2canvas-pro` (hỗ trợ hoàn toàn CSS OKLCH / modern CSS của Tailwind v4)
 * kết hợp `jspdf` để tạo file PDF chuẩn A4 siêu nét.
 */

import html2canvas from "html2canvas-pro";
import { jsPDF } from "jspdf";

export interface GenerateCvPdfOptions {
  filename?: string;
  marginMm?: number;
}

export interface GeneratedCvPdf {
  blob: Blob;
  file: File;
  pdf: jsPDF;
}

/** Chuyển đổi tên tiếng Việt có dấu thành tên file ASCII chuẩn không dấu để tránh lỗi URL / CDN */
export function sanitizePdfFilename(name: string): string {
  const base = (name || "UngVien")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .trim()
    .replace(/[^a-zA-Z0-9_-]/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  return `${base || "UngVien"}_CV.pdf`;
}

/**
 * Kết xuất phần tử DOM của CV thành PDF chuẩn A4 (210 x 297 mm).
 */
export async function generateCvPdf(
  element: HTMLElement,
  options?: GenerateCvPdfOptions
): Promise<GeneratedCvPdf> {
  const filename = options?.filename || sanitizePdfFilename("UngVien");

  // Kết xuất Canvas với độ phân giải cao (scale: 2)
  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    logging: false,
    scrollX: 0,
    scrollY: 0,
    backgroundColor: "#ffffff",
  });

  const imgData = canvas.toDataURL("image/jpeg", 0.98);

  const pdf = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });

  const pdfPageWidth = pdf.internal.pageSize.getWidth(); // 210mm
  const pdfPageHeight = pdf.internal.pageSize.getHeight(); // 297mm

  // Tỉ lệ kích thước ảnh
  const imgWidth = pdfPageWidth;
  const imgHeight = (canvas.height * pdfPageWidth) / canvas.width;

  if (imgHeight <= pdfPageHeight) {
    // Vừa trọn 1 trang A4
    pdf.addImage(imgData, "JPEG", 0, 0, imgWidth, imgHeight);
  } else {
    // Nếu nội dung vượt quá 1 trang, tự động phân trang
    let heightLeft = imgHeight;
    let position = 0;

    pdf.addImage(imgData, "JPEG", 0, position, imgWidth, imgHeight);
    heightLeft -= pdfPageHeight;

    while (heightLeft > 5) {
      position -= pdfPageHeight;
      pdf.addPage();
      pdf.addImage(imgData, "JPEG", 0, position, imgWidth, imgHeight);
      heightLeft -= pdfPageHeight;
    }
  }

  const blob = pdf.output("blob");
  const file = new File([blob], filename, { type: "application/pdf" });

  return { blob, file, pdf };
}
