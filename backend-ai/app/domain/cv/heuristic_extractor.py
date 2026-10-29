import datetime
import re

from app.contracts.cv import EducationItem, ProjectItem, StructuredCv, WorkExperienceItem

# Canonical known technical keywords to search for across text
KNOWN_TECH_KEYWORDS: list[str] = [
    # .NET ecosystem
    "ASP.NET Core",
    "ASP.NET",
    "Entity Framework Core",
    "Entity Framework",
    "EF Core",
    "LINQ",
    ".NET Core",
    ".NET",
    "C#",
    "Blazor",
    "WPF",
    "xUnit",
    "NUnit",
    # Databases & Caching
    "PostgreSQL",
    "SQL Server",
    "MySQL",
    "MongoDB",
    "Redis",
    "Oracle",
    "SQLite",
    "Elasticsearch",
    "Cassandra",
    # DevOps & Infrastructure
    "Docker Compose",
    "Docker",
    "Kubernetes",
    "GitHub Actions",
    "GitLab CI",
    "GitLab",
    "Azure DevOps",
    "Azure",
    "AWS",
    "GCP",
    "Terraform",
    "Ansible",
    "Jenkins",
    "Git",
    "Linux",
    "Nginx",
    "CI/CD",
    # Architecture & Practices
    "Microservices",
    "RESTful API",
    "REST APIs",
    "REST API",
    "Clean Architecture",
    "CQRS",
    "Dependency Injection",
    "Repository Pattern",
    "Domain-Driven Design",
    "Unit Testing",
    "Integration Testing",
    "Swagger",
    "Postman",
    "Kafka",
    "RabbitMQ",
    # Other Languages & Web Frameworks
    "Python",
    "FastAPI",
    "Django",
    "Flask",
    "Java",
    "Spring Boot",
    "JavaScript",
    "TypeScript",
    "ReactJS",
    "React",
    "Node.js",
    "Next.js",
    "VueJS",
    "Vue",
    "Angular",
    "Golang",
    "Go",
    "PHP",
    "Laravel",
    "HTML",
    "CSS",
    "TailwindCSS",
]

# Section headers patterns
SECTION_SUMMARY_REGEX = re.compile(
    r"(?:^|\n)\s*(?:PROFESSIONAL\s+SUMMARY|CAREER\s+SUMMARY|SUMMARY|TÓM\s+TẮT|MỤC\s+TIÊU|GIỚI\s+THIỆU)\s*[:\-\n]",
    re.IGNORECASE,
)
SECTION_SKILLS_REGEX = re.compile(
    r"(?:^|\n)\s*(?:CORE\s+SKILLS|TECHNICAL\s+SKILLS|SKILLS|KỸ\s+NĂNG\s+CHUYÊN\s+MÔN|KỸ\s+NĂNG)\s*[:\-\n]",
    re.IGNORECASE,
)
SECTION_EXPERIENCE_REGEX = re.compile(
    r"(?:^|\n)\s*(?:PROFESSIONAL\s+EXPERIENCE|WORK\s+EXPERIENCE|EXPERIENCE|KINH\s+NGHIỆM\s+LÀM\s+VIỆC|KINH\s+NGHIỆM)\s*[:\-\n]",
    re.IGNORECASE,
)
SECTION_EDUCATION_REGEX = re.compile(
    r"(?:^|\n)\s*(?:EDUCATION|ACADEMIC\s+BACKGROUND|HỌC\s+VẤN|TRÌNH\s+ĐỘ\s+HỌC\s+VẤN)\s*[:\-\n]",
    re.IGNORECASE,
)
SECTION_PROJECTS_REGEX = re.compile(
    r"(?:^|\n)\s*(?:KEY\s+PROJECTS|PROJECTS|DỰ\s+ÁN\s+TIÊU\s+BIỂU|DỰ\s+ÁN)\s*[:\-\n]",
    re.IGNORECASE,
)
SECTION_CERTIFICATES_REGEX = re.compile(
    r"(?:^|\n)\s*(?:CERTIFICATES|CERTIFICATIONS|CHỨNG\s+CHỈ)\s*[:\-\n]",
    re.IGNORECASE,
)

ALL_SECTION_HEADERS_REGEX = re.compile(
    r"(?:^|\n)\s*(?:PROFESSIONAL\s+SUMMARY|CAREER\s+SUMMARY|SUMMARY|TÓM\s+TẮT|MỤC\s+TIÊU|GIỚI\s+THIỆU|"
    r"CORE\s+SKILLS|TECHNICAL\s+SKILLS|SKILLS|KỸ\s+NĂNG\s+CHUYÊN\s+MÔN|KỸ\s+NĂNG|"
    r"PROFESSIONAL\s+EXPERIENCE|WORK\s+EXPERIENCE|EXPERIENCE|KINH\s+NGHIỆM\s+LÀM\s+VIỆC|KINH\s+NGHIỆM|"
    r"EDUCATION|ACADEMIC\s+BACKGROUND|HỌC\s+VẤN|TRÌNH\s+ĐỘ\s+HỌC\s+VẤN|"
    r"KEY\s+PROJECTS|PROJECTS|DỰ\s+ÁN\s+TIÊU\s+BIỂU|DỰ\s+ÁN|"
    r"CERTIFICATES|CERTIFICATIONS|CHỨNG\s+CHỈ)\s*[:\-\n]",
    re.IGNORECASE,
)


def extract_sections(raw_text: str) -> dict[str, str]:
    """Split text into distinct CV sections based on common headings."""
    matches = list(ALL_SECTION_HEADERS_REGEX.finditer(raw_text))
    sections: dict[str, str] = {}

    if not matches:
        return {"body": raw_text}

    # Header prefix before first section (contains contact info, name, title)
    sections["header"] = raw_text[: matches[0].start()].strip()

    for idx, match in enumerate(matches):
        header_text = match.group(0).strip().lower()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_text)
        content = raw_text[start:end].strip()

        if any(kw in header_text for kw in ["summary", "tóm tắt", "mục tiêu", "giới thiệu"]):
            sections["summary"] = content
        elif any(kw in header_text for kw in ["skill", "kỹ năng"]):
            sections["skills"] = content
        elif any(kw in header_text for kw in ["experience", "kinh nghiệm"]):
            sections["experience"] = content
        elif any(kw in header_text for kw in ["education", "học vấn"]):
            sections["education"] = content
        elif any(kw in header_text for kw in ["project", "dự án"]):
            sections["projects"] = content
        elif any(kw in header_text for kw in ["cert", "chứng chỉ"]):
            sections["certificates"] = content

    return sections


def extract_full_name(raw_text: str, header_text: str) -> str | None:
    """Extract candidate full name from header or initial lines."""
    # 1. Look for explicit label
    m = re.search(r"(?:họ\s*(?:và)?\s*tên|full\s*name|name)\s*[:\-]\s*([^\n\r|]+)", raw_text, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        if 2 <= len(name.split()) <= 6 and len(name) <= 100:
            return name

    # 2. Look at first non-empty line of document or header
    source = header_text if header_text else raw_text
    lines = [line.strip() for line in source.split("\n") if line.strip()]
    for line in lines[:3]:
        # Filter out headers, emails, phones, URLs
        if any(char in line for char in ["@", "http", "www.", "/", "|", "•", "*"]):
            continue
        if re.search(r"\b(?:curriculum|vitae|resume|cv)\b", line, re.IGNORECASE):
            continue
        words = line.split()
        if 2 <= len(words) <= 6 and len(line) <= 60:
            return line

    return None


def extract_email(raw_text: str) -> str | None:
    """Extract email address via regex."""
    m = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", raw_text)
    return m.group(0).strip() if m else None


def extract_phone(raw_text: str) -> str | None:
    """Extract phone number via regex."""
    m = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", raw_text)
    if m:
        phone = m.group(0).strip()
        # Ensure at least 9 digits
        digits = [c for c in phone if c.isdigit()]
        if len(digits) >= 9:
            return phone
    return None


def extract_skills_heuristically(raw_text: str, skills_section: str = "") -> list[str]:
    """Extract technical skills and keywords from skills section and overall text."""
    found_skills: list[str] = []
    seen_lower: set[str] = set()

    def add_skill(skill: str) -> None:
        clean = skill.strip(" \t\r\n,;:•*l-|()")
        if clean.endswith(".") and not clean.lower().endswith(".net") and not clean.lower().endswith(".js"):
            clean = clean.rstrip(".")
        if not clean or len(clean) > 50:
            return
        lower = clean.lower()
        if lower not in seen_lower:
            seen_lower.add(lower)
            found_skills.append(clean)

    # 1. Parse lines in skills section (often grouped e.g. "Languages: C#, .NET...")
    if skills_section:
        for line in skills_section.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Remove leading bullets like 'l ', '- ', '• '
            line = re.sub(r"^[l\-\*•]\s*", "", line)
            if ":" in line:
                _, content = line.split(":", 1)
            else:
                content = line
            # Split items by comma, semicolon
            for token in re.split(r"[,;]", content):
                token_clean = token.strip()
                # Normalize things like ".NET 6/7/8" -> ".NET"
                if re.search(r"\.net\b", token_clean, re.IGNORECASE):
                    add_skill(".NET")
                elif re.search(r"\bc#\b", token_clean, re.IGNORECASE):
                    add_skill("C#")
                elif token_clean and len(token_clean.split()) <= 4:
                    add_skill(token_clean)

    # 2. Check for known keywords:
    # If skills_section is present and produced valid skills, scan inside skills_section.
    # Otherwise, scan raw_text, but strictly filter out lines indicating lack of experience or low-match notes.
    negation_indicators = [
        "no experience",
        "no professional experience",
        "not familiar",
        "without experience",
        "chưa có kinh nghiệm",
        "không có kinh nghiệm",
        "chưa từng làm",
        "low-match",
        "lack of",
        "no hands-on",
        "chưa nắm vững",
        "không thành thạo",
        "not used",
    ]

    search_target = skills_section if (skills_section and len(found_skills) > 0) else raw_text
    filtered_lines = [
        line for line in search_target.split("\n") if not any(neg in line.lower() for neg in negation_indicators)
    ]
    clean_search_text = "\n".join(filtered_lines)

    for kw in KNOWN_TECH_KEYWORDS:
        escaped = re.escape(kw)
        pattern = rf"(?<![\w#.]){escaped}(?![\w#.])"
        if re.search(pattern, clean_search_text, re.IGNORECASE):
            add_skill(kw)

    return found_skills[:100]


def _calculate_role_years(start_date: str | None, end_date: str | None) -> float:
    """Calculate duration in years from start and end dates (YYYY or YYYY-MM).

    Returns 0.0 if start_date is absent or dates cannot be parsed.
    """
    if not start_date:
        return 0.0

    try:
        if "-" in start_date:
            y_s, m_s = map(int, start_date.split("-")[:2])
        else:
            y_s, m_s = int(start_date), 1

        if end_date:
            if "-" in end_date:
                y_e, m_e = map(int, end_date.split("-")[:2])
            else:
                y_e, m_e = int(end_date), 12
        else:
            now = datetime.datetime.now(datetime.UTC)
            y_e, m_e = now.year, now.month

        months = (y_e - y_s) * 12 + (m_e - m_s)
        if months <= 0:
            return 0.0
        return min(round(months / 12.0, 1), 60.0)
    except (ValueError, TypeError):
        return 0.0


def extract_work_experience(
    raw_text: str = "", experience_section: str = "", header_text: str = ""
) -> list[WorkExperienceItem]:
    """Extract work experience items or construct a sensible representation."""
    _ = raw_text
    items: list[WorkExperienceItem] = []

    # Look for candidate's primary job title in header (e.g. "Senior .NET Backend Engineer")
    primary_title = None
    if header_text:
        lines = [ln.strip() for ln in header_text.split("\n") if ln.strip()]
        technical_roles = ["engineer", "developer", "kỹ sư", "lập trình", "architect", "lead"]
        for line in lines[1:3]:
            lower_line = line.lower()
            if any(term in lower_line for term in technical_roles):
                primary_title = line.split("|")[0].strip()
                break

    if experience_section:
        # Split by blank lines or job headers (not starting with a digit/date)
        split_pattern = r"\n\s*\n|(?<=\n)(?=[^\d\n|]+\|\s*[^\n|]+\n)"
        blocks = [b.strip() for b in re.split(split_pattern, experience_section) if b.strip()]
        for block in blocks:
            lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
            if not lines:
                continue
            first_line = lines[0]
            title = None
            company = ""

            if "|" in first_line:
                parts = [p.strip() for p in first_line.split("|")]
                title = parts[0] if parts[0] else None
                if len(parts) > 1:
                    company = parts[1]
            else:
                title = first_line if first_line else None

            if not title:
                title = primary_title or None

            duration = ""
            start_date = None
            end_date = None
            for ln in lines[1:3]:
                d_match = re.search(
                    r"(\d{2}/\d{4}|\d{4})\s*[-–—]\s*(Present|Hiện tại|\d{2}/\d{4}|\d{4})",  # noqa: RUF001
                    ln,
                    re.IGNORECASE,
                )
                if d_match:
                    duration = d_match.group(0)
                    start_raw = d_match.group(1)
                    end_raw = d_match.group(2)
                    if "/" in start_raw:
                        m, y = start_raw.split("/")
                        start_date = f"{y}-{int(m):02d}"
                    else:
                        start_date = start_raw
                    if "present" not in end_raw.lower() and "hiện tại" not in end_raw.lower():
                        if "/" in end_raw:
                            m, y = end_raw.split("/")
                            end_date = f"{y}-{int(m):02d}"
                        else:
                            end_date = end_raw
                    break

            desc = "\n".join(lines[2:]) if len(lines) > 2 else block
            years_calc = _calculate_role_years(start_date, end_date)
            items.append(
                WorkExperienceItem(
                    job_title=title,
                    company=company,
                    duration=duration,
                    start_date=start_date,
                    end_date=end_date,
                    years_of_experience=years_calc,
                    description=desc[:2000],
                )
            )

    return items


def extract_education(education_section: str = "") -> list[EducationItem]:
    """Extract education background."""
    items: list[EducationItem] = []
    if not education_section:
        return items

    lines = [ln.strip() for ln in education_section.split("\n") if ln.strip()]
    for line in lines:
        degree = None
        institution = ""
        field_of_study = ""
        grad_year = None

        if re.search(r"\b(?:bachelor|master|engineer|kỹ sư|cử nhân|tiến sĩ|phd)\b", line, re.IGNORECASE):
            degree = line.split("|")[0].strip() if "|" in line else line
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) > 1:
                institution = parts[1]

        y_match = re.search(r"\b(20\d{2}|19\d{2})\b", line)
        if y_match:
            grad_year = y_match.group(1)

        if degree or institution:
            items.append(
                EducationItem(
                    degree=degree,
                    institution=institution,
                    field_of_study=field_of_study,
                    graduation_year=grad_year,
                )
            )

    return items


def extract_projects(projects_section: str = "", skills: list[str] | None = None) -> list[ProjectItem]:
    """Extract projects from project section."""
    items: list[ProjectItem] = []
    if not projects_section:
        return items

    blocks = [b.strip() for b in re.split(r"\n\s*\n", projects_section) if b.strip()]
    for block in blocks:
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        name = lines[0].strip(" -•*")
        if not name:
            continue
        desc = "\n".join(lines[1:]) if len(lines) > 1 else lines[0]
        # Match technologies in this block
        proj_techs = [s for s in (skills or []) if s.lower() in block.lower()]
        items.append(
            ProjectItem(
                name=name[:200],
                description=desc[:2000],
                technologies=proj_techs[:20],
            )
        )

    return items


def extract_structured_cv_heuristically(raw_text: str) -> StructuredCv:
    """
    Perform end-to-end rule-based extraction of StructuredCv from untrusted raw CV text.
    Enables accurate, deterministic offline parsing when LLM_PROVIDER=mock.
    """
    sections = extract_sections(raw_text)
    header = sections.get("header", "")
    summary = sections.get("summary", "")
    skills_sec = sections.get("skills", "")
    exp_sec = sections.get("experience", "")
    edu_sec = sections.get("education", "")
    proj_sec = sections.get("projects", "")

    full_name = extract_full_name(raw_text, header)
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    skills = extract_skills_heuristically(raw_text, skills_sec)
    work_exp = extract_work_experience(raw_text, exp_sec, header)
    education = extract_education(edu_sec)
    projects = extract_projects(proj_sec, skills)

    # If summary section is empty, use first few lines or fallback
    career_summary = summary.strip() if summary else None
    if not career_summary and header:
        career_summary = header.strip()[:1000]

    return StructuredCv(
        full_name=full_name,
        email=email,
        phone=phone,
        career_summary=career_summary,
        skills=skills,
        work_experience=work_exp,
        education=education,
        certificates=[],
        projects=projects,
        technologies=skills,
    )
