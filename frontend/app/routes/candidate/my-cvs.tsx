/**
 * @file my-cvs.tsx
 * @description Route thin wrapper cho trang Quản lý CV (/candidate/cvs — FC-82).
 * Sửa triệt để lỗi 404 từ dropdown điều hướng ứng viên.
 */
import { CvManagementView } from "~/features/candidate/components/cv-management/CvManagementView";

export default function MyCvsPage() {
  return <CvManagementView />;
}
