/**
 * @file AlreadyAppliedModal.tsx
 * @description Modal thông báo lỗi 409 khi ứng viên đã nộp hồ sơ trước đó (FC-81a).
 * @architecture Modal chuyển hướng xem danh sách đơn ứng tuyển tại /candidate/applications.
 */

import { Modal } from "~/components/ui";

interface AlreadyAppliedModalProps {
  open: boolean;
  onClose: () => void;
  jobTitle: string;
  onNavigateApplications: () => void;
}

export function AlreadyAppliedModal({
  open,
  onClose,
  jobTitle,
  onNavigateApplications,
}: AlreadyAppliedModalProps) {
  return (
    <Modal open={open} onClose={onClose} title="Thông báo ứng tuyển">
      <div className="py-2">
        <p className="text-sm text-ink-variant leading-relaxed">
          Bạn đã nộp hồ sơ ứng tuyển cho công việc <strong className="text-navy">{jobTitle}</strong> trước đó.
          Hồ sơ của bạn đang được nhà tuyển dụng xem xét.
        </p>
        <div className="mt-6 flex flex-col sm:flex-row justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 rounded-full border border-navy/20 text-xs font-semibold text-navy hover:bg-navy/5"
          >
            Đóng
          </button>
          <button
            type="button"
            onClick={onNavigateApplications}
            className="px-6 py-2.5 rounded-full bg-navy text-xs font-semibold text-white hover:bg-navy-secondary"
          >
            Đến danh sách ứng tuyển
          </button>
        </div>
      </div>
    </Modal>
  );
}
