/**
 * @file jobs.mock.ts
 * @description Mock data danh sách việc làm (DEMO_JOBS) và hàm xử lý bộ lọc giả lập (filterDemoJobs) phục vụ môi trường phát triển (Dev/Demo).
 * @architecture Tuân thủ SRP (Tách riêng biệt dữ liệu mock ra khỏi tầng Service) & DIP (Làm nguồn fallback độc lập cho Service).
 */

import type { Job, JobFilters, JobListResult, JobMasterData } from "../types";


export const DEMO_JOBS: Job[] = [
  {
    id: "1",
    title: "Senior Fullstack Engineer (React / Node.js & Cloud)",
    company: "VNG Tech Corporation",
    location: "Hà Nội",
    salaryMin: 35,
    salaryMax: 55,
    jobType: "Toàn thời gian (Hybrid)",
    experience: "3+ Năm",
    categories: ["IT / Phần mềm"],
    postedAt: new Date(Date.now() - 2 * 864e5).toISOString(),
    hot: true,
    verified: true,
    level: "Senior",
    deadline: "15/10/2026",
    quantity: "03 người",
    gender: "Không yêu cầu",
    workAddress: "Tòa nhà Keangnam Landmark 72, Phạm Hùng, Nam Từ Liêm, Hà Nội",
    companyWebsite: "vngtech.com.vn",
    companySize: "1,000+ nhân viên",
    companyIndustry: "Công nghệ thông tin / Phần mềm",
    matchRate: 92,
    description:
      "Thiết kế, phát triển và bảo trì các ứng dụng web quy mô lớn sử dụng ReactJS và Node.js.\nTối ưu hóa hiệu suất ứng dụng trên các trình duyệt và thiết bị khác nhau.\nPhối hợp chặt chẽ với đội ngũ Product, Design và QA để đưa ra giải pháp kỹ thuật tối ưu.\nTham gia thiết kế kiến trúc hệ thống và deploy lên nền tảng Cloud (AWS/GCP).",
    descriptionList: [
      "Thiết kế, phát triển và bảo trì các ứng dụng web quy mô lớn sử dụng ReactJS và Node.js.",
      "Tối ưu hóa hiệu suất ứng dụng trên các trình duyệt và thiết bị khác nhau.",
      "Phối hợp chặt chẽ với đội ngũ Product, Design và QA để đưa ra giải pháp kỹ thuật tối ưu.",
      "Tham gia thiết kế kiến trúc hệ thống và deploy lên nền tảng Cloud (AWS/GCP).",
    ],
    requirements: [
      "Tối thiểu 3 năm kinh nghiệm làm việc với hệ sinh thái Javascript (ReactJS, Node.js, TypeScript).",
      "Nắm vững kiến thức về cấu trúc dữ liệu, thuật toán và Design Patterns.",
      "Có kinh nghiệm làm việc với cơ sở dữ liệu SQL (PostgreSQL) và NoSQL (MongoDB).",
      "Kinh nghiệm làm việc với Docker, CI/CD và các dịch vụ Cloud là một lợi thế lớn.",
    ],
    benefits: [
      "Lương thưởng hấp dẫn, review lương 2 lần/năm. Thưởng tháng 13, 14 tùy theo kết quả kinh doanh.",
      "Cung cấp Macbook Pro và màn hình phụ 4K làm việc.",
      "Bảo hiểm sức khỏe cao cấp cho nhân viên và người thân.",
      "Môi trường làm việc trẻ trung, năng động, linh hoạt thời gian (Hybrid working 2 ngày remote/tuần).",
    ],
  },
  {
    id: "2",
    title: "Chuyên Viên Marketing Digital (Tối ưu chuyển đổi)",
    company: "Global Commerce Corp",
    location: "TP. HCM",
    salaryMin: 15,
    salaryMax: 25,
    jobType: "Toàn thời gian",
    experience: "2 năm",
    categories: ["Marketing / PR"],
    postedAt: new Date(Date.now() - 5 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Chuyên viên",
    deadline: "20/10/2026",
    quantity: "02 người",
    gender: "Không yêu cầu",
    workAddress: "Tòa nhà Bitexco Financial Tower, Số 2 Hải Triều, Bến Nghé, Quận 1, TP. HCM",
    companyWebsite: "globalcommerce.vn",
    companySize: "200 - 500 nhân viên",
    companyIndustry: "Thương mại điện tử / Bán lẻ",
    matchRate: 88,
    description:
      "Lên kế hoạch và vận hành các kênh marketing số, tối ưu tỷ lệ chuyển đổi cho website thương mại điện tử.\nPhân tích dữ liệu hiệu quả chiến dịch qua Google Analytics 4, Meta Ads Manager.\nThực hiện A/B testing cho landing page và chiến dịch quảng cáo.",
    descriptionList: [
      "Lên kế hoạch và vận hành các kênh marketing số, tối ưu tỷ lệ chuyển đổi cho website thương mại điện tử.",
      "Phân tích dữ liệu hiệu quả chiến dịch qua Google Analytics 4, Meta Ads Manager.",
      "Thực hiện A/B testing cho landing page và chiến dịch quảng cáo.",
    ],
    requirements: [
      "Tối thiểu 2 năm kinh nghiệm Digital Marketing mảng E-commerce.",
      "Thành thạo GA4, Google Ads, Meta Ads và các công cụ tracking.",
      "Tư duy phân tích dữ liệu tốt và nhạy bén với xu hướng thị trường.",
    ],
    benefits: [
      "Thưởng hoa hồng theo hiệu suất chuyển đổi không giới hạn.",
      "Du lịch nghỉ dưỡng công ty 5 sao hàng năm.",
      "Được tài trợ 100% chi phí các khóa đào tạo nâng cao chuyên môn.",
    ],
  },
  {
    id: "3",
    title: "Nhân Viên Kinh Doanh B2B Y tế",
    company: "Vietnam Healthcare Group",
    location: "Đà Nẵng",
    salaryMin: 15,
    salaryMax: 30,
    jobType: "Toàn thời gian",
    experience: "1 năm",
    categories: ["Kinh doanh / Bán hàng"],
    postedAt: new Date(Date.now() - 1 * 864e5).toISOString(),
    hot: true,
    verified: true,
    level: "Nhân viên",
    deadline: "25/10/2026",
    quantity: "05 người",
    gender: "Không yêu cầu",
    workAddress: "Tầng 6, Tòa nhà Indochina Riverside, 74 Bạch Đằng, Hải Châu, Đà Nẵng",
    companyWebsite: "vietnamhealthcare.vn",
    companySize: "100 - 200 nhân viên",
    companyIndustry: "Y tế / Thiết bị y tế",
    matchRate: 85,
    description:
      "Tư vấn và phát triển mạng lưới khách hàng bệnh viện, phòng khám trong khu vực miền Trung.\nĐàm phán, ký kết hợp đồng cung cấp thiết bị và vật tư y tế.\nChăm sóc và duy trì mối quan hệ lâu dài với khách hàng chiến lược.",
    descriptionList: [
      "Tư vấn và phát triển mạng lưới khách hàng bệnh viện, phòng khám trong khu vực miền Trung.",
      "Đàm phán, ký kết hợp đồng cung cấp thiết bị và vật tư y tế.",
      "Chăm sóc và duy trì mối quan hệ lâu dài với khách hàng chiến lược.",
    ],
    requirements: [
      "Tốt nghiệp Cao đẳng/Đại học khối ngành Kinh tế, Y Dược hoặc liên quan.",
      "Kỹ năng giao tiếp, đàm phán và thuyết phục khách hàng xuất sắc.",
      "Sẵn sàng đi công tác ngắn ngày tại các tỉnh miền Trung.",
    ],
    benefits: [
      "Lương cứng đảm bảo + Hoa hồng doanh số hấp dẫn (Thu nhập trung bình 20 - 35 triệu/tháng).",
      "Phụ cấp xăng xe, điện thoại và chi phí công tác đầy đủ.",
      "Tham gia đầy đủ BHXH, BHYT và gói bảo hiểm sức khỏe Bảo Việt.",
    ],
  },
  {
    id: "4",
    title: "Nhân Viên Kế Toán Tổng Hợp",
    company: "EduTech VN",
    location: "Hà Nội",
    salaryMin: 12,
    salaryMax: 18,
    jobType: "Toàn thời gian",
    experience: "2 năm",
    categories: ["Tài chính / Kế toán"],
    postedAt: new Date(Date.now() - 10 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Chuyên viên",
    deadline: "30/10/2026",
    quantity: "01 người",
    gender: "Không yêu cầu",
    workAddress: "Tầng 4, Tòa nhà CMC Tower, Duy Tân, Cầu Giấy, Hà Nội",
    companyWebsite: "edutech.vn",
    companySize: "50 - 100 nhân viên",
    companyIndustry: "Giáo dục / Đào tạo",
    matchRate: 80,
    description:
      "Theo dõi sổ sách, lập báo cáo tài chính nội bộ và làm việc với cơ quan thuế.\nKiểm soát thu chi, hóa đơn chứng từ kế toán theo quy định pháp luật.",
    descriptionList: [
      "Theo dõi sổ sách, lập báo cáo tài chính nội bộ và làm việc với cơ quan thuế.",
      "Kiểm soát thu chi, hóa đơn chứng từ kế toán theo quy định pháp luật.",
    ],
    requirements: [
      "Tốt nghiệp Đại học chuyên ngành Kế toán - Kiểm toán.",
      "Có chứng chỉ kế toán và thành thạo phần mềm MISA, Excel nâng cao.",
    ],
    benefits: [
      "Môi trường giáo dục thân thiện, văn minh, giờ làm việc linh hoạt.",
      "Được cấp học bổng các khóa học công nghệ cho bản thân và con em.",
    ],
  },
  {
    id: "5",
    title: "Nhân Viên Nhân Sự (C&B)",
    company: "Techcom Solutions VN",
    location: "Hà Nội",
    salaryMin: 12,
    salaryMax: 20,
    jobType: "Toàn thời gian",
    experience: "2 năm",
    categories: ["Nhân sự (HR)"],
    postedAt: new Date(Date.now() - 3 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Chuyên viên",
    deadline: "18/10/2026",
    quantity: "02 người",
    gender: "Không yêu cầu",
    workAddress: "Tòa nhà Keangnam Landmark 72, Phạm Hùng, Nam Từ Liêm, Hà Nội",
    companyWebsite: "techcom.vn",
    companySize: "500 - 1,000 nhân viên",
    companyIndustry: "Công nghệ thông tin",
    matchRate: 82,
    description:
      "Quản lý chính sách lương thưởng, phúc lợi và các chương trình giữ chân nhân tài.\nThực hiện thủ tục bảo hiểm, thuế TNCN và hợp đồng lao động.",
    descriptionList: [
      "Quản lý chính sách lương thưởng, phúc lợi và các chương trình giữ chân nhân tài.",
      "Thực hiện thủ tục bảo hiểm, thuế TNCN và hợp đồng lao động.",
    ],
    requirements: [
      "Am hiểu sâu luật lao động, luật BHXH và luật thuế TNCN.",
      "Tối thiểu 2 năm kinh nghiệm chuyên môn mảng C&B.",
    ],
    benefits: [
      "Đánh giá xét duyệt tăng lương 2 lần/năm.",
      "Cơm trưa miễn phí tại canteen công ty.",
    ],
  },
  {
    id: "6",
    title: "Thiết Kế Đồ Họa (UI/UX Product Designer)",
    company: "Global Commerce Corp",
    location: "Từ xa",
    salaryMin: 14,
    salaryMax: 22,
    jobType: "Bán thời gian / Remote",
    experience: "1 năm",
    categories: ["Thiết kế / Nghệ thuật"],
    postedAt: new Date(Date.now() - 7 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Junior / Mid-level",
    deadline: "22/10/2026",
    quantity: "02 người",
    gender: "Không yêu cầu",
    workAddress: "Làm việc từ xa (Remote 100%)",
    companyWebsite: "globalcommerce.vn",
    companySize: "200 - 500 nhân viên",
    companyIndustry: "Thiết kế / Sáng tạo",
    matchRate: 90,
    description:
      "Thiết kế giao diện sản phẩm web/app, xây dựng design system thống nhất.\nThực hiện user research và prototype tương tác.",
    descriptionList: [
      "Thiết kế giao diện sản phẩm web/app, xây dựng design system thống nhất.",
      "Thực hiện user research và prototype tương tác.",
    ],
    requirements: [
      "Portfolio thiết kế ấn tượng chứng minh năng lực thực tế.",
      "Thành thạo công cụ Figma, Auto-layout và Design Tokens.",
    ],
    benefits: [
      "100% làm việc từ xa, tự chủ hoàn toàn thời gian.",
      "Trợ cấp chi phí internet và thiết bị làm việc hàng tháng.",
    ],
  },
  {
    id: "8",
    title: "Nhân Viên Vận Hành Máy Dây ",
    company: "Tập Đoàn Bao Bì Crown VN",
    location: "Bắc Ninh",
    salaryMin: 9,
    salaryMax: 14,
    jobType: "Toàn thời gian",
    experience: "Không yêu cầu",
    categories: ["Kỹ thuật"],
    postedAt: new Date(Date.now() - 4 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Công nhân / Nhân viên",
    deadline: "15/10/2026",
    quantity: "10 người",
    gender: "Không yêu cầu",
    workAddress: "Khu Công Nghiệp Thăng Long, Đông Anh, Hà Nội",
    companyWebsite: "crownpackaging.vn",
    companySize: "1,000+ nhân viên",
    companyIndustry: "Sản xuất / Bao bì",
    matchRate: 75,
    description:
      "Vận hành máy đóng gói và kiểm soát dây chuyền sản xuất tự động theo quy trình an toàn lao động.",
    descriptionList: [
      "Vận hành máy đóng gói và kiểm soát dây chuyền sản xuất tự động.",
      "Kiểm tra chất lượng thành phẩm đầu ra trên dây chuyền.",
    ],
    requirements: [
      "Tốt nghiệp THPT trở lên, sức khỏe tốt, chăm chỉ và trung thực.",
      "Có thể làm việc theo ca luân phiên.",
    ],
    benefits: [
      "Bao ăn giữa ca và phụ cấp chuyên cần hàng tháng.",
      "Có xe đưa đón từ nội thành Hà Nội về nhà máy.",
    ],
  },
  {
    id: "9",
    title: "Nhân Viên Vận Hành Máy",
    company: "Tập Đoàn Cám",
    location: "Hải Phòng",
    salaryMin: 18,
    salaryMax: 20,
    jobType: "Toàn thời gian",
    experience: "Không yêu cầu",
    categories: ["Kỹ thuật"],
    postedAt: new Date(Date.now() - 4 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Công nhân / Nhân viên",
    deadline: "15/10/2026",
    quantity: "10 người",
    gender: "Không yêu cầu",
    workAddress: "Khu Công Nghiệp Thăng Long, Đông Anh, Hà Nội",
    companyWebsite: "crownpackaging.vn",
    companySize: "1,000+ nhân viên",
    companyIndustry: "Sản xuất / Bao bì",
    matchRate: 75,
    description:
      "Vận hành máy đóng gói và kiểm soát dây chuyền sản xuất tự động theo quy trình an toàn lao động.",
    descriptionList: [
      "Vận hành máy đóng gói và kiểm soát dây chuyền sản xuất tự động.",
      "Kiểm tra chất lượng thành phẩm đầu ra trên dây chuyền.",
    ],
    requirements: [
      "Tốt nghiệp THPT trở lên, sức khỏe tốt, chăm chỉ và trung thực.",
      "Có thể làm việc theo ca luân phiên.",
    ],
    benefits: [
      "Bao ăn giữa ca và phụ cấp chuyên cần hàng tháng.",
      "Có xe đưa đón từ nội thành Hà Nội về nhà máy.",
    ],
  },
  {
    id: "10",
    title: "Nhân Viên Vận Hành Máy Dây Chuyền Sản Xuất",
    company: "Tập Đoàn Dệt May",
    location: "Thái Bình",
    salaryMin: 9,
    salaryMax: 14,
    jobType: "Toàn thời gian",
    experience: "Không yêu cầu",
    categories: ["Kỹ thuật"],
    postedAt: new Date(Date.now() - 4 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Công nhân / Nhân viên",
    deadline: "15/10/2026",
    quantity: "10 người",
    gender: "Không yêu cầu",
    workAddress: "Khu Công Nghiệp Thăng Long, Đông Anh, Hà Nội",
    companyWebsite: "crownpackaging.vn",
    companySize: "1,000+ nhân viên",
    companyIndustry: "Sản xuất / Bao bì",
    matchRate: 75,
    description:
      "Vận hành máy đóng gói và kiểm soát dây chuyền sản xuất tự động theo quy trình an toàn lao động.",
    descriptionList: [
      "Vận hành máy đóng gói và kiểm soát dây chuyền sản xuất tự động.",
      "Kiểm tra chất lượng thành phẩm đầu ra trên dây chuyền.",
    ],
    requirements: [
      "Tốt nghiệp THPT trở lên, sức khỏe tốt, chăm chỉ và trung thực.",
      "Có thể làm việc theo ca luân phiên.",
    ],
    benefits: [
      "Bao ăn giữa ca và phụ cấp chuyên cần hàng tháng.",
      "Có xe đưa đón từ nội thành Hà Nội về nhà máy.",
    ],
  },
  {
    id: "11",
    title: "Nhân Viên Vận Hành Máy Dây Chuyền Sản Xuất",
    company: "Tập Đoàn Giấy",
    location: "Hải Dương",
    salaryMin: 9,
    salaryMax: 14,
    jobType: "Toàn thời gian",
    experience: "Không yêu cầu",
    categories: ["Kỹ thuật"],
    postedAt: new Date(Date.now() - 4 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Công nhân / Nhân viên",
    deadline: "15/10/2026",
    quantity: "10 người",
    gender: "Không yêu cầu",
    workAddress: "Khu Công Nghiệp Thăng Long, Đông Anh, Hà Nội",
    companyWebsite: "crownpackaging.vn",
    companySize: "1,000+ nhân viên",
    companyIndustry: "Sản xuất / Bao bì",
    matchRate: 75,
    description:
      "Vận hành máy đóng gói và kiểm soát dây chuyền sản xuất tự động theo quy trình an toàn lao động.",
    descriptionList: [
      "Vận hành máy đóng gói và kiểm soát dây chuyền sản xuất tự động.",
      "Kiểm tra chất lượng thành phẩm đầu ra trên dây chuyền.",
    ],
    requirements: [
      "Tốt nghiệp THPT trở lên, sức khỏe tốt, chăm chỉ và trung thực.",
      "Có thể làm việc theo ca luân phiên.",
    ],
    benefits: [
      "Bao ăn giữa ca và phụ cấp chuyên cần hàng tháng.",
      "Có xe đưa đón từ nội thành Hà Nội về nhà máy.",
    ],
  },
  {
    id: "12",
    title: "Chỉ Huy Phó Công Trình (Cơ Điện MEP)",
    company: "Công ty Cổ phần VISACONS",
    location: "TP. HCM",
    salaryMin: 22,
    salaryMax: 32,
    jobType: "Toàn thời gian",
    experience: "Trên 3 năm",
    categories: ["Kỹ thuật"],
    postedAt: new Date(Date.now() - 1 * 864e5).toISOString(),
    hot: true,
    verified: true,
    level: "Quản lý / Chỉ huy phó",
    deadline: "28/10/2026",
    quantity: "02 người",
    gender: "Không yêu cầu",
    workAddress: "Dự án Khu Đô Thị Sala, Đường Mai Chí Thọ, TP. Thủ Đức, TP. HCM",
    companyWebsite: "visacons.com.vn",
    companySize: "500 - 1,000 nhân viên",
    companyIndustry: "Xây dựng / Bất động sản",
    matchRate: 86,
    description:
      "Giám sát thi công hệ thống cơ điện (MEP) cho các dự án cao tầng và khu đô thị.\nQuản lý nhà thầu phụ và kiểm tra tiến độ, an toàn lao động.",
    descriptionList: [
      "Giám sát thi công hệ thống cơ điện (MEP) cho các dự án cao tầng và khu đô thị.",
      "Quản lý nhà thầu phụ và kiểm tra tiến độ, an toàn lao động.",
    ],
    requirements: [
      "Tốt nghiệp Đại học chuyên ngành Điện, Cơ điện, Tự động hóa.",
      "Có chứng chỉ hành nghề giám sát thi công cơ điện hạng II trở lên.",
    ],
    benefits: [
      "Thưởng tiến độ và kết quả dự án hấp dẫn.",
      "Cung cấp đầy đủ đồ bảo hộ cao cấp và bảo hiểm tai nạn 24/7.",
    ],
  },
];

export function filterDemoJobs(filters: JobFilters): JobListResult {
  const keyword = (filters.keyword ?? "").trim().toLowerCase();
  const page = filters.page ?? 1;
  const pageSize = filters.pageSize ?? 5;

  const filtered = DEMO_JOBS.filter((job) => {
    const matchKeyword =
      !keyword ||
      job.title.toLowerCase().includes(keyword) ||
      job.company.toLowerCase().includes(keyword);
    const matchCategory =
      !filters.categoryId ||
      job.categoryId === filters.categoryId ||
      job.categories.some((c) => c.toLowerCase().includes(filters.categoryId!.toLowerCase()));
    const matchLocation =
      !filters.locationId ||
      job.locationId === filters.locationId ||
      job.location.toLowerCase().includes(filters.locationId.toLowerCase());
    const matchType =
      !filters.employmentTypeId ||
      job.employmentTypeId === filters.employmentTypeId ||
      job.jobType.toLowerCase().includes(filters.employmentTypeId.toLowerCase());
    return matchKeyword && matchCategory && matchLocation && matchType;
  });

  const start = (page - 1) * pageSize;
  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
    totalPages: Math.ceil(filtered.length / pageSize) || 1,
    hasPreviousPage: page > 1,
    hasNextPage: start + pageSize < filtered.length,
    isDemoFallback: true,
  };
}

export const DEMO_MASTER_DATA: JobMasterData = {
  isDemoFallback: true,
  categories: [
    { id: "it", name: "IT / Phần mềm" },
    { id: "kd", name: "Kinh doanh / Bán hàng" },
    { id: "mkt", name: "Marketing / PR" },
    { id: "tc", name: "Tài chính / Kế toán" },
    { id: "hr", name: "Nhân sự (HR)" },
    { id: "tk", name: "Thiết kế / Nghệ thuật" },
  ],
  levels: [
    { id: "intern", name: "Thực tập sinh" },
    { id: "fresher", name: "Fresher" },
    { id: "junior", name: "Junior" },
    { id: "middle", name: "Middle" },
    { id: "senior", name: "Senior" },
    { id: "lead", name: "Trưởng nhóm / Lead" },
  ],
  employmentTypes: [
    { id: "fulltime", name: "Toàn thời gian" },
    { id: "parttime", name: "Bán thời gian" },
    { id: "internship", name: "Thực tập" },
    { id: "contract", name: "Hợp đồng / Freelance" },
    { id: "remote", name: "Làm việc từ xa" },
  ],
  locations: [
    { id: "hn", name: "Hà Nội" },
    { id: "hcm", name: "TP. HCM" },
    { id: "dn", name: "Đà Nẵng" },
    { id: "remote", name: "Từ xa" },
  ],
};

// ---- Đồng bộ id giữa DEMO_JOBS và DEMO_MASTER_DATA ----
// Bộ lọc (chip trang chủ / sidebar) hoạt động theo id của master options;
// mock jobs chỉ mang text -> tự gán id tương ứng một lần khi module load,
// khỏi phải maintain id thủ công từng entry khi thêm/sửa job mock.
const normText = (s: string | undefined) => (s ?? "").toLowerCase().trim();
const matchDemoOption = (opts: { id: string; name: string }[], text: string | undefined) =>
  opts.find(
    (o) => normText(text).includes(normText(o.name)) || normText(o.name).includes(normText(text)),
  )?.id;

for (const job of DEMO_JOBS) {
  job.categoryId ??= matchDemoOption(DEMO_MASTER_DATA.categories, job.categories[0]);
  job.locationId ??= matchDemoOption(DEMO_MASTER_DATA.locations, job.location);
  job.employmentTypeId ??= matchDemoOption(DEMO_MASTER_DATA.employmentTypes, job.jobType);
  job.isDemoFallback = true;
}
