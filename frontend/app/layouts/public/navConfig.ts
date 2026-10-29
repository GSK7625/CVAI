/**
 * @file navConfig.ts
 * @description File cấu hình dữ liệu tĩnh cho toàn bộ Navigation: Mega Menu Việc làm, Menu CV, Menu Công ty và Footer.
 * @architecture Tuân thủ Open/Closed Principle (OCP): Dễ dàng thêm bớt danh mục mà không phải sửa đổi JSX của Header/Footer.
 */

export interface NavItem {

  label: string;
  href: string;
  iconName?: string;
  badge?: string;
}

export const JOB_MENU_ACTIONS: NavItem[] = [
  { label: "Tìm việc làm", href: "/jobs", iconName: "search" },
  { label: "Việc làm đã lưu", href: "/candidate/saved-jobs", iconName: "bookmark" },
  { label: "Việc làm đã ứng tuyển", href: "/candidate/applications", iconName: "file-text" },

];



export const JOB_POSITION_LINKS: { label: string; href: string }[] = [
  { label: "Việc làm Nhân viên kinh doanh", href: "/jobs?q=Nhân%20viên%20kinh%20doanh" },
  { label: "Việc làm Lao động phổ thông", href: "/jobs?q=Lao%20động%20phổ%20thông" },
  { label: "Việc làm Kế toán", href: "/jobs?q=Kế%20toán" },
  { label: "Việc làm Senior", href: "/jobs?q=Senior" },
  { label: "Việc làm Marketing", href: "/jobs?q=Marketing" },
  { label: "Việc làm Kỹ sư xây dựng", href: "/jobs?q=Kỹ%20sư%20xây%20dựng" },
  { label: "Việc làm Hành chính nhân sự", href: "/jobs?q=Hành%20chính%20nhân%20sự" },
  { label: "Việc làm Thiết kế đồ họa", href: "/jobs?q=Thiết%20kế%20đồ%20họa" },
  { label: "Việc làm Chăm sóc khách hàng", href: "/jobs?q=Chăm%20sóc%20khách%20hàng" },
  { label: "Việc làm Bất động sản", href: "/jobs?q=Bất%20động%20sản" },
  { label: "Việc làm Ngân hàng", href: "/jobs?q=Ngân%20hàng" },
  { label: "Việc làm Giáo dục", href: "/jobs?q=Giáo%20dục" },
  { label: "Việc làm IT", href: "/jobs?q=IT" },
  { label: "Việc làm Telesales", href: "/jobs?q=Telesales" },
];

export const JOB_FIELD_LINKS: { label: string; href: string }[] = [
  { label: "Việc làm Sản xuất", href: "/jobs?q=Sản%20xuất" },
  { label: "Việc làm Bán lẻ - Hàng tiêu dùng - FMCG", href: "/jobs?q=Bán%20lẻ%20-%20Hàng%20tiêu%20dùng%20-%20FMCG" },
  { label: "Việc làm IT - Phần mềm", href: "/jobs?q=IT%20-%20Phần%20mềm" },
  { label: "Việc làm Xây dựng", href: "/jobs?q=Xây%20dựng" },
  { label: "Việc làm Giáo dục/Đào tạo", href: "/jobs?q=Giáo%20dục%2FĐào%20tạo" },
];

export const CV_STYLE_LINKS: NavItem[] = [
  { label: "Mẫu CV Đơn giản", href: "/cv/templates?category=simple", iconName: "box" },
  { label: "Mẫu CV Ấn tượng", href: "/cv/templates?category=impressive", iconName: "compass" },
  { label: "Mẫu CV Chuyên nghiệp", href: "/cv/templates?category=professional", iconName: "star" },
  { label: "Mẫu CV Harvard", href: "/cv/templates?category=harvard", iconName: "writing" },
];

export const CV_TOOL_LINKS: NavItem[] = [
  { label: "Quản lý CV", href: "/candidate/cvs", iconName: "file-text" },
  { label: "Tải CV lên", href: "/cv/upload", iconName: "cloud-upload" },
];

export const FOOTER_SECTIONS = [
  {
    title: "Dành cho ứng viên",
    links: [
      { label: "Tìm việc làm mới nhất", href: "/" },
      { label: "Tạo CV chuyên nghiệp", href: "/cv/templates" },
      { label: "Phân tích CV bằng AI", href: "/" },
    ],
  },
  {
    title: "Dành cho nhà tuyển dụng",
    links: [
      { label: "Đăng tin tuyển dụng", href: "/register" },
      { label: "Tìm kiếm hồ sơ ứng viên", href: "/register" },
      { label: "Giải pháp AI ATS", href: "/register" },
    ],
  },
  {
    title: "Liên hệ hỗ trợ",
    items: [
      "Hotline: 024 6680 5588",
      "Email: hotro@futurecv.vn",
      "Địa chỉ: Hà Nội & TP. Hồ Chí Minh",
    ],
  },
];
