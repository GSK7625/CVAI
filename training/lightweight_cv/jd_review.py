"""Translate prepared JD conditions to the frozen model's supported atomic rubric.

Unsupported conditions stay visible. Never score an incomplete JD, reinterpret
approximate durations as minimums, or turn a choice of skills into an AND list.
"""
import re

from jd_parser import SKILLS as MODEL_SKILLS, digest
from jd_parser_v2 import detect_skills, logic_skills, prepare_jd
from pipeline import MAX_CV_CHARS
from evidence_features import duration_evidence
from jd_parser import fold

VALUES = {"met": 1, "partial": .5, "not_evidenced": 0}
REASONS = {
    "unsupported_skill": "Kỹ năng đã được đọc từ JD nhưng bộ đánh giá hiện tại chưa hỗ trợ chấm kỹ năng này.",
    "unsupported_qualification": "Đã đọc yêu cầu bằng cấp, ngoại ngữ hoặc chứng chỉ; cần đối chiếu trực tiếp với CV.",
    "duration_relation": "Cần đối chiếu đúng khoảng hoặc mốc kinh nghiệm của JD; không tự đổi thành yêu cầu tối thiểu.",
    "extra_constraint": "Cần kiểm tra thêm mức thành thạo, thời gian dùng kỹ năng hoặc điều kiện bổ sung trong câu JD gốc.",
    "unresolved_skill_context": "CV có nhắc kỹ năng nhưng chưa xác định rõ bối cảnh sử dụng hoặc mức kinh nghiệm.",
    "conflicting_skill_claims": "Các đoạn CV mô tả kinh nghiệm kỹ năng chưa thống nhất.",
    "ambiguous_duration": "Chưa xác định chắc thời gian kinh nghiệm từ CV.",
    "too_many_requirements": "Số tiêu chí vượt giới hạn đánh giá hiện tại; vẫn giữ lại toàn bộ để đối chiếu.",
    "unsupported_requirement": "Điều kiện này cần đối chiếu trực tiếp với CV.",
}


def prepare_input(sample):
    cv = sample.get("cv_text")
    if not isinstance(cv, str) or not cv.strip() or len(cv) > MAX_CV_CHARS:
        raise ValueError(f"cv_text phải có nội dung và không quá {MAX_CV_CHARS} ký tự")
    sources = [key for key in ("jd_text", "job_profile", "requirements") if sample.get(key) is not None]
    if len(sources) != 1 or (sample.get("job_title") is not None and sources[0] != "jd_text"):
        raise ValueError("Truyền đúng một nguồn JD; job_title chỉ dùng cùng jd_text")
    if sources[0] == "jd_text":
        return prepare_jd(sample["jd_text"], sample.get("job_title") or "")
    if sources[0] == "job_profile":
        supplied = sample["job_profile"]
        if not isinstance(supplied, dict):
            raise ValueError("job_profile phải là object từ /jobs/prepare")
        if supplied.get("schema") == "prepared-jd-v2":
            profile = prepare_jd(supplied.get("jd_text"), supplied.get("job_title", ""))
            if profile != supplied:
                raise ValueError("job_profile đã đổi hoặc khác phiên bản; cần chuẩn bị lại JD")
            return profile
    # Keep the original validator/model contract for structured input and v1 profiles.
    from jd_parser import resolve_input
    resolve_input(sample)
    return None


def _skill_text(skill, level):
    return {"basic": f"Basic knowledge of {skill}.",
            "practical": f"Practical project experience with {skill}.",
            "professional": f"Paid professional experience with {skill}."}[level]


def _atomic_texts(criterion):
    if criterion["constraints"]:
        return [], "extra_constraint"
    if criterion["kind"] == "skill":
        return [_skill_text(s, criterion["level"]) for s in logic_skills(criterion["logic"]) if s in MODEL_SKILLS], None
    if criterion["kind"] == "experience":
        duration = criterion["duration"]
        months = duration.get("months", 0)
        if duration["relation"] == "minimum" and months > 0 and int(months) == months:
            return [f"At least {int(months)} months of paid experience as a {criterion['subject']}."], None
        return [], "duration_relation"
    return [], "unsupported_qualification"


def _approximate_duration_match(cv, criterion):
    evidence = duration_evidence(cv, criterion["subject"])
    # An exact, explicit total satisfies the centre of an approximate target.
    # Do not invent a tolerance or accept an approximate/ranged CV claim as exact.
    uncertain = r"\b(?:around|about|approximately|roughly|over|under|more than|less than|at least|at most|up to|khoang|xap xi|hon|duoi|toi thieu|toi da)\b|[<>+]"
    for context in evidence["contexts"]:
        value = fold(context["text"])
        if re.search(uncertain, value) or re.search(r"\d\s*[-–]\s*\d+\s*(?:months?|years?)", value):
            return None
        if not evidence["dated"] and len(re.findall(r"\d+\s*(?:months?|years?)\b", value)) != 1:
            return None
    if (evidence["known"] and evidence["contexts"] and
            evidence["months"] == criterion["duration"]["months"]):
        return evidence
    return None


def _contexts(cv, skills):
    return [{"text": line.group(), "start": line.start(), "end": line.end()}
            for line in re.finditer(r"[^\r\n]+", cv)
            if {s for _, _, s in detect_skills(line.group())} & set(skills)]


def _bounds(node, leaves):
    if "skill" in node:
        value = leaves.get(node["skill"])
        return (0, 1) if value is None else (value, value)
    children = [_bounds(child, leaves) for child in node["children"]]
    combine = max if node["op"] == "any" else min
    return combine(low for low, _ in children), combine(high for _, high in children)


def _logic_title(node):
    if "skill" in node:
        return node["skill"]
    join = " hoặc " if node["op"] == "any" else " và "
    return "(" + join.join(_logic_title(child) for child in node["children"]) + ")"


def _title(criterion):
    if criterion["kind"] != "skill":
        return criterion["text"]
    prefix = {"basic": "Kiến thức", "practical": "Kinh nghiệm thực hành / dự án", "professional": "Kinh nghiệm làm việc chuyên nghiệp"}
    return prefix[criterion["level"]] + ": " + _logic_title(criterion["logic"])


def review_with_diagnostics(reviewer, sample):
    profile = prepare_input(sample)
    if profile is None:
        return reviewer.review(sample)
    prepared = [_atomic_texts(c) for c in profile["criteria"]]
    atoms = {text: {"id": "atom-" + digest(text)[:20], "text": text, "weight": 1}
             for texts, _ in prepared for text in texts}
    limited = len(profile["criteria"]) > 20 or len(atoms) > 20
    model = {"assessments": []}
    if atoms and not limited:
        model = reviewer.review({"sample_id": sample.get("sample_id", "new-cv"), "cv_text": sample["cv_text"],
                                 "requirements": list(atoms.values())})
    by_id = {a["id"]: a for a in model["assessments"]}
    assessments = []
    for criterion, (texts, reason) in zip(profile["criteria"], prepared):
        reasons = ["too_many_requirements"] if limited else [reason] if reason else []
        leaves, contexts, retrieved = {}, [], []
        parts = []
        for text in texts if not limited else []:
            a = by_id[atoms[text]["id"]]
            parts.append(a)
            signals = a.get("evidence_signals", {})
            reasons.extend(signals.get("review_reasons", []))
            contexts.extend(signals.get("contexts", []))
            retrieved.extend(a.get("retrieved_context", []))
        value = None
        matched_duration = None
        if criterion["kind"] == "skill":
            for skill in logic_skills(criterion["logic"]):
                text = _skill_text(skill, criterion["level"])
                a = by_id.get(atoms.get(text, {}).get("id")) if not reason and not limited else None
                leaves[skill] = (VALUES.get(a["status"]) if a and not a.get("evidence_signals", {}).get("review_reasons") else None)
                if skill not in MODEL_SKILLS:
                    reasons.append("unsupported_skill")
                    contexts.extend(_contexts(sample["cv_text"], [skill]))
            low, high = _bounds(criterion["logic"], leaves)
            if low == high:
                value = low
        elif parts and not reasons:
            value = VALUES.get(parts[0]["status"])
        elif (not limited and criterion["kind"] == "experience" and not criterion["constraints"]
              and criterion["duration"]["relation"] == "approximate"):
            matched_duration = _approximate_duration_match(sample["cv_text"], criterion)
            if matched_duration:
                value = 1
                contexts.extend(matched_duration["contexts"])
        reasons = list(dict.fromkeys(reasons)) if value is None else []
        if value is None and not reasons:
            reasons = ["unsupported_requirement"]
        status = next((key for key, points in VALUES.items() if points == value), "needs_review")
        comment = (" ".join(REASONS.get(r, REASONS["unsupported_requirement"]) for r in reasons) if reasons else
                   {"met": "Có bằng chứng phù hợp theo mức yêu cầu đã đọc; hãy đối chiếu các đoạn CV bên dưới.",
                    "partial": "Có bằng chứng liên quan nhưng chưa đầy đủ mức yêu cầu.",
                    "not_evidenced": "Chưa tìm thấy bằng chứng đáp ứng tiêu chí này trong CV."}[status])
        if matched_duration:
            months = matched_duration["months"]
            comment = f"CV nêu {months:g} tháng kinh nghiệm được trả lương ở đúng vai trò, khớp mốc khoảng {months:g} tháng của JD."
        unique_contexts = {digest(c): c for c in contexts}
        assessments.append({"id": criterion["id"], "requirement_text": _title(criterion), "status": status,
                            "weight": criterion["weight"], "priority": criterion["priority"], "comment": comment,
                            "jd_sources": criterion["sources"], "contribution_points": None,
                            "assessment_method": "exact_duration_evidence" if matched_duration else "model_or_review",
                            "evidence_signals": {"contexts": list(unique_contexts.values()), "review_reasons": reasons},
                            "retrieved_context": retrieved})
    pending = sum(a["status"] == "needs_review" for a in assessments)
    ready = bool(assessments) and not pending and not profile["unresolved"] and not limited
    score = None
    if ready:
        total = sum(a["weight"] for a in assessments)
        for a in assessments:
            a["contribution_points"] = round(100 * a["weight"] * VALUES[a["status"]] / total, 4)
        score = round(100 * sum(a["weight"] * VALUES[a["status"]] for a in assessments) / total, 4)
    summary = (f"Đã đọc {len(assessments)} tiêu chí JD. " +
               ("Điểm phản ánh kỹ năng và kinh nghiệm đã nhận diện; xem câu JD gốc để đối chiếu đầy đủ công việc." if ready else
                f"Còn {len(profile['unresolved'])} điều kiện JD chưa tách rõ; chưa tính điểm tổng." if profile["unresolved"] else
                f"Còn {pending} tiêu chí cần đối chiếu bằng chứng hoặc điều kiện bổ sung; chưa tính điểm tổng."))
    return {**{key: model[key] for key in ("schema", "model_profile", "elapsed_seconds", "notice") if key in model},
            "sample_id": sample.get("sample_id", "new-cv"), "status": "ready" if ready else "needs_review", "score": score,
            "summary": summary, "score_scope": profile["policy"]["score_scope"],
            "scoring_policy_version": profile["policy"]["version"], "review_policy_version": "jd-evidence-v2.1", "jd_profile": profile,
            "assessments": assessments, "review_required": [{"id": a["id"], "reasons": a["evidence_signals"]["review_reasons"]}
                                                             for a in assessments if a["status"] == "needs_review"]}
