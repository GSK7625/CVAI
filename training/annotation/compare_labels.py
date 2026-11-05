"""Freeze independent annotations, then compare with provisional rule labels."""
import argparse
import collections
import hashlib
import json
import random
import re
from pathlib import Path
from zipfile import ZipFile

from build_round import ROUND, RUBRIC, content_hash

LABELS = ("met", "partial", "not_evidenced")


def read_jsonl(text):
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def read_annotations(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("schema") != "cvai-human-annotations-v1" or data.get("round_id") != ROUND
            or data.get("rubric_version") != RUBRIC or data.get("reference_seen") is not False
            or not isinstance(data.get("annotator_id"), str) or not data["annotator_id"].strip()
            or not isinstance(data.get("annotations"), list)):
        raise ValueError("Not an independent annotation export for this round/rubric")
    return data


def freeze(path):
    data = read_annotations(path)
    receipt = path.with_suffix(path.suffix + ".freeze.json")
    if receipt.exists():
        raise FileExistsError("Freeze receipt already exists; keep the original and use a new export filename")
    metadata = {"annotation_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "annotator_id": data["annotator_id"], "round_id": data["round_id"],
                "rubric_version": data["rubric_version"], "reference_seen_declared": False,
                "note": "Local integrity receipt, not proof that the reviewer never accessed reference labels."}
    receipt.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(receipt)
    return receipt


def agreement(pairs):
    if not pairs: return {"n": 0, "agreement": None, "cohen_kappa": None, "macro_f1_rule_vs_human": None}
    n = len(pairs)
    observed = sum(h == a for h, a in pairs) / n
    hc, ac = collections.Counter(h for h, _ in pairs), collections.Counter(a for _, a in pairs)
    expected = sum(hc[k] * ac[k] for k in LABELS) / (n * n)
    per_class = {}
    for label in LABELS:
        tp = sum(h == a == label for h, a in pairs)
        fp = sum(a == label and h != label for h, a in pairs)
        fn = sum(h == label and a != label for h, a in pairs)
        per_class[label] = {"human_support": hc[label], "rule_support": ac[label],
                            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}
    return {"n": n, "agreement": observed,
            "cohen_kappa": (observed - expected) / (1 - expected) if expected < 1 else None,
            "macro_f1_rule_vs_human": sum(v["f1"] for v in per_class.values()) / 3,
            "per_class": per_class,
            "confusion_human_rows_rule_columns": [[sum(h == x and a == y for h, a in pairs) for y in LABELS] for x in LABELS],
            "label_order": LABELS}


def evidence_f1(human, reference):
    # Lexical overlap only; two valid supporting quotes can differ completely.
    def tokens(spans): return set(re.findall(r"\w+", " ".join(spans).casefold()))
    h, r = tokens(human), tokens(reference)
    return 2 * len(h & r) / (len(h) + len(r)) if h or r else None


def bootstrap(groups):
    if len(groups) < 2: return None
    rng, values = random.Random(20261102), []
    for _ in range(1000):
        sample = [p for _ in groups for p in rng.choice(groups)]
        values.append(sum(h == a for h, a in sample) / len(sample))
    values.sort()
    return [values[24], values[974]]


def compare(annotation, inputs_path, reference_zip, output):
    if output.exists(): raise FileExistsError("Refusing to overwrite a comparison")
    data = read_annotations(annotation)
    receipt = json.loads(annotation.with_suffix(annotation.suffix + ".freeze.json").read_text(encoding="utf-8"))
    current = hashlib.sha256(annotation.read_bytes()).hexdigest()
    if current != receipt["annotation_sha256"]: raise ValueError("Annotation changed after freeze")
    inputs = read_jsonl(inputs_path.read_text(encoding="utf-8"))
    if content_hash(inputs) != data.get("input_sha256"): raise ValueError("Wrong input packet or changed CV/JD")
    by_id = {s["sample_id"]: s for s in inputs}
    with ZipFile(reference_zip) as z:
        refs = {r["sample_id"]: r for r in read_jsonl(z.read("references.jsonl").decode())}
        register = {r["sample_id"]: r for r in read_jsonl(z.read("source_register.jsonl").decode())}
    pairs, grouped, adjudication, seen, evidence_scores = [], collections.defaultdict(list), [], set(), []
    completion, by_case, by_split = collections.Counter(), collections.defaultdict(list), collections.defaultdict(list)
    for a in data["annotations"]:
        sid, rid = a["sample_id"], a["requirement_id"]
        s = by_id.get(sid)
        if s is None or rid not in {r["id"] for r in s["requirements"]} or (sid, rid) in seen:
            raise ValueError("Unknown or duplicate annotation key")
        seen.add((sid, rid))
        if a.get("input_sha256") != content_hash(s) or refs[sid]["input_sha256"] != content_hash(s):
            raise ValueError("Input/reference hash mismatch")
        label, ev = a.get("label"), a.get("evidence")
        if label not in ("", *LABELS, "needs_review") or not isinstance(ev, list): raise ValueError("Invalid label/evidence")
        if any(not isinstance(q, str) or not q.strip() or q not in s["cv_text"] for q in ev):
            raise ValueError("Evidence is not a verbatim CV substring")
        if label == "not_evidenced" and ev: raise ValueError("not_evidenced needs empty evidence")
        complete = bool(label and a.get("confidence") in ("low", "medium", "high")
                        and (label not in ("met", "partial") or ev)
                        and (label != "needs_review" or a.get("notes", "").strip()))
        if not complete:
            completion["unfinished"] += 1
            continue
        completion["complete"] += 1
        ref = next(r for r in refs[sid]["assessments"] if r["id"] == rid)
        eligible = label in LABELS and ref["label"] in LABELS
        if eligible:
            pair = (label, ref["label"])
            pairs.append(pair)
            grouped[s["cv_group"]].append(pair)
            by_case[register[sid]["case"]].append(pair)
            by_split[register[sid]["split"]].append(pair)
            if label == ref["label"] and label in ("met", "partial"):
                evidence_scores.append({"sample_id": sid, "requirement_id": rid,
                                        "exact_span_set_match": set(ev) == set(ref["evidence"]),
                                        "token_set_f1": evidence_f1(ev, ref["evidence"])})
        else: completion["needs_review_either_side"] += 1
        if label != ref["label"] or not eligible or a.get("rubric_feedback", "").strip():
            adjudication.append({"sample_id": sid, "requirement_id": rid,
                                 "human_label": label, "rule_label": ref["label"],
                                 "human_evidence": ev, "rule_evidence": ref["evidence"],
                                 "human_notes": a.get("notes", ""), "rubric_feedback": a.get("rubric_feedback", ""),
                                 "final_label": "", "final_evidence": [], "adjudicator": "", "reason": ""})
    total = sum(len(s["requirements"]) for s in inputs)
    completion["missing_records"] = total - len(seen)
    report = {"round_id": ROUND, "rubric_version": RUBRIC, "annotator_id": data["annotator_id"],
              "annotations_sha256": current, "packet_requirements": total, "completion": dict(completion),
              "coverage": completion["complete"] / total, "agreement_metrics": agreement(pairs),
              "agreement_95pct_cluster_bootstrap_ci": bootstrap(list(grouped.values())),
              "bootstrap_unit": "independent synthetic CV; 1000 resamples, seed 20261102",
              "by_case": {k: agreement(v) for k, v in by_case.items()},
              "by_split": {k: agreement(v) for k, v in by_split.items()},
              "evidence_comparison": {"n_same_positive_label": len(evidence_scores),
                                      "exact_span_set_agreement": sum(r["exact_span_set_match"] for r in evidence_scores) / len(evidence_scores) if evidence_scores else None,
                                      "mean_token_set_f1": sum(r["token_set_f1"] for r in evidence_scores) / len(evidence_scores) if evidence_scores else None},
              "source": "synthetic, no third-party real CVs; permission-verified real CV count = 0",
              "human_reviewed_complete": completion["complete"] == total,
              "adjudicated": False,
              "limits": ["Agreement with rule-generated proposals is not label accuracy or source authenticity.",
                         "One human vs rules is not human-human inter-rater reliability.",
                         "Unfinished/needs_review excluded from three-class metrics; coverage reported.",
                         "Evidence overlap is lexical, not a semantic validity judgement.",
                         "After revealing holdout comparisons, retire that holdout from model selection."]}
    output.mkdir(parents=True)
    (output / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "adjudication.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in adjudication), encoding="utf-8")
    (output / "evidence_comparison.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in evidence_scores), encoding="utf-8")
    print(json.dumps({"report": str(output / 'comparison.json'), "coverage": report['coverage'],
                      "agreement": report['agreement_metrics'], "to_adjudicate": len(adjudication)}, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("freeze"); p.add_argument("annotations", type=Path)
    p = sub.add_parser("compare")
    p.add_argument("annotations", type=Path)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "freeze": freeze(args.annotations)
    else: compare(args.annotations, args.inputs, args.reference, args.output)
