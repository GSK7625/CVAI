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
    location: "Hanoi",
    locationId: "hn",
    salaryMin: 35,
    salaryMax: 55,
    jobType: "Full-time (Hybrid)",
    employmentTypeId: "fulltime",
    experience: "3+ Years",
    categories: ["IT / Software"],
    categoryId: "it",
    postedAt: new Date(Date.now() - 2 * 864e5).toISOString(),
    hot: true,
    verified: true,
    level: "Senior",
    deadline: "15/10/2026",
    quantity: "3 openings",
    gender: "Any",
    workAddress: "Keangnam Landmark 72 Tower, Pham Hung, Nam Tu Liem, Hanoi",
    companyWebsite: "vngtech.com.vn",
    companySize: "1,000+ employees",
    companyIndustry: "Information Technology / Software",
    matchRate: 92,
    description:
      "Design, develop, and maintain large-scale web applications using ReactJS and Node.js.\nOptimize application performance across browsers and devices.\nCollaborate closely with Product, Design, and QA teams to deliver optimal technical solutions.\nContribute to system architecture design and cloud deployment (AWS/GCP).",
    descriptionList: [
      "Design, develop, and maintain large-scale web applications using ReactJS and Node.js.",
      "Optimize application performance across browsers and devices.",
      "Collaborate closely with Product, Design, and QA teams to deliver optimal technical solutions.",
      "Contribute to system architecture design and cloud deployment (AWS/GCP).",
    ],
    requirements: [
      "At least 3 years of experience working with the JavaScript ecosystem (ReactJS, Node.js, TypeScript).",
      "Strong knowledge of data structures, algorithms, and design patterns.",
      "Hands-on experience with SQL (PostgreSQL) and NoSQL (MongoDB) databases.",
      "Experience with Docker, CI/CD pipelines, and Cloud services is a strong plus.",
    ],
    benefits: [
      "Competitive compensation with bi-annual salary reviews and 13th/14th-month performance bonuses.",
      "MacBook Pro and external 4K monitor provided.",
      "Premium health insurance for employees and their family members.",
      "Young, dynamic culture with flexible hybrid working (2 remote days/week).",
    ],
  },
  {
    id: "2",
    title: "Digital Marketing Specialist (Conversion Optimization)",
    company: "Global Commerce Corp",
    location: "Ho Chi Minh City",
    locationId: "hcm",
    salaryMin: 15,
    salaryMax: 25,
    jobType: "Full-time",
    employmentTypeId: "fulltime",
    experience: "2 years",
    categories: ["Marketing / PR"],
    categoryId: "mkt",
    postedAt: new Date(Date.now() - 5 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Specialist",
    deadline: "20/10/2026",
    quantity: "2 openings",
    gender: "Any",
    workAddress: "Bitexco Financial Tower, 2 Hai Trieu, Ben Nghe, District 1, Ho Chi Minh City",
    companyWebsite: "globalcommerce.vn",
    companySize: "200 - 500 employees",
    companyIndustry: "E-Commerce / Retail",
    matchRate: 88,
    description:
      "Plan and operate digital marketing channels and optimize conversion rates for the e-commerce platform.\nAnalyze campaign performance data using Google Analytics 4 and Meta Ads Manager.\nRun A/B tests across landing pages and paid advertising campaigns.",
    descriptionList: [
      "Plan and operate digital marketing channels and optimize conversion rates for the e-commerce platform.",
      "Analyze campaign performance data using Google Analytics 4 and Meta Ads Manager.",
      "Run A/B tests across landing pages and paid advertising campaigns.",
    ],
    requirements: [
      "At least 2 years of Digital Marketing experience in E-commerce.",
      "Proficiency in GA4, Google Ads, Meta Ads, and conversion tracking tools.",
      "Strong data-driven mindset and awareness of market trends.",
    ],
    benefits: [
      "Uncapped conversion performance commission.",
      "Annual 5-star company retreat.",
      "100% sponsorship for advanced professional training courses.",
    ],
  },
  {
    id: "3",
    title: "B2B Healthcare Sales Executive",
    company: "Vietnam Healthcare Group",
    location: "Da Nang",
    locationId: "dn",
    salaryMin: 15,
    salaryMax: 30,
    jobType: "Full-time",
    employmentTypeId: "fulltime",
    experience: "1 year",
    categories: ["Sales / Business Development"],
    categoryId: "kd",
    postedAt: new Date(Date.now() - 1 * 864e5).toISOString(),
    hot: true,
    verified: true,
    level: "Executive",
    deadline: "25/10/2026",
    quantity: "5 openings",
    gender: "Any",
    workAddress: "6th Floor, Indochina Riverside Tower, 74 Bach Dang, Hai Chau, Da Nang",
    companyWebsite: "vietnamhealthcare.vn",
    companySize: "100 - 200 employees",
    companyIndustry: "Healthcare / Medical Devices",
    matchRate: 85,
    description:
      "Consult and expand our network of hospital and clinic clients across the Central Vietnam region.\nNegotiate and close supply contracts for medical equipment and consumables.\nNurture and maintain long-term relationships with strategic accounts.",
    descriptionList: [
      "Consult and expand our network of hospital and clinic clients across the Central Vietnam region.",
      "Negotiate and close supply contracts for medical equipment and consumables.",
      "Nurture and maintain long-term relationships with strategic accounts.",
    ],
    requirements: [
      "College or University degree in Business, Economics, Pharmacy, or a related field.",
      "Excellent communication, negotiation, and persuasive presentation skills.",
      "Willingness to travel regionally for short business trips.",
    ],
    benefits: [
      "Guaranteed base salary + attractive sales commission (average income 20 - 35 million VND/month).",
      "Full travel, fuel, and phone allowances.",
      "Full statutory insurance plus Bao Viet private health coverage.",
    ],
  },
  {
    id: "4",
    title: "General Accountant",
    company: "EduTech VN",
    location: "Hanoi",
    locationId: "hn",
    salaryMin: 12,
    salaryMax: 18,
    jobType: "Full-time",
    employmentTypeId: "fulltime",
    experience: "2 years",
    categories: ["Finance / Accounting"],
    categoryId: "tc",
    postedAt: new Date(Date.now() - 10 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Specialist",
    deadline: "30/10/2026",
    quantity: "1 opening",
    gender: "Any",
    workAddress: "4th Floor, CMC Tower, Duy Tan, Cau Giay, Hanoi",
    companyWebsite: "edutech.vn",
    companySize: "50 - 100 employees",
    companyIndustry: "Education / Training",
    matchRate: 80,
    description:
      "Maintain accounting ledgers, prepare internal financial reports, and coordinate with tax authorities.\nControl payables, receivables, invoices, and accounting vouchers in compliance with regulations.",
    descriptionList: [
      "Maintain accounting ledgers, prepare internal financial reports, and coordinate with tax authorities.",
      "Control payables, receivables, invoices, and accounting vouchers in compliance with regulations.",
    ],
    requirements: [
      "Bachelor's degree in Accounting or Auditing.",
      "Accounting certification and proficiency in MISA software and advanced Excel.",
    ],
    benefits: [
      "Friendly, collaborative education environment with flexible working hours.",
      "Scholarships for technology courses for employees and their children.",
    ],
  },
  {
    id: "5",
    title: "HR Compensation & Benefits (C&B) Specialist",
    company: "Techcom Solutions VN",
    location: "Hanoi",
    locationId: "hn",
    salaryMin: 12,
    salaryMax: 20,
    jobType: "Full-time",
    employmentTypeId: "fulltime",
    experience: "2 years",
    categories: ["Human Resources (HR)"],
    categoryId: "hr",
    postedAt: new Date(Date.now() - 3 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Specialist",
    deadline: "18/10/2026",
    quantity: "2 openings",
    gender: "Any",
    workAddress: "Keangnam Landmark 72 Tower, Pham Hung, Nam Tu Liem, Hanoi",
    companyWebsite: "techcom.vn",
    companySize: "500 - 1,000 employees",
    companyIndustry: "Information Technology",
    matchRate: 82,
    description:
      "Administer compensation, benefits policies, and employee retention programs.\nManage social insurance, personal income tax filings, and labor contracts.",
    descriptionList: [
      "Administer compensation, benefits policies, and employee retention programs.",
      "Manage social insurance, personal income tax filings, and labor contracts.",
    ],
    requirements: [
      "Strong knowledge of Labor Law, Social Insurance Law, and Personal Income Tax regulations.",
      "At least 2 years of dedicated experience in Compensation & Benefits (C&B).",
    ],
    benefits: [
      "Salary performance reviews twice a year.",
      "Complimentary lunch at the company canteen.",
    ],
  },
  {
    id: "6",
    title: "UI/UX Product Designer",
    company: "Global Commerce Corp",
    location: "Remote",
    locationId: "remote",
    salaryMin: 14,
    salaryMax: 22,
    jobType: "Part-time / Remote",
    employmentTypeId: "parttime",
    experience: "1 year",
    categories: ["Design / Creative"],
    categoryId: "tk",
    postedAt: new Date(Date.now() - 7 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Junior / Mid-level",
    deadline: "22/10/2026",
    quantity: "2 openings",
    gender: "Any",
    workAddress: "100% Remote",
    companyWebsite: "globalcommerce.vn",
    companySize: "200 - 500 employees",
    companyIndustry: "Design / Creative",
    matchRate: 90,
    description:
      "Design web and mobile product interfaces and maintain a unified design system.\nConduct user research and create interactive prototypes.",
    descriptionList: [
      "Design web and mobile product interfaces and maintain a unified design system.",
      "Conduct user research and create interactive prototypes.",
    ],
    requirements: [
      "Strong design portfolio demonstrating real-world product impact.",
      "Proficiency in Figma, Auto-layout, and Design Tokens.",
    ],
    benefits: [
      "100% remote work with full schedule flexibility.",
      "Monthly internet and home-office equipment stipend.",
    ],
  },
  {
    id: "8",
    title: "Production Line Machine Operator",
    company: "Crown Packaging Group VN",
    location: "Bac Ninh",
    salaryMin: 9,
    salaryMax: 14,
    jobType: "Full-time",
    employmentTypeId: "fulltime",
    experience: "No experience required",
    categories: ["Engineering"],
    postedAt: new Date(Date.now() - 4 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Operator / Staff",
    deadline: "15/10/2026",
    quantity: "10 openings",
    gender: "Any",
    workAddress: "Thang Long Industrial Park, Dong Anh, Hanoi",
    companyWebsite: "crownpackaging.vn",
    companySize: "1,000+ employees",
    companyIndustry: "Manufacturing / Packaging",
    matchRate: 75,
    description:
      "Operate packaging machinery and monitor automated production lines in compliance with workplace safety standards.",
    descriptionList: [
      "Operate packaging machinery and monitor automated production lines.",
      "Inspect finished product quality along the production line.",
    ],
    requirements: [
      "High school diploma or higher, good physical health, diligent and reliable.",
      "Available to work rotating shifts.",
    ],
    benefits: [
      "Free mid-shift meals and monthly attendance bonus.",
      "Company shuttle bus provided from central Hanoi to the plant.",
    ],
  },
  {
    id: "9",
    title: "Industrial Machine Operator",
    company: "AgriFeed Group",
    location: "Hai Phong",
    salaryMin: 18,
    salaryMax: 20,
    jobType: "Full-time",
    employmentTypeId: "fulltime",
    experience: "No experience required",
    categories: ["Engineering"],
    postedAt: new Date(Date.now() - 4 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Operator / Staff",
    deadline: "15/10/2026",
    quantity: "10 openings",
    gender: "Any",
    workAddress: "Thang Long Industrial Park, Dong Anh, Hanoi",
    companyWebsite: "crownpackaging.vn",
    companySize: "1,000+ employees",
    companyIndustry: "Manufacturing / Packaging",
    matchRate: 75,
    description:
      "Operate packaging machinery and monitor automated production lines in compliance with workplace safety standards.",
    descriptionList: [
      "Operate packaging machinery and monitor automated production lines.",
      "Inspect finished product quality along the production line.",
    ],
    requirements: [
      "High school diploma or higher, good physical health, diligent and reliable.",
      "Available to work rotating shifts.",
    ],
    benefits: [
      "Free mid-shift meals and monthly attendance bonus.",
      "Company shuttle bus provided from central Hanoi to the plant.",
    ],
  },
  {
    id: "10",
    title: "Production Line Operator (Textile Manufacturing)",
    company: "Vietnam Textile Group",
    location: "Thai Binh",
    salaryMin: 9,
    salaryMax: 14,
    jobType: "Full-time",
    employmentTypeId: "fulltime",
    experience: "No experience required",
    categories: ["Engineering"],
    postedAt: new Date(Date.now() - 4 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Operator / Staff",
    deadline: "15/10/2026",
    quantity: "10 openings",
    gender: "Any",
    workAddress: "Thang Long Industrial Park, Dong Anh, Hanoi",
    companyWebsite: "crownpackaging.vn",
    companySize: "1,000+ employees",
    companyIndustry: "Manufacturing / Packaging",
    matchRate: 75,
    description:
      "Operate packaging machinery and monitor automated production lines in compliance with workplace safety standards.",
    descriptionList: [
      "Operate packaging machinery and monitor automated production lines.",
      "Inspect finished product quality along the production line.",
    ],
    requirements: [
      "High school diploma or higher, good physical health, diligent and reliable.",
      "Available to work rotating shifts.",
    ],
    benefits: [
      "Free mid-shift meals and monthly attendance bonus.",
      "Company shuttle bus provided from central Hanoi to the plant.",
    ],
  },
  {
    id: "11",
    title: "Production Line Operator (Paper Manufacturing)",
    company: "Vietnam Paper Group",
    location: "Hai Duong",
    salaryMin: 9,
    salaryMax: 14,
    jobType: "Full-time",
    employmentTypeId: "fulltime",
    experience: "No experience required",
    categories: ["Engineering"],
    postedAt: new Date(Date.now() - 4 * 864e5).toISOString(),
    hot: false,
    verified: true,
    level: "Operator / Staff",
    deadline: "15/10/2026",
    quantity: "10 openings",
    gender: "Any",
    workAddress: "Thang Long Industrial Park, Dong Anh, Hanoi",
    companyWebsite: "crownpackaging.vn",
    companySize: "1,000+ employees",
    companyIndustry: "Manufacturing / Packaging",
    matchRate: 75,
    description:
      "Operate packaging machinery and monitor automated production lines in compliance with workplace safety standards.",
    descriptionList: [
      "Operate packaging machinery and monitor automated production lines.",
      "Inspect finished product quality along the production line.",
    ],
    requirements: [
      "High school diploma or higher, good physical health, diligent and reliable.",
      "Available to work rotating shifts.",
    ],
    benefits: [
      "Free mid-shift meals and monthly attendance bonus.",
      "Company shuttle bus provided from central Hanoi to the plant.",
    ],
  },
  {
    id: "12",
    title: "Deputy Site Manager (MEP Engineering)",
    company: "VISACONS Joint Stock Company",
    location: "Ho Chi Minh City",
    locationId: "hcm",
    salaryMin: 22,
    salaryMax: 32,
    jobType: "Full-time",
    employmentTypeId: "fulltime",
    experience: "3+ years",
    categories: ["Engineering"],
    postedAt: new Date(Date.now() - 1 * 864e5).toISOString(),
    hot: true,
    verified: true,
    level: "Manager / Deputy Site Manager",
    deadline: "28/10/2026",
    quantity: "2 openings",
    gender: "Any",
    workAddress: "Sala Urban Area Project, Mai Chi Tho Street, Thu Duc City, Ho Chi Minh City",
    companyWebsite: "visacons.com.vn",
    companySize: "500 - 1,000 employees",
    companyIndustry: "Construction / Real Estate",
    matchRate: 86,
    description:
      "Supervise MEP (Mechanical, Electrical, Plumbing) construction for high-rise buildings and urban developments.\nManage subcontractors and enforce schedule adherence and site safety standards.",
    descriptionList: [
      "Supervise MEP (Mechanical, Electrical, Plumbing) construction for high-rise buildings and urban developments.",
      "Manage subcontractors and enforce schedule adherence and site safety standards.",
    ],
    requirements: [
      "Bachelor's degree in Electrical, Electromechanical, or Automation Engineering.",
      "Valid Grade II or higher MEP construction supervision practicing certificate.",
    ],
    benefits: [
      "Attractive milestone and project completion bonuses.",
      "Full premium protective gear and 24/7 accident insurance provided.",
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
