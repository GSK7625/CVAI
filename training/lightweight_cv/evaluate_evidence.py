"""One-shot historical/held-out evaluation AFTER recipe and weights are locked."""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from zipfile import ZipFile

import numpy as np

from evidence_features import analyze, requirement_spec, rule_label
from optimize_evidence import ROOT, detailed_metrics, dump_jsonl
from pipeline import (LABELS, ClassifierHead, Reviewer, features_for_samples, file_hash,
                      read_jsonl, target_labels, weighted_score, write_json)


def paired_bootstrap(samples, baseline, predicted, method, repeats=5000, seed=20261105):
    """Paired cluster bootstrap. Requirements are NEVER resampled independently."""
    gold = target_labels(samples)
    index = {label: i for i, label in enumerate(LABELS)}
    matrices = np.zeros((len(samples), 2, 3, 3), dtype=int)
    errors = np.zeros((len(samples), 2))
    offset = 0
    for i, s in enumerate(samples):
        n = len(s["requirements"])
        ids = [r["id"] for r in s["requirements"]]
        truth = dict(zip(ids, gold[offset:offset+n]))
        for m, prediction in enumerate((baseline, predicted)):
            p = prediction[offset:offset+n]
            for a, b in zip(gold[offset:offset+n], p): matrices[i, m, index[a], index[b]] += 1
            errors[i, m] = abs(weighted_score(s["requirements"], dict(zip(ids, p))) - weighted_score(s["requirements"], truth))
        offset += n
    _, jd = np.unique([s["jd_group"] for s in samples], return_inverse=True)
    _, cv = np.unique([s["cv_group"] for s in samples], return_inverse=True)
    nj, nc = max(jd)+1, max(cv)+1
    rng, delta, skipped = np.random.default_rng(seed), [], 0

    def compute(weights):
        matrix = np.einsum("i,imab->mab", weights, matrices)
        denominator = matrix.sum(1) + matrix.sum(2)
        numer = 2 * np.diagonal(matrix, axis1=1, axis2=2)
        f1 = np.divide(numer, denominator, out=np.zeros_like(numer, dtype=float), where=denominator > 0).mean(1)
        mae = np.average(errors, weights=weights, axis=0)
        return np.array([f1[1]-f1[0], mae[1]-mae[0]])

    for _ in range(repeats):
        weights = rng.multinomial(nj, np.ones(nj)/nj)[jd]
        if method == "crossed_jd_cv": weights = weights * rng.multinomial(nc, np.ones(nc)/nc)[cv]
        elif method != "jd": raise ValueError("Unsupported cluster scheme")
        if weights.sum() == 0:
            skipped += 1
            continue
        delta.append(compute(weights))
    delta = np.asarray(delta)
    return {"method": method, "seed": seed, "requested_repeats": repeats, "valid_repeats": len(delta),
            "skipped_empty": skipped, "jd_groups": int(nj), "cv_groups": int(nc),
            "delta_f1": float(compute(np.ones(len(samples)))[0]),
            "delta_mae": float(compute(np.ones(len(samples)))[1]),
            "delta_f1_ci95": np.quantile(delta[:, 0], [.025, .975]).tolist(),
            "delta_mae_ci95": np.quantile(delta[:, 1], [.025, .975]).tolist(),
            "limit": "Percentile cluster interval; few groups and shared synthetic generator limit generalization."}


def load_holdout(review_dir, development):
    # No evaluation code may generate new data or consult generator fact states.
    with ZipFile(review_dir / "holdout_sealed.zip") as z:
        inputs = [json.loads(line) for line in z.read("inputs_blind.jsonl").decode().splitlines() if line.strip()]
    ids = {s["sample_id"] for s in inputs}
    with ZipFile(review_dir / "reference_sealed.zip") as z:
        refs = {r["sample_id"]: r for line in z.read("references.jsonl").decode().splitlines()
                if (r := json.loads(line))["sample_id"] in ids}
    for key in ("sample_id", "cv_group", "jd_group"):
        if {r[key] for r in inputs} & {r[key] for r in development}: raise ValueError("Holdout leakage: " + key)
    if {" ".join(r["cv_text"].lower().split()) for r in inputs} & {" ".join(r["cv_text"].lower().split()) for r in development}:
        raise ValueError("Holdout CV content leakage")
    import hashlib
    samples, excluded = [], []
    for s in inputs:
        digest = hashlib.sha256(json.dumps(s, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        if digest != refs[s["sample_id"]]["input_sha256"]: raise ValueError("Holdout reference mismatch")
        target = {r["id"]: r for r in refs[s["sample_id"]]["assessments"]}
        reqs, labels = [], []
        for req in s["requirements"]:
            ref = target[req["id"]]
            if ref["label"] not in LABELS:
                excluded.append({"pair_id": s["sample_id"], "requirement_id": req["id"], "reason": ref["label"]})
                continue
            reqs.append(req)
            spans = ref["evidence"]
            if any(span not in s["cv_text"] for span in spans): raise ValueError("Invalid reference quote")
            evidence = s["cv_text"][min(s["cv_text"].index(x) for x in spans):max(s["cv_text"].index(x)+len(x) for x in spans)] if spans else None
            labels.append({"id": req["id"], "status": ref["label"], "evidence": evidence})
        if not reqs: raise ValueError("No eligible holdout criteria")
        samples.append({**s, "requirements": reqs, "target": {"assessments": labels}})
    return samples, inputs, excluded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--recover-report", action="store_true",
                        help="Recover a failed report from frozen CSV predictions; never rerun model selection")
    args = parser.parse_args()
    protocol = json.loads((args.run / "protocol.json").read_text(encoding="utf-8"))
    selection = json.loads((args.run / "selection_locked.json").read_text(encoding="utf-8"))
    complete = json.loads((args.run / "training_complete.json").read_text(encoding="utf-8"))
    if selection["protocol_sha256"] != file_hash(args.run / "protocol.json"): raise ValueError("Protocol changed")
    for name, digest in protocol["source_hashes"].items():
        if args.recover_report and name == Path(__file__).name: continue
        if file_hash(ROOT / name) != digest: raise ValueError("Code changed after training: " + name)
    if not selection["selected"] or not complete["all_stability_seeds_pass"]:
        raise ValueError("Validation/stability gates failed; keep holdout closed")
    receipt = args.run / "holdout_open_receipt.json"
    if args.recover_report:
        recover_report(args.run, protocol, complete)
        return
    if receipt.exists(): raise FileExistsError("Holdout was already opened; never tune and reopen")
    baseline = Reviewer(ROOT / "artifact")
    previous = ClassifierHead(ROOT / "artifacts/augmentation-r1/classifier.npz")
    selected = Reviewer(args.run / "selected_artifact")
    if selected.manifest["classifier_sha256"] != complete["artifact_classifier_sha256"]: raise ValueError("Selected weights changed")
    review_dir = ROOT.parent / "datasets/human_review_round1"
    global_receipt = review_dir / "holdout_first_evaluation.json"
    if global_receipt.exists():
        raise ValueError("This holdout has already been used by another recorded run; it is no longer a fresh test")
    if file_hash(review_dir / "holdout_sealed.zip") != protocol["holdout_zip_sha256"]: raise ValueError("Holdout changed")
    development = read_jsonl(ROOT.parent / "datasets/cvai_augmented_r1/train.jsonl") + read_jsonl(ROOT.parent / "datasets/cvai_augmented_r1/validation.jsonl")
    # Receipt is written BEFORE opening. Interrupted evaluations are investigated,
    # never silently repeated after looking at the held-out answers.
    write_json(receipt, {"opened_at_unix": time.time(), "selection_sha256": file_hash(args.run / "selection_locked.json"),
                        "classifier_sha256": complete["artifact_classifier_sha256"], "status": "started"})
    write_json(global_receipt, {"run": str(args.run.resolve()), "receipt_sha256": file_hash(receipt),
                               "holdout_zip_sha256": protocol["holdout_zip_sha256"]})
    holdout, full_inputs, excluded = load_holdout(review_dir, development)
    results = {}
    output = args.run / "evaluation"
    output.mkdir()
    dump_jsonl(output / "holdout_excluded.jsonl", excluded)
    for name, samples, clustering in (("historical_test", read_jsonl(ROOT.parent / "datasets/cvai_v1/test.jsonl"), "crossed_jd_cv"),
                                     ("holdout", holdout, "jd")):
        print("Evaluating", name, flush=True)
        started = time.perf_counter()
        x, records = features_for_samples(samples, baseline.encoder)
        p_v1, p_prev = baseline.head.predict(x), previous.predict(x)
        p_new = selected.predict_labels(samples, x, records)
        analyses = [analyze(s["cv_text"], r["text"]) for s in samples for r in s["requirements"]]
        rules = [rule_label(a) for a in analyses]
        p_rule = np.array([a if a is not None else b for a, b in zip(rules, p_v1)])
        results[name] = {"v1": detailed_metrics(samples, p_v1), "augmentation_r1": detailed_metrics(samples, p_prev),
                         "selected": detailed_metrics(samples, p_new), "rule_with_v1_fallback": detailed_metrics(samples, p_rule),
                         "rule_coverage": sum(x is not None for x in rules)/len(rules),
                         "unresolved_input_requirements": sum(bool(a["review_reasons"]) for a in analyses),
                         "elapsed_seconds": time.perf_counter()-started,
                         "paired_bootstrap_vs_v1": paired_bootstrap(samples, p_v1, p_new, clustering),
                         "paired_bootstrap_vs_aug_r1": paired_bootstrap(samples, p_prev, p_new, clustering)}
        rows, offset = [], 0
        for s in samples:
            truth = {a["id"]: a["status"] for a in s["target"]["assessments"]}
            for req in s["requirements"]:
                rows.append({"pair_id": s["sample_id"], "jd_group": s["jd_group"], "cv_group": s["cv_group"],
                             "requirement_id": req["id"], "requirement_kind": requirement_spec(req["text"])["kind"],
                             "y_true": truth[req["id"]], "pred_v1": p_v1[offset], "pred_previous": p_prev[offset],
                             "pred_new": p_new[offset], "weight": req["weight"], "pred_rule": rules[offset]})
                offset += 1
        with (output / f"{name}_predictions.csv").open("x", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
        dump_jsonl(output / f"{name}_context.jsonl", samples)
        write_json(output / "results_partial.json", results)
    finish_report(args.run, results, full_inputs, excluded, selected)


def normalized_input(sample):
    return {key: sample[key] for key in ("sample_id", "cv_text", "requirements")}


def finish_report(run, results, full_inputs, excluded, selected):
    output = run / "evaluation"
    # Unresolved gold labels are excluded from F1, but still test inference abstention.
    unresolved_pairs = {r["pair_id"] for r in excluded}
    abstentions = [selected.review(normalized_input(s)) for s in full_inputs if s["sample_id"] in unresolved_pairs]
    dump_jsonl(output / "unresolved_holdout_reviews.jsonl", abstentions)
    results["holdout_scope"] = {"raw_pairs": len(full_inputs), "raw_requirements": sum(len(s["requirements"]) for s in full_inputs),
                                "excluded_requirements": len(excluded), "gold_human_reviewed": False,
                                "score_mae_scope": "eligible criteria only; partial score for pairs with excluded gold",
                                "abstained_unresolved_pairs": sum(r["score"] is None for r in abstentions),
                                "unresolved_pairs": len(unresolved_pairs)}
    hold = results["holdout"]
    passed = (hold["paired_bootstrap_vs_v1"]["delta_f1_ci95"][0] > 0
              and hold["selected"]["by_kind"]["professional"]["accuracy"] >= hold["v1"]["by_kind"]["professional"]["accuracy"]
              and hold["selected"]["score_mae"] <= hold["v1"]["score_mae"])
    results["decision"] = {"synthetic_pilot_gate_passed": bool(passed), "baseline_replaced": False,
                           "production_validated": False, "github_published": False,
                           "reason": "Holdout is a small same-generator synthetic set; require real human gold before production."}
    write_json(output / "results.json", results)
    write_json(run / "evaluation_complete.json", {"results_sha256": file_hash(output / "results.json"),
                                                       "decision": results["decision"]})
    print(json.dumps({k: {m: round(v[m]["macro_f1"], 4) for m in ("v1", "augmentation_r1", "selected", "rule_with_v1_fallback")}
                      for k, v in results.items() if k in ("historical_test", "holdout")}, indent=2), flush=True)


def recover_report(run, protocol, complete):
    """Original pass failed AFTER writing both prediction CSVs, before reporting."""
    output = run / "evaluation"
    if not (run / "holdout_open_receipt.json").exists() or (run / "evaluation_complete.json").exists():
        raise ValueError("Recovery requires an incomplete, already opened evaluation")
    recovery_path = run / "report_recovery.json"
    if recovery_path.exists(): raise FileExistsError(recovery_path)
    selected = Reviewer(run / "selected_artifact")
    if selected.manifest["classifier_sha256"] != complete["artifact_classifier_sha256"]:
        raise ValueError("Frozen selected weights changed")
    paths = [output / f"{split}_{kind}" for split in ("historical_test", "holdout")
             for kind in ("predictions.csv", "context.jsonl")]
    write_json(recovery_path, {"reason": "Report smoke check passed both jd_text and requirements; project standardized input only.",
               "started_at_unix": time.time(), "source_predictions": {p.name: file_hash(p) for p in paths},
               "original_evaluation_script_sha256": protocol["source_hashes"]["evaluate_evidence.py"],
               "recovery_evaluation_script_sha256": file_hash(Path(__file__)),
               "classifier_unchanged": complete["artifact_classifier_sha256"],
               "candidate_selection_repeated": False, "scored_holdout_predictions_repeated": False})
    results = {}
    for split, method in (("historical_test", "crossed_jd_cv"), ("holdout", "jd")):
        samples = read_jsonl(output / f"{split}_context.jsonl")
        with (output / f"{split}_predictions.csv").open(encoding="utf-8", newline="") as f: rows = list(csv.DictReader(f))
        expected = [(s["sample_id"], r["id"]) for s in samples for r in s["requirements"]]
        if [(r["pair_id"], r["requirement_id"]) for r in rows] != expected: raise ValueError("Prediction order mismatch")
        np.testing.assert_array_equal([r["y_true"] for r in rows], target_labels(samples))
        v1, prev, new = (np.array([r[key] for r in rows]) for key in ("pred_v1", "pred_previous", "pred_new"))
        rules = [r["pred_rule"] for r in rows]
        rule_pred = np.array([a or b for a, b in zip(rules, v1)])
        analyses = [analyze(s["cv_text"], r["text"]) for s in samples for r in s["requirements"]]
        results[split] = {"v1": detailed_metrics(samples, v1), "augmentation_r1": detailed_metrics(samples, prev),
                          "selected": detailed_metrics(samples, new), "rule_with_v1_fallback": detailed_metrics(samples, rule_pred),
                          "rule_coverage": sum(bool(x) for x in rules)/len(rules),
                          "unresolved_input_requirements": sum(bool(a["review_reasons"]) for a in analyses),
                          "elapsed_seconds": None, "metrics_recovered_from_frozen_csv": True,
                          "paired_bootstrap_vs_v1": paired_bootstrap(samples, v1, new, method),
                          "paired_bootstrap_vs_aug_r1": paired_bootstrap(samples, prev, new, method)}
    review_dir = ROOT.parent / "datasets/human_review_round1"
    if file_hash(review_dir / "holdout_sealed.zip") != protocol["holdout_zip_sha256"]: raise ValueError("Holdout changed")
    with ZipFile(review_dir / "holdout_sealed.zip") as z:
        full_inputs = [json.loads(s) for s in z.read("inputs_blind.jsonl").decode().splitlines() if s.strip()]
    excluded = read_jsonl(output / "holdout_excluded.jsonl")
    finish_report(run, results, full_inputs, excluded, selected)


if __name__ == "__main__": main()
