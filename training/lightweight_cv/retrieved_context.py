"""MLP inputs derived from the JD, E5's top passages and their enclosing CV headings."""
from bisect import bisect_right
import re
import numpy as np

from evidence_features import KINDS, STATES, duration_evidence, line_state, requirement_spec
from jd_parser_v2 import BASIC, PRACTICAL, PROFESSIONAL, detect_skills

HEADINGS = {
    "experience": "paid", "work experience": "paid", "professional experience": "paid",
    "employment": "paid", "employment history": "paid", "work history": "paid",
    "projects": "project", "personal projects": "project", "selected projects": "project",
    "technical skills": "listed", "skills": "listed", "technologies": "listed",
    "education": None, "certifications": None, "summary": None, "interests": None,
    "volunteer experience": None, "activities": None, "awards": None, "coursework": None,
}
ACTION = re.compile(r"\b(?:used|applied|built|wrote|maintained|implemented|created|developed|"
                    r"designed|shipped|tested|deployed|automated|managed|integrated|migrated|"
                    r"reduced|optimized|prototyped|packaged|led|delivered|configured|refactored)\b", re.I)
UNCERTAIN = re.compile(r"\b(?:not|never|no|without|team (?:used|uses|mentioned)|exposure|observed|"
                       r"shadowed|plan to|would like|unpaid|volunteer|unspecified)\b|n['’]t\b", re.I)


def section_index(cv):
    offsets, kinds = [], []
    for match in re.finditer(r"[^\r\n]+", cv):
        title = match.group().strip().rstrip(":").casefold()
        if title in HEADINGS:
            offsets.append(match.start())
            kinds.append(HEADINGS[title])
    return offsets, kinds


def context_vector(query, passages, sections):
    spec = requirement_spec(query)
    kind = spec["kind"]
    entities = {s for _, _, s in detect_skills(query)}
    states = set()
    duration = np.zeros(5)
    if kind == "experience":
        d = duration_evidence("\n".join(p["text"] for p in passages), spec["role"])
        duration[:] = [min(d["months"] / spec["months"], 4), d["months"] >= spec["months"],
                       d["months"] > 0, d["known"], d["ambiguous"]]
    elif len(entities) == 1:
        skill = entities.pop()
        if kind == "unknown":
            for pattern, level in [(PRACTICAL, "practical"), (PROFESSIONAL, "professional"), (BASIC, "basic")]:
                if re.search(pattern, query, re.I):
                    kind = level
                    break
        offsets, kinds = sections
        for p in passages:
            text = p["text"]
            mentioned = {s for _, _, s in detect_skills(text)}
            if skill not in mentioned:
                continue
            state = line_state(text, skill) or "unknown"
            idx = bisect_right(offsets, p["start"]) - 1
            section = kinds[idx] if idx >= 0 else None
            if state == "unknown" and not UNCERTAIN.search(text):
                if section == "listed":
                    state = "listed"
                elif section in ("paid", "project") and len(mentioned) == 1 and ACTION.search(text):
                    state = section
            states.add(state)
        if not states:
            states.add("absent")
        if "negated" in states and states & {"project", "paid", "listed", "course"}:
            states.add("conflict")
    k = np.asarray([kind == key for key in KINDS], dtype=np.float32)
    s = np.asarray([key in states for key in STATES], dtype=np.float32)
    return np.r_[k, s, np.outer(k, s).ravel(), duration]


def model_inputs(samples, base, records):
    vectors = []
    for sample in samples:
        sections = section_index(sample["cv_text"])
        for req in sample["requirements"]:
            record = records[len(vectors)]
            if (record["sample_id"], record["requirement_id"]) != (sample.get("sample_id", "new-cv"), req["id"]):
                raise ValueError("Retrieved context does not align with requirements")
            vectors.append(context_vector(req["text"], record["retrieved"], sections))
    if len(vectors) != len(records) or len(vectors) != len(base):
        raise ValueError("Unexpected retrieval feature count")
    return np.column_stack((base, vectors)).astype(np.float32)
