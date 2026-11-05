"""EN/VI job preparation, separate from the checksum-frozen model feature parser.

Extract the stated conditions and retain their source. Model support is a separate
decision: recognizing a degree or an approximate duration does not certify a match.
shortcut: rule-based IT EN/VI grammar; extend with reviewed examples before
claiming support for arbitrary industries or full business-task semantics.
"""
from __future__ import annotations

import copy
import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path

from jd_parser import SKILLS as MODEL_SKILLS, ROLES, digest, fold, section_type

POLICY = {"version": "jd-priority-v2", "weights": {"mandatory": 3, "standard": 2, "preferred": 1},
          "default_priority": "standard", "default_skill_level": "basic",
          "experience_word_level": "professional", "duration_scope": "paid_role",
          "score_scope": "recognized_skills_and_experience"}
SKILLS = {**MODEL_SKILLS,
          "Apache Spark": [*MODEL_SKILLS["Apache Spark"], "pyspark"],
          "PyTorch": ["pytorch", "torch"], "TensorFlow": ["tensorflow"], "Keras": ["keras"],
          "NumPy": ["numpy"], "OpenCV": ["opencv"], "YOLO": ["yolo", "yolov8", "yolo11"],
          "Matplotlib": ["matplotlib"], "MLflow": ["mlflow"], "Hugging Face": ["hugging face", "huggingface"],
          "FastAPI": ["fastapi"], "Flask": ["flask"], "Django": ["django"],
          "C#": ["c#", "c sharp"], "C++": ["c++"], ".NET": [".net", "dotnet"],
          "Golang": ["golang"], "Rust": ["rust"], "Vue": ["vue", "vue.js", "vuejs"],
          "Angular": ["angular"], "Spring Boot": ["spring boot"], "MySQL": ["mysql"],
          "MongoDB": ["mongodb"], "Kafka": ["kafka", "apache kafka"], "Azure": ["azure"],
          "GCP": ["gcp", "google cloud"], "Power BI": ["power bi", "powerbi"],
          "Tableau": ["tableau"], "Excel": ["excel"], "Snowflake": ["snowflake"],
          "Databricks": ["databricks"], "dbt": ["dbt"], "GitLab CI": ["gitlab ci"]}
MANDATORY = r"\b(?:must(?: have)?|mandatory|required|essential|bat buoc)\b"
PREFERRED = r"\b(?:preferred|preferably|optional|nice[- ]to[- ]have|a plus|an advantage|uu tien|loi the|diem cong)\b"
NEGATIVE = r"\b(?:not required|not mandatory|no (?:prior )?experience (?:with [^,;]+? )?(?:is )?(?:required|necessary)|khong (?:yeu cau|bat buoc)|khong can(?: co)?)\b"
PROFESSIONAL = r"\b(?:paid|professional|commercial|employment|tra luong|chuyen nghiep)\b"
PRACTICAL = r"\b(?:project|projects|prototype|practical|hands[- ]on|self[- ]directed|du an|thuc hanh)\b"
EXPERIENCE = r"\b(?:experience|experienced|kinh nghiem)\b"
BASIC = r"\b(?:basic|knowledge|familiar|familiarity|understanding|co ban|kien thuc|hieu biet)\b"
ADVANCED = r"\b(?:expert|advanced|mastery|proficient|proficiency|chuyen sau|nang cao|thanh thao)\b"
TASK = r"\b(?:clean|cleaning|preprocess|preprocessing|transform|transforming|write|writing|query|querying|extract|filter|aggregate|train|training|evaluate|build|develop|implement|deploy|maintain|lam sach|tien xu ly|xu ly|truy van|huan luyen|danh gia|xay dung|phat trien|trien khai)\b"
NUMBER = r"\d+(?:[.,]\d+)?"
UNIT = r"years?|months?|nam|thang"
DURATION = re.compile(rf"(?P<a>{NUMBER})\s*(?:\+\s*)?(?:(?P<u1>{UNIT})\s*)?(?:(?:[-–—]|to|den)\s*(?P<b>{NUMBER})\s*)?(?P<unit>{UNIT})\b")
SINGLE_DURATION = re.compile(rf"(?P<a>{NUMBER})\s*\+?\s*(?P<unit>{UNIT})\b")
LEVEL_RANK = {"basic": 0, "practical": 1, "professional": 2}


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        elif not self.hidden and tag in {"br", "p", "li", "div", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden and tag in {"p", "li", "div", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def source_text(text):
    if not re.search(r"</?(?:p|li|ul|ol|div|br|h[1-6]|strong|b|span|script|style)\b", text, re.I):
        return text
    parser = _HTMLText()
    parser.feed(text)
    return "".join(parser.parts)


def detect_skills(text):
    candidates = []
    for skill, aliases in SKILLS.items():
        for alias in aliases:
            for match in re.finditer(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", text, re.I):
                candidates.append((match.start(), match.end(), skill))
    selected = []
    for start, end, skill in sorted(candidates, key=lambda item: (-(item[1] - item[0]), item[0])):
        if not any(start < b and end > a for a, b, _ in selected):
            selected.append((start, end, skill))
    return sorted(selected)


def detect_roles(text):
    value = fold(text)
    roles = {role for role, aliases in ROLES.items()
             if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", value) for alias in aliases)}
    if re.search(r"\b(?:data\s*(?:or|and|/|and/or)\s*(?:ml|machine learning)\s*engineer|ky su (?:du lieu|hoc may))\b", value):
        roles.add("data/ML engineer")
    return sorted(roles)


def _parts(text):
    """Yield source spans and section markers; labels never become skill names."""
    for line in re.finditer(r"[^\r\n]+", text):
        start, end = line.span()
        bullet = re.match(r"\s*(?:[-*•▪●#]+\s*|\d+[.)]\s+)?", line.group())
        start += bullet.end()
        while end > start and text[end - 1].isspace():
            end -= 1
        if start == end:
            continue
        content = text[start:end]
        header, colon, tail = content.partition(":")
        value = fold(header).strip(" *#:")
        section = section_type(header)
        if value in {"responsibilities", "job description", "mo ta cong viec", "what you will do", "nhiem vu"}:
            section = "responsibility"
        if value in {"quyen loi", "benefits", "phuc loi", "salary", "about us", "ve chung toi", "how to apply", "lien he"}:
            section = "ignore"
        if section:
            yield {"section": section}
            if not colon or not tail.strip():
                continue
            start += len(header) + 1
        # A label describes the following criterion, while the source keeps the label.
        for part in re.finditer(r"[^;]+", text[start:end]):
            for sentence in re.finditer(r".+?(?:[.!?](?=\s+[A-ZÀ-Ỹ])|$)", part.group()):
                a = start + part.start() + sentence.start()
                b = start + part.start() + sentence.end()
                while a < b and text[a].isspace():
                    a += 1
                if a < b:
                    yield {"start": a, "end": b, "text": text[a:b]}


def _content(text):
    header, colon, tail = text.partition(":")
    if colon and tail.strip() and not detect_skills(header) and not re.search(r"\d", header):
        return tail.strip()
    return text


def _split_scopes(clause):
    """Split independent levels/priorities, never commas inside task examples."""
    pending = [clause]
    while pending:
        clause = pending.pop()
        text, depth = clause["text"], 0
        for match in re.finditer(r"[()]|,\s*|\s+(?:and|but|va|và|nhưng|nhung)\s+", text, re.I):
            token = match.group()
            if token == "(":
                depth += 1
            elif token == ")":
                depth = max(0, depth - 1)
            elif depth == 0:
                left, right = text[:match.start()], text[match.end():]
                priorities = f"{MANDATORY}|{PREFERRED}|{NEGATIVE}"
                levels = f"{PROFESSIONAL}|{PRACTICAL}|{BASIC}"
                if any(re.search(signals, fold(left)) and re.search(signals, fold(right))
                       for signals in (priorities, levels)):
                    for a, b in ((match.end(), len(text)), (0, match.start())):
                        pending.append({"start": clause["start"] + a, "end": clause["start"] + b, "text": text[a:b]})
                    break
        else:
            yield clause


def _logic(text, skills):
    if len(skills) == 1:
        return {"skill": skills[0][2]}
    # Only parentheses enclosing skills group alternatives; task examples are prose.
    ranges, stack = [], []
    for match in re.finditer(r"[()]", text):
        if match.group() == "(":
            stack.append(match.start())
            if len(stack) > 16:
                raise ValueError("Skill groups nested too deeply")
        elif stack:
            a = stack.pop()
            if any(a < s and e <= match.start() for s, e, _ in skills):
                ranges.append((a, match.start()))
    events = [(a, "skill", skill) for a, _, skill in skills]
    for a, b in ranges:
        events.extend([(a, "(", None), (b, ")", None)])
    for match in re.finditer(r"\band/or\b|\bor\b|\bhoặc\b|\bhoac\b|\band\b|\bva\b|\bvà\b|[,/&]", text, re.I):
        if skills[0][1] <= match.start() < skills[-1][0] and not any(a <= match.start() < b for a, b, _ in skills):
            # Ignore connectors inside parentheses that contain task descriptions only.
            if text[:match.start()].count("(") - text[:match.start()].count(")") > sum(a < match.start() < b for a, b in ranges):
                continue
            value = fold(match.group())
            events.append((match.start(), "or" if value in {"or", "hoac", "/", "and/or"} else "and", None))
    tokens = [(kind, value) for _, kind, value in sorted(events)]
    if re.search(r"\b(?:one of|either|mot trong|it nhat mot)\b", fold(text[:skills[0][0]])):
        tokens = [("or" if kind == "and" else kind, value) for kind, value in tokens]
    # Comma plus 'and' represents one connector; adjacent entity names form a list.
    clean = []
    for token in tokens:
        if clean and clean[-1][0] in {"and", "or"} and token[0] in {"and", "or"}:
            clean[-1] = ("or" if "or" in {clean[-1][0], token[0]} else "and", None)
        else:
            if clean and clean[-1][0] in {"skill", ")"} and token[0] in {"skill", "("}:
                clean.append(("and", None))
            clean.append(token)
    position = 0

    def primary():
        nonlocal position
        if position >= len(clean):
            raise ValueError("Incomplete skill group")
        kind, value = clean[position]
        position += 1
        if kind == "skill":
            return {"skill": value}
        if kind != "(":
            raise ValueError("Ambiguous skill group")
        node = expression("or")
        if position >= len(clean) or clean[position][0] != ")":
            raise ValueError("Unbalanced skill group")
        position += 1
        return node

    def expression(operator):
        nonlocal position
        parse = primary if operator == "and" else lambda: expression("and")
        children = [parse()]
        while position < len(clean) and clean[position][0] == operator:
            position += 1
            children.append(parse())
        return children[0] if len(children) == 1 else {"op": "all" if operator == "and" else "any", "children": children}

    result = expression("or")
    if position != len(clean):
        raise ValueError("Unparsed skill group")
    return result


def logic_skills(node):
    if "skill" in node:
        return [node["skill"]]
    return sorted({skill for child in node["children"] for skill in logic_skills(child)})


def _duration(value):
    matches = list(DURATION.finditer(value)) or list(SINGLE_DURATION.finditer(value))
    if not matches:
        return None
    if len(matches) != 1:
        return {"relation": "ambiguous", "text": " / ".join(match.group() for match in matches)}
    match = matches[0]
    first_unit = match.groupdict().get("u1") or match["unit"]
    a = float(match["a"].replace(",", ".")) * (12 if first_unit in {"year", "years", "nam"} else 1)
    b = match.groupdict().get("b")
    if b:
        b = float(b.replace(",", ".")) * (12 if match["unit"] in {"year", "years", "nam"} else 1)
        return {"relation": "range", "min_months": a, "max_months": b}
    prefix = value[max(0, match.start() - 40):match.start()]
    relation = "minimum"
    for name, pattern in (("approximate", r"\b(?:around|about|approximately|roughly|khoang|xap xi)\s*$"),
                          ("maximum", r"(?:at most|maximum|up to|toi da|khong qua|<=)\s*$"),
                          ("less_than", r"(?:less than|under|duoi|<)\s*$"),
                          ("more_than", r"(?:more than|over|hon|>)\s*$"),
                          ("exact", r"(?:exactly|chinh xac|dung)\s*$")):
        if re.search(pattern, prefix):
            relation = name
            break
    return {"relation": relation, "months": a}


def _level(value, responsibility):
    # Acceptance of projects broadens eligibility even when paid work is also named.
    if re.search(PRACTICAL, value) and re.search(r"\b(?:accepted|acceptable|counts|equivalent|chap nhan|duoc tinh)\b", value):
        return "practical"
    if re.search(PROFESSIONAL, value):
        return "professional"
    if re.search(PRACTICAL, value):
        return "practical"
    if re.search(EXPERIENCE, value):
        return "professional"
    if responsibility or re.search(TASK, value):
        return "practical"
    return "basic"


def prepare_jd(jd_text, job_title=""):
    if not isinstance(jd_text, str) or not jd_text.strip() or len(jd_text) > 20000:
        raise ValueError("jd_text phải có nội dung, tối đa 20.000 ký tự")
    if not isinstance(job_title, str) or len(job_title) > 200:
        raise ValueError("job_title phải là chuỗi tối đa 200 ký tự")
    text = source_text(jd_text)
    criteria, unresolved, ignored, warnings = [], [], [], []
    section = "standard"

    def issue(source, code, message):
        unresolved.append({**source, "code": code, "message": message})

    for part in _parts(text):
        if "section" in part:
            section = part["section"]
            continue
        for source in _split_scopes(part):
            content = _content(source["text"])
            value = fold(content)
            if section == "ignore" or (job_title and value.strip(" .:") == fold(job_title).strip(" .:")):
                ignored.append({**source, "reason": "non_requirement_section"})
                continue
            negative = re.search(NEGATIVE, value)
            preferred = re.search(PREFERRED, value)
            mandatory = re.search(MANDATORY, re.sub(NEGATIVE, "", value))
            if negative and mandatory:
                issue(source, "mixed_negation", "Chưa xác định rõ phạm vi điều kiện không bắt buộc.")
                continue
            if negative and not preferred:
                ignored.append({**source, "reason": "explicitly_not_required"})
                continue
            if mandatory and preferred:
                issue(source, "mixed_priority", "Cần tách rõ yêu cầu bắt buộc và ưu tiên.")
                continue
            priority = "preferred" if preferred else "mandatory" if mandatory else section if section in {"mandatory", "preferred"} else "standard"
            origin = "explicit_clause" if preferred or mandatory else "section" if section in {"mandatory", "preferred"} else "default_policy"
            skills = detect_skills(content)
            duration = _duration(value)
            base = {"weight": POLICY["weights"][priority], "priority": priority, "priority_origin": origin,
                    "sources": [source], "constraints": [], "level": "basic"}
            if re.search(r"\b(?:bachelor|master'?s?|phd|doctorate|degree|cu nhan|thac si|tien si|tot nghiep dai hoc|bang dai hoc)\b", value):
                degree = next((name for name, pattern in (("doctorate", r"phd|doctorate|tien si"), ("master", r"master|thac si"),
                                                          ("bachelor", r"bachelor|cu nhan|dai hoc")) if re.search(pattern, value)), "degree")
                criteria.append({**base, "kind": "education", "subject": degree, "text": content, "level": degree})
                continue
            if re.search(r"\b(?:certified|certification|certificate|chung chi|cissp|pmp)\b", value) and not re.search(r"toeic|ielts|toefl", value):
                criteria.append({**base, "kind": "certification", "subject": content, "text": content})
                continue
            if re.search(r"\b(?:english|tieng anh|french|tieng phap|japanese|tieng nhat|toeic|ielts|toefl)\b", value):
                criteria.append({**base, "kind": "language", "subject": content, "text": content})
                continue
            if duration and not skills and re.search(f"{EXPERIENCE}|{PROFESSIONAL}", value):
                roles = detect_roles(content) or detect_roles(job_title)
                if len(roles) != 1 or duration["relation"] == "ambiguous":
                    issue(source, "ambiguous_role_or_duration", "Chưa xác định được một vai trò và khoảng thời gian cụ thể.")
                    continue
                numbers = [n for key, n in duration.items() if key.endswith("months")]
                if any(n <= 0 or n > 600 for n in numbers) or (duration["relation"] == "range" and duration["min_months"] > duration["max_months"]):
                    issue(source, "invalid_duration", "Khoảng thời gian kinh nghiệm không hợp lệ.")
                    continue
                criteria.append({**base, "kind": "experience", "subject": roles[0], "level": "paid_role_months",
                                 "duration": duration, "text": content})
                continue
            if not skills:
                if re.match(r"(?:we are (?:seeking|looking|hiring)|join (?:our|the) team|chung toi (?:dang )?tim)\b", value):
                    ignored.append({**source, "reason": "role_description_without_skill_criterion"})
                else:
                    issue(source, "unrecognized_requirement", "Yêu cầu được giữ lại để đối chiếu; chưa nhận diện được tiêu chí cụ thể.")
                continue
            # Preserve extra constraints rather than treating a skill mention as the entire condition.
            if duration:
                base["constraints"].append({"kind": "skill_duration", **duration})
            if re.search(ADVANCED, value):
                base["constraints"].append({"kind": "proficiency", "text": re.search(ADVANCED, value).group()})
            if re.search(r"\b(?:distributed systems|he thong phan tan|security clearance|work permit|giay phep lao dong)\b", value):
                base["constraints"].append({"kind": "domain_or_eligibility", "text": content})
            if re.search(r"\b(?:communication|teamwork|problem.solving|giao tiep|lam viec nhom|analytical thinking)\b", value):
                base["constraints"].append({"kind": "soft_skill", "text": content})
            for a, b, skill in skills:
                version = re.match(r"\s+v?(\d+(?:\.\d+)*)(?!\w)", content[b:])
                if version and not duration:
                    base["constraints"].append({"kind": "version", "skill": skill, "value": version[1]})
            try:
                logic = _logic(content, skills)
            except ValueError:
                issue(source, "alternative_or_group", "Chưa xác định được cách nhóm các lựa chọn kỹ năng.")
                continue
            # Unknown members of an explicit list must not disappear beside a known tool.
            for fragment in re.split(r",|\b(?:and|or|va|hoac|và|hoặc)\b", content, flags=re.I):
                if (re.fullmatch(r"\s*[A-Za-z][A-Za-z0-9+#.-]*(?:\s+(?:required|preferred))?[. ]*", fragment)
                        and not detect_skills(fragment) and not re.search(TASK, fold(fragment))):
                    issue(source, "unknown_list_member", "Danh sách còn kỹ năng chưa nhận diện: " + fragment.strip())
            base["level"] = _level(value, section == "responsibility")
            nodes = logic["children"] if logic.get("op") == "all" else [logic]
            for node in nodes:
                subjects = logic_skills(node)
                criteria.append({**copy.deepcopy(base), "kind": "skill", "subject": " / ".join(subjects),
                                 "logic": node, "text": content})

    # Merge repetitions and let a stronger requirement subsume an implicit lower level.
    merged = []
    for item in criteria:
        identity = (item["kind"], item["subject"], digest(item.get("logic")), digest(item.get("duration")), digest(item["constraints"]))
        existing = next((old for old in merged if old["_identity"] == identity and
                         (old["level"] == item["level"] or (old["priority"] == item["priority"] == "standard"))), None)
        if existing:
            if (existing["priority"] != item["priority"] and
                    "default_policy" not in {existing["priority_origin"], item["priority_origin"]}):
                issue(item["sources"][0], "conflicting_priority", "Mâu thuẫn giữa yêu cầu bắt buộc và ưu tiên.")
            if LEVEL_RANK.get(item["level"], 0) > LEVEL_RANK.get(existing["level"], 0):
                existing["level"] = item["level"]
                existing["text"] = item["text"]
            if item["weight"] > existing["weight"]:
                existing.update(weight=item["weight"], priority=item["priority"], priority_origin=item["priority_origin"])
            existing["sources"].extend(item["sources"])
        else:
            merged.append({**item, "_identity": identity})
    for item in merged:
        item.pop("_identity")
        item["id"] = "req-" + digest({key: item.get(key) for key in ("kind", "subject", "logic", "duration", "level", "constraints")})[:12]
        if item["priority_origin"] == "default_policy":
            warnings.append({"code": "default_weight", "requirement_id": item["id"], "message": "JD không nêu mức ưu tiên; dùng trọng số chuẩn."})
    merged.sort(key=lambda item: (item["kind"], item["subject"], item["level"]))
    if len(merged) > 20:
        unresolved.append({"code": "too_many_requirements", "message": "JD có hơn 20 tiêu chí; không bỏ bớt để tính điểm."})
    if not merged:
        unresolved.append({"code": "no_requirements", "message": "Chưa nhận diện được tiêu chí để đánh giá."})
    profile = {"schema": "prepared-jd-v2", "policy": copy.deepcopy(POLICY), "job_title": job_title,
               "jd_text": jd_text, "source_text": text, "jd_sha256": hashlib.sha256(jd_text.encode()).hexdigest(),
               "parser_sha256": hashlib.sha256(Path(__file__).read_text(encoding="utf-8").replace("\r\n", "\n").encode()).hexdigest(),
               "status": "needs_review" if unresolved else "ready", "criteria": merged,
               "requirements": [{key: item[key] for key in ("id", "text", "weight")} for item in merged],
               "warnings": warnings, "unresolved": unresolved, "ignored": ignored}
    profile["profile_id"] = "jd-" + digest(profile)
    return profile
