/**
 * @file CvPickerSection.tsx
 * @description Phần chọn hoặc tải lên CV ứng tuyển (FC-81a, P3-UC01, P3-UC05).
 * @architecture Double-bezel nesting, hỗ trợ chọn CV sẵn có hoặc tải trực tiếp file PDF.
 */

import type { ChangeEvent, RefObject } from "react";
import {
  IconCheck,
  IconCloudUpload,
  IconFileText,
  IconLoader2,
} from "@tabler/icons-react";
import type { CvResponse } from "../../types";
import { Skeleton } from "~/components/ui";

interface CvPickerSectionProps {
  cvs: CvResponse[];
  selectedCvId: string;
  onSelectCv: (id: string) => void;
  isLoading: boolean;
  isUploadingInline: boolean;
  onUploadFile: (e: ChangeEvent<HTMLInputElement>) => void;
  fileInputRef: RefObject<HTMLInputElement | null>;
}

export function CvPickerSection({
  cvs,
  selectedCvId,
  onSelectCv,
  isLoading,
  isUploadingInline,
  onUploadFile,
  fileInputRef,
}: CvPickerSectionProps) {
  return (
    <div className="p-1.5 rounded-[2rem] bg-navy/5 border border-navy/10">
      <div className="p-6 sm:p-8 bg-white rounded-[calc(2rem-0.375rem)] shadow-[inset_0_1px_1px_rgba(255,255,255,0.8)]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-navy/5 pb-4 mb-6">
          <div>
            <h2 className="text-base font-bold text-navy">2. Chọn CV ứng tuyển</h2>
            <p className="text-xs text-ink-variant mt-0.5">
              Chọn một bản CV lưu trên hệ thống hoặc tải lên file PDF mới
            </p>
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={onUploadFile}
            />
            <button
              type="button"
              disabled={isUploadingInline}
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-navy/20 bg-surface-low text-xs font-semibold text-navy hover:bg-navy/5 hover:border-navy transition-all active:scale-[0.98] disabled:opacity-50"
            >
              {isUploadingInline ? (
                <>
                  <IconLoader2 size={14} className="animate-spin text-navy" />
                  <span>Đang tải lên...</span>
                </>
              ) : (
                <>
                  <IconCloudUpload size={15} />
                  <span>Tải lên CV khác (.pdf)</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Danh sách CV */}
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-16 w-full rounded-2xl" />
            <Skeleton className="h-16 w-full rounded-2xl" />
          </div>
        ) : cvs.length === 0 ? (
          /* Chưa có CV nào: Dropzone lớn */
          <div
            role="button"
            tabIndex={0}
            onClick={() => fileInputRef.current?.click()}
            onKeyDown={(e) => e.key === "Enter" && fileInputRef.current?.click()}
            className="flex flex-col items-center justify-center p-8 rounded-2xl border-2 border-dashed border-navy/20 bg-surface-low/50 hover:bg-navy/[0.02] hover:border-navy cursor-pointer transition-all text-center"
          >
            <div className="w-12 h-12 rounded-full bg-navy/5 text-navy flex items-center justify-center mb-3">
              <IconCloudUpload size={24} stroke={1.5} />
            </div>
            <h3 className="font-semibold text-sm text-navy">Bạn chưa có CV nào trong hồ sơ</h3>
            <p className="text-xs text-ink-variant mt-1 max-w-sm">
              Bấm để tải lên CV định dạng PDF (tối đa 5MB) để tiến hành ứng tuyển vị trí này.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {cvs.map((cv) => {
              const isSelected = selectedCvId === cv.id;
              return (
                <div
                  key={cv.id}
                  role="button"
                  tabIndex={0}
                  onClick={() => onSelectCv(cv.id)}
                  onKeyDown={(e) => e.key === "Enter" && onSelectCv(cv.id)}
                  className={`group p-1 rounded-2xl transition-all duration-300 cursor-pointer ${
                    isSelected
                      ? "bg-navy/10 ring-2 ring-navy/40 shadow-sm"
                      : "bg-transparent border border-navy/10 hover:border-navy/30"
                  }`}
                >
                  <div
                    className={`p-4 rounded-[calc(1rem-0.125rem)] flex items-center justify-between gap-4 transition-colors ${
                      isSelected ? "bg-white" : "bg-surface-low/60 hover:bg-white"
                    }`}
                  >
                    <div className="flex items-center gap-3.5 min-w-0">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${
                          isSelected ? "bg-navy text-white shadow-xs" : "bg-navy/5 text-navy"
                        }`}
                      >
                        <IconFileText size={20} stroke={1.5} />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-bold text-navy truncate">
                            {cv.title || "Bản CV ứng tuyển"}
                          </h4>
                          {cv.isPrimary && (
                            <span className="shrink-0 px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-[10px] font-semibold">
                              CV Chính
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-ink-muted mt-0.5 truncate">
                          {cv.fileType ? cv.fileType.toUpperCase() : "PDF"} • Tải lên:{" "}
                          {new Date(cv.uploadedAt).toLocaleDateString("vi-VN")}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {cv.fileUrl && (
                        <a
                          href={cv.fileUrl}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-xs text-navy underline hover:text-navy-secondary hidden sm:inline"
                        >
                          Xem trước
                        </a>
                      )}
                      <div
                        className={`w-6 h-6 rounded-full border flex items-center justify-center transition-all ${
                          isSelected
                            ? "border-navy bg-navy text-white"
                            : "border-navy/20 bg-white"
                        }`}
                      >
                        {isSelected && <IconCheck size={14} stroke={2.5} />}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
