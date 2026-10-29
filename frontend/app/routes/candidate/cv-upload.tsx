/**
 * @file cv-upload.tsx
 * @description Route chính cho trang Tải CV lên (/cv/upload).
 * @architecture Thin Route Pattern: Ủy quyền toàn bộ UI cho CvUploadView.
 */

import { CvUploadView } from "~/features/candidate/components/cv-upload/CvUploadView";

export function meta() {
  return [
    { title: "Tải CV lên - FutureCV" },
    {
      name: "description",
      content:
        "Tải lên CV cá nhân dạng PDF để hệ thống FutureCV tự động phân tích điểm chất lượng và đồng bộ vào Kho hồ sơ ứng tuyển.",
    },
  ];
}

export default function CvUploadPage() {
  return <CvUploadView />;
}
