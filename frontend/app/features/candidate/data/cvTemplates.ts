export interface CvTemplate {
  id: string;
  name: string;
  subtitle: string;
  category: "simple" | "professional" | "modern" | "impressive" | "harvard" | "ats";
  categoryName: string;
  tags: string[];
  colors: string[];
  defaultColor: string;
  thumbnail: string;
  isHot?: boolean;
  isNew?: boolean;
  sampleCandidate: {
    fullName: string;
    title: string;
    avatar: string;
    summary: string;
    skills: string[];
  };
}

export const CV_TEMPLATES: CvTemplate[] = [
  {
    id: "standard-general",
    name: "Tiêu chuẩn",
    subtitle: "Dành cho mọi ngành nghề, bố cục gọn gàng chuẩn ATS",
    category: "ats",
    categoryName: "ATS",
    tags: ["ATS", "Đơn giản", "Chuẩn quốc tế"],
    colors: ["#111827", "#1e3a8a", "#047857", "#c9973b"],
    defaultColor: "#111827",
    thumbnail: "standard",
    isHot: true,
    sampleCandidate: {
      fullName: "Lê Quang Dũng",
      title: "Business Development Executive",
      avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
      summary: "Có 3 năm kinh nghiệm trong phát triển kinh doanh B2B và mở rộng thị phần đối tác chiến lược.",
      skills: ["Bán hàng B2B", "Đàm phán & Thuyết trình", "Phân tích thị trường", "CRM"],
    },
  },
  {
    id: "junior-starter",
    name: "Tiêu chuẩn (Ít kinh nghiệm)",
    subtitle: "Tập trung làm nổi bật hoạt động, kỹ năng & học vấn cho sinh viên mới tốt nghiệp",
    category: "simple",
    categoryName: "Đơn giản",
    tags: ["ATS", "Đơn giản", "Sinh viên mới ra trường"],
    colors: ["#047857", "#1e40af", "#111827", "#c9973b"],
    defaultColor: "#047857",
    thumbnail: "junior",
    isHot: true,
    sampleCandidate: {
      fullName: "Nguyễn Minh Trang",
      title: "Audit / Financial Analyst Intern",
      avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80",
      summary: "Sinh viên năm cuối loại Giỏi chuyên ngành Kế toán - Kiểm toán ĐH Ngoại Thương, đạt IELTS 7.5.",
      skills: ["Excel & PowerBI", "IFRS / VAS", "Phân tích BCTC", "Tiếng Anh C1"],
    },
  },
  {
    id: "impressive-dark-header",
    name: "Ấn tượng 6",
    subtitle: "Thiết kế hiện đại với header tối màu thu hút ánh nhìn của nhà tuyển dụng",
    category: "impressive",
    categoryName: "Ấn tượng",
    tags: ["ATS", "Hiện đại", "Chuyên nghiệp"],
    colors: ["#1e293b", "#312e81", "#14532d", "#7c2d12"],
    defaultColor: "#1e293b",
    thumbnail: "impressive",
    isNew: true,
    sampleCandidate: {
      fullName: "Trần Mạnh Dũng",
      title: "Content & Growth Lead",
      avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
      summary: "Chuyên gia Content & Social Marketing 5 năm kinh nghiệm quản lý team và tối ưu ROI chuyển đổi.",
      skills: ["Growth Marketing", "Social Ads", "Team Management", "SEO & Copywriting"],
    },
  },
  {
    id: "professional-executive",
    name: "Chuyên nghiệp Classic",
    subtitle: "Bố cục 2 cột cân đối, thanh lịch, phù hợp cho cấp bậc Senior & Quản lý",
    category: "professional",
    categoryName: "Chuyên nghiệp",
    tags: ["Chuyên nghiệp", "Senior", "2 Cột"],
    colors: ["#1e3a8a", "#0f172a", "#065f46", "#b45309"],
    defaultColor: "#1e3a8a",
    thumbnail: "professional",
    isHot: true,
    sampleCandidate: {
      fullName: "Hoàng Nhật Nam",
      title: "Senior Software Architect",
      avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
      summary: "Senior Architect hơn 7 năm kinh nghiệm thiết kế hệ thống Microservices chịu tải cao.",
      skills: ["System Design", "Cloud Native (AWS/GCP)", "React / Node / .NET", "CI/CD & DevOps"],
    },
  },
  {
    id: "harvard-clean",
    name: "Harvard Academic Standard",
    subtitle: "Mẫu CV học thuật kinh điển của ĐH Harvard, tối giản 100% không ảnh",
    category: "harvard",
    categoryName: "Harvard",
    tags: ["Harvard", "ATS Tối ưu 100%", "Tối giản"],
    colors: ["#000000", "#1e293b", "#3b0764", "#064e3b"],
    defaultColor: "#000000",
    thumbnail: "harvard",
    isHot: true,
    sampleCandidate: {
      fullName: "Phạm Thu Hà",
      title: "Product Manager / Strategy Consultant",
      avatar: "",
      summary: "Thạc sĩ Quản trị Kinh doanh, 4 năm kinh nghiệm dẫn dắt các sản phẩm FinTech triệu người dùng.",
      skills: ["Product Roadmap", "Data-Driven Decision", "User Research", "Agile/Scrum"],
    },
  },
  {
    id: "modern-accent-sidebar",
    name: "Hiện đại Sidebar",
    subtitle: "Thanh bên màu sắc tạo điểm nhấn cho kỹ năng và thông tin liên hệ",
    category: "modern",
    categoryName: "Hiện đại",
    tags: ["Hiện đại", "Trẻ trung", "Thiết kế & Marketing"],
    colors: ["#c9973b", "#2563eb", "#059669", "#7c3aed"],
    defaultColor: "#c9973b",
    thumbnail: "modern",
    isNew: true,
    sampleCandidate: {
      fullName: "Vũ Bảo Ngọc",
      title: "UI/UX Product Designer",
      avatar: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
      summary: "UI/UX Designer với tư duy thẩm mỹ cao và am hiểu sâu sắc hành vi trải nghiệm người dùng.",
      skills: ["Figma & Design Systems", "Prototyping", "User Journey", "Mobile & Web App UI"],
    },
  },
];
