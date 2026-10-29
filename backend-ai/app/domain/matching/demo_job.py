"""Standardized high-quality demo fixtures for Job Matching evaluation and demonstrations."""

from app.contracts.cv import (
    EducationItem,
    ProjectItem,
    StructuredCv,
    WorkExperienceItem,
)
from app.contracts.job import StructuredJob

# ─────────────────────────────────────────────────────────────────────────────
# Standard Demo Job
# - 5 required skills (within 4-6)
# - 3 preferred skills (within 1-3)
# - clear minimum experience (3.0 years)
# - explicit education requirement
# - detailed, professional responsibilities description
# ─────────────────────────────────────────────────────────────────────────────
DEMO_JOB = StructuredJob(
    title="Senior Backend Engineer (Python / FastAPI)",
    description=(
        "Vị trí Senior Backend Engineer chịu trách nhiệm thiết kế, xây dựng và vận hành "
        "các hệ thống backend hiệu năng cao, phân tán trên nền tảng đám mây.\n\n"
        "Trách nhiệm chính:\n"
        "- Thiết kế kiến trúc microservices và phát triển các RESTful API hiệu năng cao bằng Python/FastAPI.\n"
        "- Thiết kế, tối ưu hóa mô hình cơ sở dữ liệu quan hệ PostgreSQL và bộ nhớ đệm phân tán Redis.\n"
        "- Đóng gói ứng dụng trong các container Docker và điều phối triển khai trên cụm Kubernetes.\n"
        "- Xây dựng các đường ống CI/CD tự động hóa kiểm thử và triển khai hạ tầng trên đám mây AWS.\n"
        "- Đánh giá mã nguồn (code review), duy trì chuẩn kỹ thuật và hướng dẫn chuyên môn cho các kỹ sư trẻ.\n"
        "- Giám sát, phát hiện sự cố hệ thống và tối ưu hóa độ trễ phản hồi của API."
    ),
    required_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "REST API"],
    preferred_skills=["Redis", "Kubernetes", "AWS"],
    minimum_experience_years=3.0,
    education_requirement="Cử nhân Công nghệ Thông tin hoặc ngành liên quan",
    location="Hà Nội (Hybrid)",
    salary="35,000,000 - 55,000,000 VND",
    employment_type="Full-time",
)

# ─────────────────────────────────────────────────────────────────────────────
# High Match Candidate (Matches all required skills, preferred skills, 4 yrs exp, degree)
# Expected Score: ~90-100
# ─────────────────────────────────────────────────────────────────────────────
DEMO_CV_HIGH = StructuredCv(
    full_name="Trần Minh Hoàng",
    email="hoang.tran@example.com",
    phone="0912345678",
    career_summary=(
        "Senior Backend Engineer với hơn 4 năm kinh nghiệm chuyên sâu về Python, FastAPI và hệ thống phân tán."
    ),
    skills=["Python", "FastAPI", "PostgreSQL", "Docker", "REST API", "Redis", "AWS", "Git", "Linux"],
    work_experience=[
        WorkExperienceItem(
            company="Fintech Solutions VN",
            job_title="Senior Backend Developer",
            start_date="2020-01",
            end_date="2024-01",
            duration="2020 - 2024",
            years_of_experience=4.0,
            description=(
                "Phát triển hệ thống xử lý giao dịch thanh toán bằng FastAPI, PostgreSQL và Redis. "
                "Tối ưu thông lượng tăng 40%."
            ),
        )
    ],
    education=[
        EducationItem(
            institution="Đại học Bách Khoa Hà Nội",
            degree="Kỹ sư",
            field_of_study="Công nghệ Thông tin",
            graduation_year="2020",
        )
    ],
    certificates=["AWS Certified Developer - Associate"],
    projects=[
        ProjectItem(
            name="Payment Processing Engine",
            description="Hệ thống thanh toán cốt lõi xử lý 10.000 giao dịch/giây.",
            technologies=["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        )
    ],
    technologies=["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "AWS"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Medium Match Candidate (Partial required skills 3/5, 0 preferred, 2 yrs exp < 3 yrs, bachelor)
# Expected Score: ~55-70
# ─────────────────────────────────────────────────────────────────────────────
DEMO_CV_MEDIUM = StructuredCv(
    full_name="Lê Văn Hùng",
    email="hung.le@example.com",
    phone="0987654321",
    career_summary="Backend Developer có 2 năm kinh nghiệm làm việc với Python và cơ sở dữ liệu quan hệ.",
    skills=["Python", "FastAPI", "PostgreSQL", "Git"],
    work_experience=[
        WorkExperienceItem(
            company="WebTech Company",
            job_title="Software Developer",
            start_date="2022-01",
            end_date="2024-01",
            duration="2022 - 2024",
            years_of_experience=2.0,
            description="Phát triển các API backend phục vụ ứng dụng quản lý doanh nghiệp.",
        )
    ],
    education=[
        EducationItem(
            institution="Đại học Khoa học Tự nhiên",
            degree="Cử nhân",
            field_of_study="Công nghệ Thông tin",
            graduation_year="2022",
        )
    ],
    certificates=[],
    projects=[
        ProjectItem(
            name="Internal ERP Portal",
            description="Cổng thông tin nội bộ doanh nghiệp.",
            technologies=["Python", "PostgreSQL", "Flask"],
        )
    ],
    technologies=["Python", "FastAPI", "PostgreSQL"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Low Match Candidate (Unrelated skills, 0.5 yrs exp, associate degree)
# Expected Score: ~10-30
# ─────────────────────────────────────────────────────────────────────────────
DEMO_CV_LOW = StructuredCv(
    full_name="Phạm Thị Mai",
    email="mai.pham@example.com",
    phone="0901234567",
    career_summary="Fresher UI Designer mới tốt nghiệp cao đẳng chuyên ngành Thiết kế Đồ họa.",
    skills=["HTML", "CSS", "Figma", "Adobe Photoshop", "Illustrator"],
    work_experience=[
        WorkExperienceItem(
            company="Creative Studio",
            job_title="Design Intern",
            start_date="2023-06",
            end_date="2023-12",
            duration="06/2023 - 12/2023",
            years_of_experience=0.5,
            description="Thiết kế giao diện landing page và banner quảng cáo.",
        )
    ],
    education=[
        EducationItem(
            institution="Cao đẳng Thực hành",
            degree="Cao đẳng",
            field_of_study="Thiết kế Đồ họa",
            graduation_year="2023",
        )
    ],
    certificates=[],
    projects=[
        ProjectItem(
            name="Brand Identity Pack",
            description="Bộ nhận diện thương hiệu cho chuỗi cà phê.",
            technologies=["Figma", "Photoshop"],
        )
    ],
    technologies=["HTML", "CSS", "Figma"],
)
