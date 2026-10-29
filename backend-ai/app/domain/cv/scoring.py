"""Deterministic CV quality scoring and structural evaluation."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CvQualityEvaluation:
    """Outcome of deterministic CV structural scoring."""

    cv_score: int
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)


def evaluate_cv_quality(cv_dict: dict[str, Any]) -> CvQualityEvaluation:
    """
    Compute explainable, deterministic quality score (0-100) for a CV based on completeness.

    Scoring rubric:
    - Contact information completeness: up to 15 pts
    - Career summary clarity: up to 10 pts
    - Technical and domain skills: up to 20 pts
    - Work experience detail and history: up to 25 pts
    - Educational qualifications: up to 15 pts
    - Key projects & certifications: up to 15 pts
    """
    score = 0
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []

    # 1. Contact Info (15 pts)
    contact_pts = 0
    has_name = bool(cv_dict.get("full_name"))
    has_email = bool(cv_dict.get("email"))
    has_phone = bool(cv_dict.get("phone"))

    if has_name:
        contact_pts += 5
    if has_email:
        contact_pts += 5
    if has_phone:
        contact_pts += 5

    score += contact_pts
    if contact_pts == 15:
        strengths.append("Thông tin liên hệ đầy đủ và rõ ràng (Họ tên, Email, Số điện thoại).")
    else:
        weaknesses.append("Thiếu một số thông tin liên hệ cơ bản.")
        suggestions.append("Bổ sung đầy đủ họ tên, email chuyên nghiệp và số điện thoại liên hệ.")

    # 2. Career Summary (10 pts)
    summary = str(cv_dict.get("career_summary") or "").strip()
    if len(summary) >= 50:
        score += 10
        strengths.append("Có phần tóm tắt mục tiêu / tổng quan sự nghiệp súc tích và định hướng rõ ràng.")
    elif len(summary) > 0:
        score += 5
        suggestions.append("Mở rộng phần tóm tắt sự nghiệp (khoảng 3-4 câu) để nêu bật thế mạnh và mục tiêu.")
    else:
        weaknesses.append("Chưa có phần tóm tắt mục tiêu / tổng quan sự nghiệp (Career Summary).")
        suggestions.append(
            "Thêm phần Tóm tắt sự nghiệp (Professional Summary) ở đầu CV để gây ấn tượng với nhà tuyển dụng."
        )

    # 3. Skills (20 pts)
    skills = cv_dict.get("skills") or []
    if len(skills) >= 8:
        score += 20
        strengths.append(f"Danh mục kỹ năng phong phú và đa dạng ({len(skills)} kỹ năng được liệt kê).")
    elif len(skills) >= 4:
        score += 12
        suggestions.append("Bổ sung thêm các công nghệ, công cụ hoặc kỹ năng mềm liên quan đến vị trí ứng tuyển.")
    elif len(skills) > 0:
        score += 6
        weaknesses.append("Số lượng kỹ năng liệt kê còn khá ít.")
        suggestions.append("Liệt kê chi tiết hơn các kỹ năng chuyên môn cốt lõi mà bạn thành thạo.")
    else:
        weaknesses.append("Chưa liệt kê danh sách kỹ năng chuyên môn.")
        suggestions.append("Tạo mục Kỹ năng (Skills) rõ ràng để hệ thống và nhà tuyển dụng dễ dàng đánh giá.")

    # 4. Work Experience (25 pts)
    experiences = cv_dict.get("work_experience") or []
    if len(experiences) >= 2:
        score += 25
        strengths.append("Lịch sử làm việc phong phú với nhiều kinh nghiệm thực tế liên quan.")
    elif len(experiences) == 1:
        score += 15
        strengths.append("Có kinh nghiệm làm việc thực tế được trình bày cụ thể.")
    else:
        weaknesses.append("Chưa có hoặc chưa liệt kê rõ ràng kinh nghiệm làm việc.")
        suggestions.append("Liệt kê các công việc, dự án thực tập hoặc hoạt động đã tham gia theo thứ tự thời gian.")

    # 5. Education (15 pts)
    education = cv_dict.get("education") or []
    if len(education) >= 1:
        score += 15
        strengths.append("Thông tin học vấn và bằng cấp được trình bày đầy đủ.")
    else:
        weaknesses.append("Thiếu thông tin về học vấn hoặc bằng cấp.")
        suggestions.append("Bổ sung thông tin trường đại học/cao đẳng, chuyên ngành và năm tốt nghiệp.")

    # 6. Projects & Certificates (15 pts)
    projects = cv_dict.get("projects") or []
    certs = cv_dict.get("certificates") or []
    proj_pts = 0
    if len(projects) >= 2:
        proj_pts += 10
        strengths.append("Có các dự án thực tế tiêu biểu minh chứng cho năng lực thực hành.")
    elif len(projects) == 1:
        proj_pts += 6
        suggestions.append("Mô tả thêm 1-2 dự án tiêu biểu kèm kết quả định lượng đạt được.")

    if len(certs) >= 1:
        proj_pts += 5
        strengths.append("Có chứng chỉ nghề nghiệp / ngoại ngữ bổ trợ giá trị.")
    else:
        suggestions.append("Cập nhật các chứng chỉ công nghệ hoặc ngoại ngữ (nếu có) để tăng tính cạnh tranh.")

    score += proj_pts

    # Ensure score bounded between 0 and 100
    final_score = max(0, min(100, score))

    return CvQualityEvaluation(
        cv_score=final_score,
        strengths=strengths,
        weaknesses=weaknesses,
        improvement_suggestions=suggestions,
    )
