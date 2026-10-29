"""Conservative EN/VI IT-JD preparation. No LLM, CV or labels determine weights.

shortcut: bounded vocabulary/grammar, use reviewed extraction data before adding
an NLP parser for arbitrary JDs; unsupported clauses block the final score.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

POLICY = {"version": "jd-priority-v1", "weights": {"mandatory": 3, "standard": 2, "preferred": 1},
          "default_priority": "standard", "default_skill_level": "basic",
          "experience_word_level": "professional", "duration_scope": "paid_role"}
SKILLS = {
    "Python": ["python", "py"], "Node.js": ["node.js", "nodejs"],
    "PostgreSQL": ["postgresql", "postgres"], "Redis": ["redis"], "Docker": ["docker"], "Java": ["java"],
    "JavaScript": ["javascript", "js"], "TypeScript": ["typescript", "ts"],
    "React": ["react", "reactjs", "react.js"], "CSS": ["css"], "HTML": ["html"], "Jest": ["jest"],
    "pytest": ["pytest"], "Playwright": ["playwright"], "Selenium": ["selenium"],
    "Postman": ["postman"], "SQL": ["sql"], "Linux": ["linux"],
    "Kubernetes": ["kubernetes", "k8s"], "AWS": ["aws", "amazon web services"],
    "Terraform": ["terraform"], "GitHub Actions": ["github actions"],
    "pandas": ["pandas"], "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "Apache Spark": ["apache spark", "spark"], "Airflow": ["airflow"],
    "Kotlin": ["kotlin"], "Android": ["android"], "Swift": ["swift"], "iOS": ["ios"],
    "React Native": ["react native", "react-native", "reactnative"], "Git": ["git"],
}
ROLES = {
    "backend developer": ["backend developer", "backend engineer", "lap trinh vien backend"],
    "frontend developer": ["frontend developer", "frontend engineer", "lap trinh vien frontend"],
    "QA engineer": ["qa engineer", "qa", "tester", "kiem thu vien"],
    "DevOps engineer": ["devops engineer", "devops", "ky su devops"],
    "data/ML engineer": ["data/ml engineer", "data engineer", "ml engineer", "machine learning engineer", "ky su du lieu"],
    "mobile developer": ["mobile developer", "mobile engineer", "lap trinh vien mobile"],
}
MANDATORY = r"\b(?:must(?: have)?|mandatory|required|essential|bat buoc)\b"
PREFERRED = r"\b(?:preferred|preferably|optional|nice to have|nice-to-have|a plus|an advantage|uu tien|loi the|diem cong)\b"
NEGATIVE = r"\b(?:not required|not mandatory|khong yeu cau|khong bat buoc)\b"
DURATION = r"(?P<number>\d+(?:[.,]\d+)?)\s*\+?\s*(?P<unit>years?|months?|nam|thang)\b"
GRAMMAR = set("""a an the and with of in on for to or is are be have has having use used using
knowledge understanding foundational basic foundation familiarity familiar skills skill required requirements
must mandatory essential preferred preferably optional nice plus advantage experience experienced professional
paid employment work working commercial practical hands hands-on independent project projects demonstrating
apply applying applied at least minimum more total totaling minimum years year months month position role
proficiency proficient solid good strong ability need needed includes include candidates candidate should
know technology technologies tools tool expertise only
but during level
co biet hieu kien thuc hieu biet co ban thanh thao ky nang su dung va ve voi bang
kinh nghiem lam viec trong cong viec tra luong chuyen mon thuc hanh du an doc lap
yeu cau bat buoc can ung vien uu tien loi the diem cong la mot it nhat toi thieu tro len
nam thang vi tri hoac khong chi tiet kiem thu vien ky su du lieu lap trinh vien o nhung
""".split())


def fold(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "D"))
                   if not unicodedata.combining(c)).lower()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def detect_skills(text):
    candidates = []
    for skill, aliases in SKILLS.items():
        for alias in aliases:
            for m in re.finditer(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", text, flags=re.I):
                candidates.append((m.start(), m.end(), skill))
    selected = []
    for start, end, skill in sorted(candidates, key=lambda x: (-(x[1] - x[0]), x[0])):
        if not any(start < other_end and end > other_start for other_start, other_end, _ in selected):
            selected.append((start, end, skill))
    return sorted(selected)


def detect_roles(text):
    value = fold(text)
    return {role for role, aliases in ROLES.items() if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", value) for alias in aliases)}


def section_type(text):
    value = fold(text).strip(" :#-*•\t")
    if value in {"requirements", "qualifications", "yeu cau", "yeu cau ung vien", "candidate requirements", "technical skills", "job requirements"}:
        return "standard"
    if value in {"must have", "must-have", "required skills", "mandatory", "bat buoc", "yeu cau bat buoc"}:
        return "mandatory"
    if value in {"preferred", "preferred skills", "preferred qualifications", "nice to have", "nice-to-have", "uu tien", "yeu cau uu tien"}:
        return "preferred"
    if value in {"benefits", "quyen loi", "phuc loi", "salary", "muc luong", "about us", "ve chung toi",
                 "responsibilities", "job description", "mo ta cong viec", "lien he", "contact", "how to apply", "cach ung tuyen"}:
        return "ignore"
    return None


def clauses(text):
    """Source spans remain offsets in the original JD, including Vietnamese text."""
    for line in re.finditer(r"[^\r\n]+", text):
        raw = line.group()
        content_start = len(raw) - len(raw.lstrip(" \t-*•#"))
        numbered = re.match(r"\d+[.)]\s+", raw[content_start:])
        if numbered:
            content_start += numbered.end()
        cleaned = raw[content_start:]
        # Headers may be alone or followed by inline content, e.g. 'Yêu cầu: Python'.
        header, separator, rest = cleaned.partition(":")
        section = section_type(header) if separator else section_type(cleaned)
        if section:
            yield {"section": section}
            if not separator or not rest.strip():
                continue
            content_start += len(header) + 1
            cleaned = raw[content_start:]
        for part in re.finditer(r"[^;]+", cleaned):
            for sentence in re.finditer(r".+?(?:[.!?](?=\s+[A-ZÀ-Ỹ])|$)", part.group()):
                start = line.start() + content_start + part.start() + sentence.start()
                end = line.start() + content_start + part.start() + sentence.end()
                while start < end and text[start].isspace():
                    start += 1
                while end > start and text[end - 1].isspace():
                    end -= 1
                if start < end:
                    yield {"start": start, "end": end, "text": text[start:end]}


class JDPreparationError(ValueError):
    def __init__(self, profile):
        super().__init__("JD có điều kiện chưa xử lý được; chưa tính điểm tổng. Xem jd_profile.unresolved.")
        self.profile = profile


def prepare_jd(jd_text, job_title=""):
    if not isinstance(jd_text, str) or not jd_text.strip() or len(jd_text) > 20_000:
        raise ValueError("jd_text phải có nội dung, tối đa 20.000 ký tự")
    if not isinstance(job_title, str) or len(job_title) > 200:
        raise ValueError("job_title phải là chuỗi tối đa 200 ký tự")
    criteria, unresolved, ignored, warnings = {}, [], [], []
    section = "standard"

    def issue(clause, code, message):
        unresolved.append({**clause, "code": code, "message": message})

    for clause in clauses(jd_text):
        if "section" in clause:
            section = clause["section"]
            continue
        text, value = clause["text"], fold(clause["text"])
        if job_title and value.strip(" .:") == fold(job_title).strip(" .:"):
            ignored.append({**clause, "reason": "job_title"})
            continue
        if section == "ignore":
            ignored.append({**clause, "reason": "non_requirement_section"})
            continue
        negative = re.search(NEGATIVE, value)
        preferred = re.search(PREFERRED, value)
        mandatory = re.search(MANDATORY, re.sub(NEGATIVE, "", value))
        if negative and mandatory:
            issue(clause, "mixed_negation", "Câu chứa cả yêu cầu bắt buộc và điều kiện không bắt buộc; cần tách riêng.")
            continue
        if negative and not preferred:
            ignored.append({**clause, "reason": "explicitly_not_required"})
            continue
        if mandatory and preferred:
            issue(clause, "mixed_priority", "Tách riêng yêu cầu bắt buộc và ưu tiên trong câu này.")
            continue
        priority = "preferred" if preferred else "mandatory" if mandatory else section
        origin = "explicit_clause" if preferred or mandatory else "section" if section != "standard" else "default_policy"
        skills = detect_skills(text)
        if negative and preferred and len(skills) > 1:
            issue(clause, "mixed_negation", "Câu phủ định/ưu tiên chứa nhiều kỹ năng; cần tách rõ phạm vi từng điều kiện.")
            continue
        # Alternatives cannot be turned into independent AND requirements.
        if re.search(r"\b(?:or|hoac)\b|and/or", re.sub(r"\bor more\b", "", value)) or (len(skills) > 1 and "/" in text):
            issue(clause, "alternative_or_group", "Điều kiện lựa chọn/nhóm cần được chuẩn hóa riêng, không tách thành các yêu cầu AND.")
            continue
        if re.search(r"\b(?:expert|advanced|mastery|chuyen sau|nang cao|thanh thao|proficient|proficiency)\b|>=|<=|\b(?:less than|more than|duoi|hon)\s+\d|\d\s*[-–]\s*\d", value):
            issue(clause, "unsupported_constraint", "Điều kiện mức độ hoặc khoảng định lượng chưa nằm trong rubric v1.")
            continue
        durations = list(re.finditer(DURATION, value))
        if durations and skills:
            issue(clause, "skill_specific_duration", "Số năm theo từng kỹ năng chưa được classifier v1 huấn luyện; không chuyển thành số năm toàn vai trò.")
            continue
        if len(durations) > 1 or (re.search(r"\d", value) and not durations):
            issue(clause, "unsupported_number", "Không bỏ qua điều kiện số lượng/chứng chỉ/phiên bản kỹ thuật.")
            continue
        if durations:
            roles = detect_roles(text) or detect_roles(job_title)
            number = float(durations[0]["number"].replace(",", "."))
            months = number * (12 if durations[0]["unit"] in {"year", "years", "nam"} else 1)
            if len(roles) != 1 or not months.is_integer() or not 1 <= months <= 600:
                issue(clause, "ambiguous_role_or_duration", "Cần một vai trò rõ ràng và số tháng kinh nghiệm dương, nguyên.")
                continue
            role = next(iter(roles))
            kind, subject, level = "experience", role, "paid_role_months"
            normalized = f"Paid experience in {role} totaling {int(months)} months or more."
            # Do not normalize 'internship only' or 'maximum X years' as a minimum.
            residual = value[:durations[0].start()] + " " + value[durations[0].end():]
            for aliases in ROLES.values():
                for alias in sorted(aliases, key=len, reverse=True):
                    residual = residual.replace(alias, " ")
            key = (kind, role, int(months))
            level_origin = "explicit_paid" if re.search(r"\b(?:paid|tra luong)\b", value) else "policy_experience_means_paid"
        elif skills:
            if len(skills) > 1 and re.search(r"\b(?:paid|professional|tra luong)\b", value) and re.search(r"\b(?:project|projects|du an)\b", value):
                issue(clause, "mixed_skill_levels", "Nhiều kỹ năng có thể gắn với các mức kinh nghiệm khác nhau; cần tách riêng.")
                continue
            if re.search(r"\b(?:paid|professional|commercial|employment|tra luong)\b", value):
                level, level_origin = "professional", "explicit"
            elif re.search(r"\b(?:project|projects|practical|hands-on|du an|thuc hanh)\b", value):
                level, level_origin = "practical", "explicit"
            elif re.search(r"\b(?:experience|experienced|kinh nghiem)\b", value):
                level, level_origin = "professional", "policy_experience_means_paid"
            else:
                level = "basic"
                level_origin = "explicit" if re.search(r"\b(?:knowledge|understanding|familiar|foundational|basic|kien thuc|co ban|biet)\b", value) else "default_policy"
            residual = text
            for start, end, _ in reversed(skills):
                residual = residual[:start] + " " + residual[end:]
            residual = fold(residual)
            kind = "skill"
        else:
            issue(clause, "unrecognized_requirement", "Chưa nhận diện được yêu cầu trong phạm vi kỹ năng/vai trò đã huấn luyện.")
            continue
        residual = re.sub(NEGATIVE, " ", residual)
        unknown = sorted(set(re.findall(r"[a-z][a-z0-9]*", residual)) - GRAMMAR)
        if unknown:
            issue(clause, "unmodeled_terms", "Từ/điều kiện chưa hỗ trợ: " + ", ".join(unknown))
            continue
        if level_origin != "explicit" and level_origin != "explicit_paid":
            warnings.append({"code": level_origin, "source": clause, "message": "Mức yêu cầu được suy ra theo chính sách, không phải dữ kiện năng lực của ứng viên."})
        if origin == "default_policy":
            warnings.append({"code": "default_weight", "source": clause, "message": "JD không nêu ưu tiên; dùng weight=2 theo chính sách."})
        items = [(skill, ("skill", skill, level)) for _, _, skill in skills] if kind == "skill" else [(subject, key)]
        for subject, key in items:
            if kind == "skill":
                normalized = {"basic": f"Foundational understanding of {subject}.",
                              "practical": f"Project-level experience applying {subject}.",
                              "professional": f"Evidence of {subject} used during paid employment."}[level]
            if key in criteria:
                item = criteria[key]
                if item["priority"] != priority and "default_policy" not in {item["priority_origin"], origin}:
                    issue(clause, "conflicting_priority", f"Mâu thuẫn ưu tiên cho {subject}; không tự gộp hai mức rõ ràng khác nhau.")
                if POLICY["weights"][priority] > item["weight"]:
                    item.update(priority=priority, priority_origin=origin, weight=POLICY["weights"][priority])
                item["sources"].append(clause)
            else:
                criteria[key] = {"id": "req-" + digest(key)[:12], "text": normalized, "weight": POLICY["weights"][priority],
                                 "kind": kind, "subject": subject, "level": level, "level_origin": level_origin,
                                 "priority": priority, "priority_origin": origin, "sources": [clause]}
    ordered = [criteria[k] for k in sorted(criteria)]
    if len(ordered) > 20:
        unresolved.append({"code": "too_many_requirements", "message": "Có hơn 20 yêu cầu; không cắt bỏ để chấm một phần."})
    if not ordered:
        unresolved.append({"code": "no_requirements", "message": "Chưa có yêu cầu nào có thể đánh giá."})
    profile = {
        "schema": "prepared-jd-v1", "policy": json.loads(json.dumps(POLICY)), "job_title": job_title, "jd_text": jd_text,
        "jd_sha256": hashlib.sha256(jd_text.encode()).hexdigest(),
        "parser_sha256": hashlib.sha256(Path(__file__).read_text(encoding="utf-8").replace("\r\n", "\n").encode()).hexdigest(),
        "status": "needs_review" if unresolved else "ready", "criteria": ordered,
        "requirements": [{k: item[k] for k in ("id", "text", "weight")} for item in ordered],
        "warnings": warnings, "unresolved": unresolved, "ignored": ignored,
    }
    profile["profile_id"] = "jd-" + digest(profile)
    return profile


def resolve_input(sample):
    """Exactly one source of criteria; never allow client overrides on a raw JD."""
    sources = [key for key in ("requirements", "jd_text", "job_profile") if sample.get(key) is not None]
    if len(sources) != 1:
        raise ValueError("Truyền đúng một trong jd_text, job_profile hoặc requirements; không trộn weight tự nhập với JD thô")
    if sample.get("job_title") is not None and sources[0] != "jd_text":
        raise ValueError("job_title chỉ dùng cùng jd_text; job_profile đã lưu tiêu đề riêng")
    profile = None
    if sources[0] == "jd_text":
        profile = prepare_jd(sample["jd_text"], sample.get("job_title") or "")
    elif sources[0] == "job_profile":
        supplied = sample["job_profile"]
        if not isinstance(supplied, dict):
            raise ValueError("job_profile phải là object từ /jobs/prepare")
        profile = prepare_jd(supplied.get("jd_text"), supplied.get("job_title", ""))
        if supplied != profile:
            raise ValueError("job_profile đã đổi hoặc parser/policy khác phiên bản; cần chuẩn bị JD thành phiên bản mới")
    if profile and profile["status"] != "ready":
        raise JDPreparationError(profile)
    normalized = {"sample_id": sample.get("sample_id", "new-cv"), "cv_text": sample.get("cv_text"),
                  "requirements": profile["requirements"] if profile else sample["requirements"]}
    return normalized, profile
