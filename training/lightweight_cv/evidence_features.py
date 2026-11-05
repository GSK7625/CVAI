"""Text-only rubric signals; shared by training and inference, never read targets.

shortcut: explicit English evidence and known IT entities only. Unknown context,
ambiguous dates and contradictions require review; this is not a general CV parser.
"""
from __future__ import annotations

import re
import numpy as np
from jd_parser import detect_roles, detect_skills, fold

FEATURE_VERSION = "e5-evidence-mlp-r1"
KINDS = ("basic", "practical", "professional", "experience", "unknown")
STATES = ("paid", "project", "course", "listed", "negated", "absent", "unknown", "conflict")
FEATURE_NAMES = (["kind_" + k for k in KINDS] + ["evidence_" + s for s in STATES]
                 + [k + "_x_" + s for k in KINDS for s in STATES]
                 + ["months_scaled", "required_scaled", "duration_ratio", "duration_enough",
                    "duration_zero", "duration_known", "duration_dated", "duration_ambiguous"])


def requirement_spec(text):
    value = fold(text)
    skills = {s for _, _, s in detect_skills(text)}
    roles = detect_roles(text)
    duration = re.search(r"\b(\d+)\s+(?:non-overlapping\s+calendar\s+)?(months?|years?)\b", value)
    if duration and len(roles) == 1 and not skills:
        months = int(duration[1]) * (12 if duration[2].startswith("year") else 1)
        if months > 0 and "paid" in value:
            return {"kind": "experience", "role": next(iter(roles)), "months": months}
    if len(skills) != 1 or duration:
        return {"kind": "unknown"}
    # An independent project OR paid work is a project-level criterion.
    if re.search(r"\b(project|prototype|hands-on|practical)\b", value):
        kind = "practical"
    elif re.search(r"\b(paid|professional|employment|commercial)\b", value):
        kind = "professional"
    elif re.search(r"\b(basic|foundational|familiarity|knowledge|understanding)\b", value):
        kind = "basic"
    else:
        kind = "unknown"
    return {"kind": kind, "skill": next(iter(skills))}


def line_state(text, skill):
    """Classify only a line which actually mentions this exact entity."""
    matches = detect_skills(text)
    hits = [(a, b) for a, b, s in matches if s == skill]
    if not hits:
        return None
    value = fold(text)
    # Generic multi-entity clauses have ambiguous attachment; never transfer
    # Python's employment claim to another skill listed in the same clause.
    if len({s for _, _, s in matches}) > 1:
        return "unknown"
    if re.search(r"\b(?:not|never)\s+(?:used|worked with|applied)\b|\bno (?:hands-on|practical) experience\b|\bnone so far\b", value):
        return "negated"
    if re.search(r"\b(?:unspecified|team.*mentioned|future learning goal|would like|plan to)\b", value):
        return "unknown"
    if re.search(r"\b(?:guided|instructor-led|tutorial|course|lessons|lab sessions|learning record)\b", value):
        return "course"
    if re.search(r"\b(?:listed|inventory|self-reported|skill list)\b|\bskills?\s*:", value):
        return "listed"
    if re.search(r"\b(?:unpaid|outside employment|personal project|independent (?:project|prototype)|self-directed)\b", value):
        return "project"
    if re.search(r"\b(?:paid (?:work|employment|position|engineering|technical)|professional work|as an employee)\b", value):
        return "paid"
    return "unknown"


def skill_evidence(cv, skill):
    states, contexts = set(), []
    for line in re.finditer(r"[^\r\n]+", cv):
        state = line_state(line.group(), skill)
        if state:
            states.add(state)
            contexts.append({"text": line.group(), "start": line.start(), "end": line.end(), "kind": state})
    if not states:
        states.add("absent")
    if "negated" in states and states & {"paid", "project", "course", "listed"}:
        states.add("conflict")
    return states, contexts


def duration_evidence(cv, role):
    intervals, totals, contexts = [], [], []
    ambiguous = False
    for line in re.finditer(r"[^\r\n]+", cv):
        text, value = line.group(), fold(line.group())
        if role not in detect_roles(text) or not re.search(r"\bpaid\b", value):
            continue
        if re.search(r"\b(?:unpaid|not paid|no paid)\b", value):
            continue
        pair = re.search(r"\b(\d{4})-(\d{2})\s+(?:to|[-–])\s+(\d{4})-(\d{2})\b", value)
        total = re.search(r"\b(\d+)\s+(months?|years?)\b", value)
        contexts.append({"text": text, "start": line.start(), "end": line.end(), "kind": "duration"})
        if pair:
            y1, m1, y2, m2 = map(int, pair.groups())
            start, end = y1 * 12 + m1 - 1, y2 * 12 + m2 - 1
            if not (1 <= m1 <= 12 and 1 <= m2 <= 12 and start <= end and "end exclusive" in value):
                ambiguous = True
            else:
                intervals.append((start, end))
        elif total:
            totals.append(int(total[1]) * (12 if total[2].startswith("year") else 1))
        else:
            ambiguous = True
    # Independent totals may overlap. Only date intervals can safely be summed.
    if len(totals) > 1 or (totals and intervals):
        ambiguous = True
    if intervals:
        merged = []
        for start, end in sorted(intervals):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(end, merged[-1][1])
            else:
                merged.append([start, end])
        months = sum(end - start for start, end in merged)
    else:
        months = totals[0] if totals else 0
    # Absence of the requested role gives no duration evidence in this rubric.
    return {"months": months, "known": not ambiguous, "dated": bool(intervals),
            "ambiguous": ambiguous, "contexts": contexts}


def analyze(cv, requirement):
    spec = requirement_spec(requirement)
    states, contexts, duration = set(), [], None
    if spec["kind"] == "experience":
        duration = duration_evidence(cv, spec["role"])
        contexts = duration["contexts"]
    elif spec.get("skill"):
        states, contexts = skill_evidence(cv, spec["skill"])
    reasons = []
    if spec["kind"] == "unknown": reasons.append("unsupported_requirement")
    if "unknown" in states: reasons.append("unresolved_skill_context")
    if "conflict" in states: reasons.append("conflicting_skill_claims")
    if duration and duration["ambiguous"]: reasons.append("ambiguous_duration")
    return {"spec": spec, "states": sorted(states), "duration": duration,
            "contexts": contexts, "review_reasons": reasons}


def rule_label(analysis):
    """Diagnostic baseline, not the MLP's target or a prediction override."""
    if analysis["review_reasons"]:
        return None
    kind, states = analysis["spec"]["kind"], set(analysis["states"])
    if kind == "experience":
        months = analysis["duration"]["months"]
        return "not_evidenced" if months == 0 else "met" if months >= analysis["spec"]["months"] else "partial"
    if not states & {"paid", "project", "course", "listed"}:
        return "not_evidenced"
    if kind == "basic" or "paid" in states or (kind == "practical" and "project" in states):
        return "met"
    return "partial"


def structured_features(samples):
    vectors, analyses = [], []
    for sample in samples:
        for req in sample["requirements"]:
            result = analyze(sample["cv_text"], req["text"])
            kind = np.array([float(result["spec"]["kind"] == k) for k in KINDS])
            state = np.array([float(s in result["states"]) for s in STATES])
            duration = np.zeros(8)
            if result["duration"]:
                d, required = result["duration"], result["spec"]["months"]
                duration[:] = [min(d["months"] / 60, 10), min(required / 60, 10),
                               min(d["months"] / required, 4), d["months"] >= required,
                               d["months"] == 0, d["known"], d["dated"], d["ambiguous"]]
            vectors.append(np.r_[kind, state, np.outer(kind, state).ravel(), duration])
            analyses.append(result)
    return np.asarray(vectors, dtype=np.float32), analyses


def combine_features(base, structured, mode):
    if len(base) != len(structured): raise ValueError("Feature rows do not align")
    if mode == "structured": return structured
    if mode == "compact": return np.c_[base[:, -3:], structured].astype(np.float32)
    if mode == "full": return np.c_[base, structured].astype(np.float32)
    raise ValueError("Unknown evidence feature mode")


def annotate_review(result, analyses):
    """Keep unresolved evidence out of a seemingly definitive aggregate score."""
    if len(result["assessments"]) != len(analyses): raise ValueError("Mismatched analyses")
    reasons = []
    for assessment, analysis in zip(result["assessments"], analyses):
        assessment["evidence_signals"] = analysis
        if analysis["review_reasons"]:
            reasons.append({"id": assessment["id"], "reasons": analysis["review_reasons"]})
    result["status"] = "needs_review" if reasons else "ready"
    result["review_required"] = reasons
    if reasons:
        result["score"] = None
        for assessment in result["assessments"]: assessment["contribution_points"] = None
        result["summary"] = "Có yêu cầu hoặc bằng chứng chưa xử lý chắc chắn; cần đối chiếu trước khi tính điểm tổng."
    return result
