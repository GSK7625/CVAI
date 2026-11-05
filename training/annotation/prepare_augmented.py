"""Merge v1 and development-only round1 proposals; quarantine unresolved labels."""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "lightweight_cv"))
from pipeline import LABELS, file_hash, load_splits, read_jsonl, write_json
from build_round import content_hash, jsonl


def contiguous_evidence(text, spans):
    if not spans: return None
    if any(not span.strip() or span not in text for span in spans):
        raise ValueError("Evidence is not in the CV")
    # v1 accepts one substring; keep all original spans separately in provenance.
    return text[min(text.index(s) for s in spans):max(text.index(s) + len(s) for s in spans)]


def merge_sample(sample, reference, humans):
    if content_hash(sample) != reference["input_sha256"]:
        raise ValueError("Input/reference hash mismatch")
    assessments, requirements, provenance, excluded = [], [], [], []
    refs = {r["id"]: r for r in reference["assessments"]}
    for req in sample["requirements"]:
        ref = refs[req["id"]]
        human = humans.get((sample["sample_id"], req["id"]))
        if ref["label"] not in LABELS or (human and human["label"] != ref["label"]):
            excluded.append({"sample_id": sample["sample_id"], "requirement_id": req["id"],
                             "reason": "unresolved_or_disputed_label", "rule_label": ref["label"],
                             "human_label": human["label"] if human else None})
            continue
        chosen = human or ref
        spans = chosen["evidence"]
        status = chosen["label"]
        evidence = contiguous_evidence(sample["cv_text"], spans)
        if status == "not_evidenced" and evidence is not None:
            raise ValueError("Negative evidence must be empty")
        if status != "not_evidenced" and evidence is None:
            raise ValueError("Positive label needs evidence")
        requirements.append(req)
        assessments.append({"id": req["id"], "status": status, "evidence": evidence})
        provenance.append({"sample_id": sample["sample_id"], "requirement_id": req["id"],
                           "source": "human_first_pass_agrees_rule" if human else "synthetic_rule_unreviewed",
                           "evidence_spans": spans, "human_reviewed": bool(human),
                           "adjudicated": False})
    if not requirements: raise ValueError("All labels unresolved")
    counts = collections.Counter(a["status"] for a in assessments)
    out = {k: sample[k] for k in ("sample_id", "cv_group", "jd_group", "cv_text")}
    out.update(requirements=requirements, target={"assessments": assessments,
               "summary": f"CV có {counts['met']} yêu cầu đáp ứng, {counts['partial']} một phần và {counts['not_evidenced']} chưa có bằng chứng trong phần được đánh giá.",
               "cv_issues": []})
    return out, provenance, excluded


def prepare(old, review, output):
    if output.exists(): raise FileExistsError("Refusing to overwrite augmented data")
    old_splits, old_hashes = load_splits(old)
    manifest = json.loads((review / "manifest.json").read_text(encoding="utf-8"))
    for name in ("inputs_blind.jsonl", "reference_sealed.zip", "holdout_sealed.zip"):
        if file_hash(review / name) != manifest["files"][name]: raise ValueError("Review packet changed: " + name)
    inputs = read_jsonl(review / "inputs_blind.jsonl")
    ids = {r["sample_id"] for r in inputs}
    # Read development keys only; never open holdout_sealed.zip or pass it to a model.
    with ZipFile(review / "reference_sealed.zip") as z:
        refs = {r["sample_id"]: r for line in z.read("references.jsonl").decode().splitlines()
                if (r := json.loads(line))["sample_id"] in ids}
        register = {r["sample_id"]: r for line in z.read("source_register.jsonl").decode().splitlines()
                    if (r := json.loads(line))["sample_id"] in ids}
    frozen = review / "doi_chieu_dang_lo1_20261103/annotations_frozen.json"
    receipt = json.loads(frozen.with_suffix(".json.freeze.json").read_text(encoding="utf-8"))
    if file_hash(frozen) != receipt["annotation_sha256"]: raise ValueError("Frozen human export changed")
    annotations = json.loads(frozen.read_text(encoding="utf-8"))
    humans = {(r["sample_id"], r["requirement_id"]): r for r in annotations["annotations"] if r["label"]}
    new = {"train": [], "validation": []}
    provenance, excluded = [], []
    for s in inputs:
        split = register[s["sample_id"]]["split"]
        if split not in new: raise ValueError("Holdout leaked into development")
        merged, labels, omitted = merge_sample(s, refs[s["sample_id"]], humans)
        new[split].append(merged)
        provenance.extend({**p, "split": split} for p in labels)
        excluded.extend({**p, "split": split} for p in omitted)
    output.mkdir(parents=True)
    for split in ("train", "validation"):
        (output / f"{split}.jsonl").write_text(jsonl(old_splits[split] + new[split]), encoding="utf-8")
        (output / f"new_{split}.jsonl").write_text(jsonl(new[split]), encoding="utf-8")
    (output / "test.jsonl").write_bytes((old / "test.jsonl").read_bytes())
    (output / "label_provenance.jsonl").write_text(jsonl(provenance), encoding="utf-8")
    (output / "excluded_requirements.jsonl").write_text(jsonl(excluded), encoding="utf-8")
    combined, hashes = load_splits(output)
    counts = {split: {"pairs": len(rows), "requirements": sum(len(s["requirements"]) for s in rows),
                      "new_pairs": len(new.get(split, []))} for split, rows in combined.items()}
    result = {"dataset": "cvai-augmented-r1", "splits": counts, "data_hashes": hashes,
              "old_data_hashes": old_hashes, "human_export_sha256": file_hash(frozen),
              "new_label_sources": dict(collections.Counter(p["source"] for p in provenance)),
              "excluded_unresolved_requirements": len(excluded), "holdout_used": False,
              "holdout_zip_sha256": file_hash(review / "holdout_sealed.zip"),
              "old_test_byte_identical": hashes["test"] == old_hashes["test"],
              "source_kind": "controlled_synthetic; partially reviewed by one human",
              "all_labels_human_reviewed": False, "preparation_script_sha256": file_hash(Path(__file__)),
              "limits": "Old test previously observed; report historical benchmark only. New scores omit unresolved requirements; evidence span hull is not a verified single semantic quote."}
    write_json(output / "manifest.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old", type=Path, default=ROOT.parent / "datasets/cvai_v1")
    p.add_argument("--review", type=Path, default=ROOT.parent / "datasets/human_review_round1")
    p.add_argument("--output", type=Path, default=ROOT.parent / "datasets/cvai_augmented_r1")
    a = p.parse_args()
    prepare(a.old, a.review, a.output)
