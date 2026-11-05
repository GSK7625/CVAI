"""Build a separate, blind human-review round. Never modify the v1 splits."""
import argparse
import collections
import hashlib
import json
import random
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
ROUND = "cvai-human-review-round1"
SEED = 20261102
RUBRIC = "cvai-review-r1.1-draft"
TRACKS = {
    "backend": ("backend developer", ["Python", "Java", "PostgreSQL", "Redis", "Node.js"]),
    "frontend": ("frontend developer", ["React", "TypeScript", "CSS", "JavaScript", "Jest"]),
    "qa": ("QA engineer", ["pytest", "Playwright", "Selenium", "Postman", "SQL"]),
    "devops": ("DevOps engineer", ["Docker", "Kubernetes", "Terraform", "AWS", "Linux"]),
    "data": ("data/ML engineer", ["pandas", "scikit-learn", "SQL", "Airflow", "Apache Spark"]),
    "mobile": ("mobile developer", ["Kotlin", "Swift", "Android", "React Native", "iOS"]),
}
CASES = ("listed", "project", "negated", "short_duration", "overlap_short",
         "overlap_enough", "absent", "course", "boundary", "ambiguous")
DOMAINS = ["seed exchange", "public archive search", "bicycle repair booking", "harbour logistics",
           "lab equipment loans", "food donation routing", "language practice", "roof inspection",
           "community transport", "accessible travel", "research grant tracking", "farm stock control"]
STATES = ("paid", "project", "course", "listed", "negated", "absent")
TASKS = ("implement the import workflow", "diagnose failed requests", "build the reporting component",
         "write checks for boundary cases", "maintain the integration layer", "validate incoming records")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def content_hash(row):
    return sha(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())


def jsonl(rows):
    return "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)


def skill_sentence(tech, state, variant, task, domain):
    forms = {
        "paid": [f"In a paid position, I used {tech} to {task} for a {domain} service.",
                 f"My paid engineering work included using {tech} to {task}.",
                 f"As an employee, I applied {tech} to {task}; I owned this implementation."],
        "project": [f"For a self-directed, unpaid {domain} project, I used {tech} to {task}.",
                    f"Outside employment, I built a {domain} prototype with {tech} to {task}.",
                    f"Personal project: independently applied {tech} to {task}; this was unpaid."],
        "course": [f"My exposure to {tech} is limited to instructor-led exercises; no independent build.",
                   f"Studied {tech} through guided lab sessions only.",
                   f"Completed a tutorial on {tech}, following the provided instructions."],
        "listed": [f"Skills inventory: {tech}.", f"Self-reported familiarity: {tech}.",
                   f"Technology listed on my profile: {tech}."],
        "negated": [f"I have not used {tech} in work or projects.",
                    f"No practical experience with {tech} so far.",
                    f"I have not worked with {tech}; it is a future learning goal."],
        "absent": [None, None, None],
        "ambiguous": [f"A team I belonged to mentioned {tech}; my own use and work context are unspecified."] * 3,
    }
    return forms[state][variant % 3]


def union_months(intervals):
    # Endpoints are exclusive, including when two paid roles run concurrently.
    return len({m for start, end in intervals for m in range(start, end)})


def month_name(index):
    return f"{2020 + index // 12:04d}-{index % 12 + 1:02d}"


def assess_skill(kind, state, evidence):
    if state == "ambiguous":
        return "needs_review", []
    if state in {"absent", "negated"}:
        return "not_evidenced", []
    full = kind == "basic" or state == "paid" or (kind == "practical" and state == "project")
    return ("met" if full else "partial"), [evidence]


def make_job(track, index):
    role, technologies = TRACKS[track]
    techs = [technologies[(index + n) % len(technologies)] for n in range(3)]
    required = (12, 18, 24, 36)[index % 4]
    reqs = [
        {"id": "r1", "text": f"Basic familiarity with {techs[0]}.", "weight": 1},
        {"id": "r2", "text": f"Independently apply {techs[1]} in a hands-on project or paid work.", "weight": 2},
        {"id": "r3", "text": f"Use {techs[2]} during paid employment, with a concrete task described.", "weight": 3},
        {"id": "r4", "text": f"At least {required} non-overlapping calendar months of paid {role} work.", "weight": 2},
    ]
    domain = DOMAINS[index]
    text = (f"Position: {role} — {domain}.\nWe maintain a {domain} product. "
            "Assess only the following technical requirements.\n" +
            "\n".join(f"- {r['text']}" for r in reqs))
    key = "jd-" + content_hash({"track": track, "index": index, "text": text})[:16]
    return {"jd_group": key, "job_title": role, "jd_text": text, "requirements": reqs}, techs, required


def make_cv(track, index, job, techs, required, rng):
    case = CASES[(index + list(TRACKS).index(track) * 2) % len(CASES)]
    role = job["job_title"]
    domain = rng.choice(DOMAINS)
    states = [rng.choice(STATES) for _ in range(3)]
    states[2] = {"listed": "listed", "project": "project", "negated": "negated",
                 "absent": "absent", "course": "course", "boundary": "paid",
                 "ambiguous": "ambiguous"}.get(case, states[2])
    start = rng.randrange(0, 30)
    months = rng.choice((6, 12, 18, 24, 36))
    if case in {"short_duration", "overlap_short"}: months = required - 3
    if case in {"boundary", "overlap_enough"}: months = required
    if case == "project": months = 0
    intervals = [] if not months else [(start, start + months)]
    if case.startswith("overlap"):
        intervals = [(start, start + months - 2), (start + 2, start + months)]
    # A CV without paid work cannot contain an independent claim of a paid task.
    if not intervals:
        states = ["project" if s == "paid" else s for s in states]
    facts = [skill_sentence(t, s, rng.randrange(3), rng.choice(TASKS), domain)
             for t, s in zip(techs, states)]
    date_lines = [f"Paid {role}, contract {n + 1}: {month_name(a)} to {month_name(b)} (end exclusive)."
                  for n, (a, b) in enumerate(intervals)]
    if not date_lines:
        date_lines = ["Employment record: no paid technical employment; projects and study only."]
    extra = [
        "I write handover notes so another contributor can reproduce a reported issue.",
        "My workflow starts with a small failing example before changing a component.",
        "I record implementation choices and their limitations in project notes.",
        "The team reviewed changes through pull requests and discussed trade-offs.",
        "I kept a checklist for testing edge cases before each demonstration.",
        "I documented a rollback procedure and the steps needed to reproduce bugs.",
        "Work was discussed in weekly planning sessions; no performance figures are claimed here.",
        "Education: computing studies covering algorithms, data structures and software design.",
        "A written project log explains which parts I implemented and which were supplied in tutorials.",
        "I prefer describing what I delivered and what remains untested rather than listing achievements.",
    ]
    paragraphs = ("During the project I collected user feedback, made a small test plan, and documented "
                  "the changes. The scope was limited to a prototype, with no claim of a production rollout. "
                  "I wrote a short handover covering known limitations, setup steps and examples of input. "
                  "Another contributor checked the documentation against the implementation. "
                  "The record does not claim ownership of every component used by the team.")
    lines = [f"Career focus: {role}.", *date_lines, *[f for f in facts if f]]
    extras = rng.sample(extra, (1, 4, 8)[index % 3])
    if index % 3 == 2: extras.extend([paragraphs, paragraphs.replace("During the project", "For the final handover")])
    if techs[2] == "Java": extras.append("A separate browser exercise used JavaScript, not Java.")
    if techs[2] == "React": extras.append("A separate mobile screen used React Native; this does not describe React web work.")
    # Distractors are explicitly separate from the assessed facts.
    headers = [("PROFILE", "EXPERIENCE", "PROJECTS AND LEARNING"),
               ("Career note", "Work history", "Delivery notes"),
               ("Overview", "Engagements", "Additional context"),
               ("Professional focus", "Timeline", "Selected activities"),
               ("Summary", "Contracts", "Portfolio notes"),
               ("About my work", "Paid appointments", "Background")][index % 6]
    if index % 6 in {0, 3}:
        cv = f"{headers[0]}\n{lines[0]}\n\n{headers[1]}\n" + "\n".join(lines[1:]) + f"\n\n{headers[2]}\n" + "\n".join(extras)
    elif index % 6 in {1, 4}:
        cv = f"{headers[0]}\n{lines[0]}\n\n{headers[2]}\n" + "\n".join(extras) + f"\n\n{headers[1]}\n" + "\n".join(reversed(lines[1:]))
    else:
        cv = "\n\n".join([headers[0] + "\n" + lines[0], *lines[1:], *extras])
    cv_group = "cv-" + sha(cv.encode())[:16]
    references = []
    for n, (kind, state, fact) in enumerate(zip(("basic", "practical", "professional"), states, facts), 1):
        label, evidence = assess_skill(kind, state, fact)
        references.append({"id": f"r{n}", "label": label, "evidence": evidence})
    duration = union_months(intervals)
    label = "not_evidenced" if duration == 0 else "met" if duration >= required else "partial"
    references.append({"id": "r4", "label": label, "evidence": date_lines if duration else []})
    return cv_group, cv, references, {"case": case, "states": states, "intervals": intervals,
                                     "union_months": duration, "track": track, "layout": index % 6}


def make_rows():
    rng = random.Random(SEED)
    inputs, references, register = [], [], []
    for track in TRACKS:
        for index in range(40):
            split = "train" if index < 24 else "validation" if index < 32 else "holdout"
            # Six train / two validation / two holdout JDs per track; no shared JD groups.
            job_index = index // 4
            job, techs, months = make_job(track, job_index)
            cv_group, cv, labels, facts = make_cv(track, index, job, techs, months, rng)
            sample_id = "review-" + content_hash([cv_group, job["jd_group"]])[:16]
            row = {"sample_id": sample_id, "cv_group": cv_group, **job, "cv_text": cv}
            row_hash = content_hash(row)
            inputs.append(row)
            references.append({"sample_id": sample_id, "input_sha256": row_hash,
                               "assessments": labels, "label_source": "synthetic_rules_r1.1",
                               "human_reviewed": False})
            register.append({"sample_id": sample_id, "cv_group": cv_group, "jd_group": job["jd_group"],
                             "split": split, "source_kind": "author_created_synthetic", "is_real_cv": False,
                             "external_source": None, "source_permission": "no_external_cv_text_used",
                             "personal_data": "no_names_contacts_or_real_employers_generated",
                             "input_sha256": row_hash, **facts})
    rng.shuffle(inputs)
    return inputs, references, register


def render(inputs):
    payload = {"schema": "cvai-annotation-input-v1", "round_id": ROUND, "rubric_version": RUBRIC,
               "samples": inputs, "sample_hashes": {r["sample_id"]: content_hash(r) for r in inputs}}
    payload["input_sha256"] = content_hash(inputs)
    encoded = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return (ROOT / "reviewer.html").read_text(encoding="utf-8").replace("__DATA__", encoded)


def build(output):
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite a review round: {output}")
    inputs, refs, register = make_rows()
    assert len({r["cv_group"] for r in inputs}) == 240
    assert len({r["jd_group"] for r in inputs}) == 60
    splits = {r["sample_id"]: r["split"] for r in register}
    old = ROOT.parent / "datasets/cvai_v1"
    old_inputs = [json.loads(line) for split in ("train", "validation", "test")
                  for line in (old / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()]
    assert not {r["cv_text"] for r in inputs} & {r["cv_text"] for r in old_inputs}
    assert not {r["cv_group"] for r in inputs} & {r["cv_group"] for r in old_inputs}
    assert not {r["jd_group"] for r in inputs} & {r["jd_group"] for r in old_inputs}
    output.mkdir(parents=True)
    dev = [r for r in inputs if splits[r["sample_id"]] != "holdout"]
    test = [r for r in inputs if splits[r["sample_id"]] == "holdout"]
    for name in ("RUBRIC.md", "README.md"):
        (output / name).write_bytes((ROOT / name).read_bytes())
    (output / "reviewer.html").write_text(render(dev), encoding="utf-8")
    (output / "inputs_blind.jsonl").write_text(jsonl(dev), encoding="utf-8")
    with ZipFile(output / "reference_sealed.zip", "w", ZIP_DEFLATED) as z:
        z.writestr("references.jsonl", jsonl(refs))
        z.writestr("source_register.jsonl", jsonl(register))
    with ZipFile(output / "holdout_sealed.zip", "w", ZIP_DEFLATED) as z:
        z.writestr("reviewer.html", render(test))
        z.writestr("inputs_blind.jsonl", jsonl(test))
        z.writestr("RUBRIC.md", (ROOT / "RUBRIC.md").read_bytes())
    summary = {"round_id": ROUND, "seed": SEED, "rubric_version": RUBRIC,
               "cvs": 240, "jds": 60, "pairs": 240, "requirements": 960,
               "splits": dict(collections.Counter(splits.values())), "synthetic": True,
               "human_reviewed": False, "source_permission_verified_real_cvs": 0,
               "no_overlap_with_old_cv_text_or_group_ids": True,
               "generator_sha256": sha(Path(__file__).read_bytes()),
               "files": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
               "note": "Sealed means separate ZIP, not encryption. Same generator/ontology; not an external real-world test."}
    (output / "manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with ZipFile(output / "START_HERE.zip", "w", ZIP_DEFLATED) as z:
        for name in ("reviewer.html", "README.md", "RUBRIC.md", "inputs_blind.jsonl"):
            z.write(output / name, name)
    print(json.dumps({"output": str(output), **{k: summary[k] for k in ("cvs", "jds", "pairs", "splits")}}, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "datasets/human_review_round1")
    build(parser.parse_args().output)
