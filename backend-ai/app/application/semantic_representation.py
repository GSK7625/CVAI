"""
Semantic text representation builders for CVs and Job Postings.

PRIVACY & PII HANDLING POLICY:
- Dedicated candidate identity fields (full_name, email, phone) are strictly excluded.
- Free-text fields are deterministically sanitized to redact obvious email addresses
  ([EMAIL_REDACTED]) and phone numbers ([PHONE_REDACTED]).
- Arbitrary person-name redaction from all free-text fields is NOT claimed or guaranteed
  without full Named Entity Recognition (NER).
"""

from app.application.text_sanitization import sanitize_semantic_text
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob

__all__ = [
    "build_cv_semantic_text",
    "build_job_semantic_text",
    "sanitize_semantic_text",
]


def build_cv_semantic_text(cv: StructuredCv) -> str:
    """
    Construct a sanitized, privacy-minimized semantic text representation of a candidate CV.

    STRICT PII EXCLUSIONS:
    - cv.full_name is NEVER included.
    - cv.email is NEVER included.
    - cv.phone is NEVER included.
    - Any candidate identifiers are NEVER included.

    INCLUDED SECTIONS (All free-text strings pass through sanitize_semantic_text):
    - Career summary (sanitized)
    - Technical skills and technologies (sanitized)
    - Work experience (roles, companies, duration, sanitized descriptions)
    - Education background (degrees, institutions, fields of study - sanitized)
    - Projects (names, sanitized descriptions, technologies - sanitized)
    - Certificates (sanitized)
    """
    parts: list[str] = []

    # 1. Career summary
    clean_summary = sanitize_semantic_text(cv.career_summary)
    if clean_summary:
        parts.append(f"Tóm tắt sự nghiệp: {clean_summary}")

    # 2. Skills and technologies
    raw_skills = cv.skills + cv.technologies
    sanitized_skills = list(dict.fromkeys(sanitize_semantic_text(s) for s in raw_skills if s and s.strip()))
    sanitized_skills = [s for s in sanitized_skills if s]
    if sanitized_skills:
        parts.append(f"Kỹ năng chuyên môn: {', '.join(sanitized_skills)}")

    # 3. Work experience
    if cv.work_experience:
        exp_lines: list[str] = []
        for exp in cv.work_experience:
            clean_title = sanitize_semantic_text(exp.job_title)
            line_parts = [clean_title] if clean_title else []
            clean_company = sanitize_semantic_text(exp.company)
            if clean_company:
                line_parts.append(f"tại {clean_company}")
            if exp.years_of_experience > 0:
                line_parts.append(f"({exp.years_of_experience:.1f} năm)")
            clean_desc = sanitize_semantic_text(exp.description)
            if clean_desc:
                line_parts.append(f"- {clean_desc}")
            if line_parts:
                exp_lines.append(" ".join(line_parts))
        if exp_lines:
            parts.append("Kinh nghiệm làm việc:\n" + "\n".join(exp_lines))

    # 4. Education
    if cv.education:
        edu_lines: list[str] = []
        for edu in cv.education:
            edu_parts = []
            clean_degree = sanitize_semantic_text(edu.degree)
            if clean_degree:
                edu_parts.append(clean_degree)
            clean_field = sanitize_semantic_text(edu.field_of_study)
            if clean_field:
                edu_parts.append(f"ngành {clean_field}")
            clean_inst = sanitize_semantic_text(edu.institution)
            if clean_inst:
                edu_parts.append(f"tại {clean_inst}")
            if edu_parts:
                edu_lines.append(" ".join(edu_parts))
        if edu_lines:
            parts.append("Học vấn: " + "; ".join(edu_lines))

    # 5. Projects
    if cv.projects:
        proj_lines: list[str] = []
        for proj in cv.projects:
            clean_name = sanitize_semantic_text(proj.name)
            clean_desc = (
                f"- {sanitize_semantic_text(proj.description)}" if proj.description and proj.description.strip() else ""
            )
            clean_techs = [sanitize_semantic_text(t) for t in proj.technologies if t and t.strip()]
            clean_techs = [t for t in clean_techs if t]
            p_tech = f"[Công nghệ: {', '.join(clean_techs)}]" if clean_techs else ""
            line_str = f"{clean_name} {p_tech} {clean_desc}".strip()
            if line_str:
                proj_lines.append(line_str)
        if proj_lines:
            parts.append("Dự án thực tế:\n" + "\n".join(proj_lines))

    # 6. Certificates
    clean_certs = [sanitize_semantic_text(c) for c in cv.certificates if c and c.strip()]
    clean_certs = [c for c in clean_certs if c]
    if clean_certs:
        parts.append(f"Chứng chỉ: {', '.join(clean_certs)}")

    return "\n\n".join(parts)


def build_job_semantic_text(job: StructuredJob) -> str:
    """Construct a sanitized semantic text representation of a Job Posting."""
    parts: list[str] = []

    clean_title = sanitize_semantic_text(job.title)
    if clean_title:
        parts.append(f"Vị trí tuyển dụng: {clean_title}")

    clean_desc = sanitize_semantic_text(job.description)
    if clean_desc:
        parts.append(f"Mô tả công việc:\n{clean_desc}")

    if job.required_skills:
        clean_req = [sanitize_semantic_text(s) for s in job.required_skills if s and s.strip()]
        clean_req = [s for s in clean_req if s]
        if clean_req:
            parts.append(f"Kỹ năng bắt buộc: {', '.join(clean_req)}")

    if job.preferred_skills:
        clean_pref = [sanitize_semantic_text(s) for s in job.preferred_skills if s and s.strip()]
        clean_pref = [s for s in clean_pref if s]
        if clean_pref:
            parts.append(f"Kỹ năng ưu tiên: {', '.join(clean_pref)}")

    if job.minimum_experience_years is not None and job.minimum_experience_years > 0:
        parts.append(f"Yêu cầu kinh nghiệm tối thiểu: {job.minimum_experience_years:.1f} năm")

    clean_edu = sanitize_semantic_text(job.education_requirement)
    if clean_edu:
        parts.append(f"Yêu cầu học vấn: {clean_edu}")

    clean_emp = sanitize_semantic_text(job.employment_type)
    if clean_emp:
        parts.append(f"Hình thức làm việc: {clean_emp}")

    return "\n\n".join(parts)
