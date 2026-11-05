"""Locked development experiment for frozen E5 + explicit evidence features.

Training never opens the sealed holdout. Run evaluate_evidence.py only after
the selected recipe, weights, feature code and validation decision are frozen.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import shutil
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

from evidence_features import (FEATURE_NAMES, FEATURE_VERSION, KINDS, analyze,
                               combine_features, requirement_spec, rule_label, structured_features)
from pipeline import (ClassifierHead, Reviewer, features_for_samples, file_hash,
                      load_splits, metrics, read_jsonl, save_classifier, target_labels, write_json)

ROOT = Path(__file__).resolve().parent
CANDIDATES = [
    {"name": "structured-mlp32", "mode": "structured", "alpha": .1, "minimal_pairs": False},
    {"name": "compact-mlp32", "mode": "compact", "alpha": .1, "minimal_pairs": False},
    {"name": "full-mlp64-a0.1", "mode": "full", "alpha": .1, "minimal_pairs": False},
    {"name": "full-mlp64-a1", "mode": "full", "alpha": 1., "minimal_pairs": False},
    {"name": "compact-mlp32-minimal", "mode": "compact", "alpha": .1, "minimal_pairs": True},
    {"name": "full-mlp64-minimal", "mode": "full", "alpha": .1, "minimal_pairs": True},
]


def dump_jsonl(path, rows):
    with Path(path).open("x", encoding="utf-8", newline="\n") as f:
        for row in rows: f.write(json.dumps(row, ensure_ascii=False) + "\n")


def detailed_metrics(samples, predictions):
    result = metrics(samples, predictions)
    gold = target_labels(samples)
    kinds = np.array([requirement_spec(r["text"])["kind"] for s in samples for r in s["requirements"]])
    result["by_kind"] = {kind: {"support": int(sum(kinds == kind)),
                              "accuracy": float(accuracy_score(gold[kinds == kind], predictions[kinds == kind]))}
                         for kind in KINDS if np.any(kinds == kind)}
    return result


def eligible(result, references):
    for split in ("old_validation", "new_validation"):
        # Guard against both released v1 and the previous augmented model.
        floor = max(ref[split]["macro_f1"] for ref in references)
        if result[split]["macro_f1"] < floor - .005: return False
        for kind in ("basic", "practical", "professional", "experience"):
            floor = max(ref[split]["by_kind"].get(kind, {"accuracy": 0})["accuracy"] for ref in references)
            if result[split]["by_kind"].get(kind, {"accuracy": 0})["accuracy"] < floor - .01:
                return False
    return True


def choose(results, references):
    safe = [r for r in results if eligible(r, references)]
    if not safe: return None
    # A structured-only ablation can win; do not pretend E5 helped if it did not.
    return max(safe, key=lambda r: (round((r["old_validation"]["macro_f1"] + r["new_validation"]["macro_f1"]) / 2, 10),
                                   -r["dimension"], not r["minimal_pairs"], r["name"]))


def minimal_pairs(train, limit=160):
    """Training-only counterfactual criteria on existing CVs, explicitly rule-labelled."""
    found, output = set(), []
    # Shuffle by stable hash to avoid taking the first job family only.
    ordered = sorted(train, key=lambda s: hashlib.sha256(s["sample_id"].encode()).hexdigest())
    for sample in ordered:
        gold = {a["id"]: a["status"] for a in sample["target"]["assessments"]}
        for req in sample["requirements"]:
            analysis = analyze(sample["cv_text"], req["text"])
            skill = analysis["spec"].get("skill")
            if not skill or (sample["cv_group"], skill) in found: continue
            if rule_label(analysis) is None or rule_label(analysis) != gold[req["id"]]: continue
            if len(found) >= limit: return output
            found.add((sample["cv_group"], skill))
            criteria = [f"Basic familiarity with {skill}.", f"Hands-on use of {skill} in an independent project.",
                        f"Use of {skill} in a paid technical role."]
            requirements = [{"id": f"r{i+1}", "text": t, "weight": i+1} for i, t in enumerate(criteria)]
            assessments = []
            for r in requirements:
                a = analyze(sample["cv_text"], r["text"])
                label = rule_label(a)
                contexts = [c for c in a["contexts"] if c["kind"] in {"paid", "project", "course", "listed"}]
                evidence = contexts[0]["text"] if label != "not_evidenced" else None
                assessments.append({"id": r["id"], "status": label, "evidence": evidence})
            key = hashlib.sha256((sample["cv_group"] + skill).encode()).hexdigest()[:16]
            output.append({"sample_id": "minimal-" + key, "cv_group": sample["cv_group"],
                           "jd_group": "derived-train-" + key, "parent_sample_id": sample["sample_id"],
                           "cv_text": sample["cv_text"], "requirements": requirements,
                           "target": {"assessments": assessments}, "label_source": "rule_counterfactual_unreviewed"})
    return output


def fit_head(x, y, spec, seed, threads):
    head = MLPClassifier(hidden_layer_sizes=(64 if spec["mode"] == "full" else 32,),
                         alpha=spec["alpha"], max_iter=500, early_stopping=False, random_state=seed)
    model = make_pipeline(StandardScaler(), head)
    with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=threads):
        warnings.simplefilter("always")
        model.fit(x, y, mlpclassifier__sample_weight=compute_sample_weight("balanced", y))
    return model, {"iterations": head.n_iter_, "loss": float(head.loss_),
                   "warnings": [str(w.message) for w in caught]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError("Refusing to overwrite experiment")
    dataset = ROOT.parent / "datasets/cvai_augmented_r1"
    old_dataset = ROOT.parent / "datasets/cvai_v1"
    baseline_path = ROOT / "artifact"
    previous_path = ROOT / "artifacts/augmentation-r1"
    data, hashes = load_splits(dataset)
    old, old_hashes = load_splits(old_dataset)
    if hashes["test"] != old_hashes["test"]: raise ValueError("Historical test modified")
    groups = {"old_validation": old["validation"], "new_validation": read_jsonl(dataset / "new_validation.jsonl")}
    args.output.mkdir(parents=True)
    code_names = ("evidence_features.py", "jd_parser.py", "pipeline.py", "optimize_evidence.py", "evaluate_evidence.py")
    code_hashes = {name: file_hash(ROOT / name) for name in code_names}
    protocol = {"experiment": "evidence-r1", "candidates": CANDIDATES, "seed": 42,
                "stability_seeds_after_selection": [43, 44], "encoder_frozen": True,
                "features": FEATURE_NAMES, "base_dimension": 1923, "data_hashes": hashes,
                "training_selection_never_opens_holdout": True, "historical_test_previously_observed": True,
                "selection": "mean of old/new validation macro-F1; ties prefer fewer features, then no minimal pairs",
                "gates": "on BOTH validations: macro-F1 >= max(v1,aug-r1)-0.005; every kind accuracy >= max(v1,aug-r1)-0.01",
                "holdout_gate": "paired JD-cluster 95% lower delta-F1 bound > 0 vs v1; paid accuracy and MAE not worse; synthetic pilot only",
                "minimal_pair_max_groups": 160, "minimal_pair_source": "train only; no new independent CVs",
                "source_hashes": code_hashes, "baseline_classifier_sha256": file_hash(baseline_path / "classifier.npz"),
                "previous_classifier_sha256": file_hash(previous_path / "classifier.npz"),
                "holdout_zip_sha256": file_hash(ROOT.parent / "datasets/human_review_round1/holdout_sealed.zip"),
                "versions": {n: importlib.metadata.version(n) for n in ("torch", "transformers", "numpy", "scikit-learn")}}
    write_json(args.output / "protocol.json", protocol)
    source = args.output / "executed_sources"
    source.mkdir()
    for name in code_names: shutil.copy2(ROOT / name, source / name)
    started = time.perf_counter()
    baseline = Reviewer(baseline_path, threads=args.threads)
    previous = ClassifierHead(previous_path / "classifier.npz")
    contrast = minimal_pairs(data["train"])
    dump_jsonl(args.output / "minimal_pairs_train.jsonl", contrast)
    cache = args.output / "features"
    cache.mkdir()
    encoded = {}
    for name, samples in {"train": data["train"], "minimal": contrast, **groups}.items():
        print(f"Encoding {name}: {len(samples)} pairs", flush=True)
        base, records = features_for_samples(samples, baseline.encoder)
        structured, analyses = structured_features(samples)
        encoded[name] = base, structured, target_labels(samples)
        np.savez_compressed(cache / f"{name}.npz", base=base, structured=structured, labels=target_labels(samples))
        if "validation" in name:
            dump_jsonl(cache / f"{name}_analysis.jsonl", analyses)
    references = []
    for name, head in (("released-v1", baseline.head), ("augmentation-r1", previous)):
        references.append({"name": name, **{split: detailed_metrics(samples, head.predict(encoded[split][0]))
                                           for split, samples in groups.items()}})
    write_json(args.output / "validation_references.json", references)
    rules = {}
    for split, samples in groups.items():
        _, analyses = structured_features(samples)
        labels = [rule_label(a) for a in analyses]
        fallback = baseline.head.predict(encoded[split][0])
        predicted = np.array([p if p is not None else f for p, f in zip(labels, fallback)])
        rules[split] = {**detailed_metrics(samples, predicted), "coverage": sum(x is not None for x in labels)/len(labels),
                        "description": "Rule baseline; unknown falls back to v1 only for comparable full-coverage metrics"}
    write_json(args.output / "rule_baseline_validation.json", rules)
    results, fitted = [], {}
    for spec in CANDIDATES:
        base, structured, y = encoded["train"]
        x = combine_features(base, structured, spec["mode"])
        if spec["minimal_pairs"]:
            mb, ms, my = encoded["minimal"]
            x, y = np.r_[x, combine_features(mb, ms, spec["mode"])], np.r_[y, my]
        model, fit = fit_head(x, y, spec, 42, args.threads)
        candidate = args.output / spec["name"]
        candidate.mkdir()
        save_classifier(candidate / "classifier.npz", model.steps[0][1], model.steps[1][1])
        exported = ClassifierHead(candidate / "classifier.npz")
        result = {**spec, "dimension": x.shape[1], "n_train_requirements": len(y), "fit": fit}
        for split, samples in groups.items():
            b, s, _ = encoded[split]
            v = combine_features(b, s, spec["mode"])
            pred = model.predict(v)
            np.testing.assert_array_equal(exported.predict(v), pred)
            result[split] = detailed_metrics(samples, pred)
        result["eligible"] = eligible(result, references)
        results.append(result)
        fitted[spec["name"]] = (x, y)
        write_json(args.output / "validation_candidates.json", results)
        print(f"{spec['name']}: F1 old/new={result['old_validation']['macro_f1']:.4f}/{result['new_validation']['macro_f1']:.4f}, eligible={result['eligible']}", flush=True)
    chosen = choose(results, references)
    write_json(args.output / "selection_locked.json", {"selected": chosen,
               "protocol_sha256": file_hash(args.output / "protocol.json"), "holdout_opened": False})
    if chosen is None:
        print("No candidate passed validation gates. Baseline retained.", flush=True)
        return
    artifact = args.output / "selected_artifact"
    artifact.mkdir()
    shutil.copy2(args.output / chosen["name"] / "classifier.npz", artifact / "classifier.npz")
    shutil.copytree(baseline_path / "encoder", artifact / "encoder")
    shutil.copy2(baseline_path / "THIRD_PARTY.md", artifact / "THIRD_PARTY.md")
    manifest = copy.deepcopy(baseline.manifest)
    manifest.update(feature_version=FEATURE_VERSION, feature_mode=chosen["mode"], feature_dimension=chosen["dimension"],
                    feature_code_hashes={n: code_hashes[n] for n in ("evidence_features.py", "jd_parser.py")},
                    classifier_sha256=file_hash(artifact / "classifier.npz"), selected_classifier=chosen["name"],
                    data_hashes=hashes, n_train_requirements=chosen["n_train_requirements"], n_validation_requirements=587,
                    minimal_pairs_sha256=file_hash(args.output / "minimal_pairs_train.jsonl"),
                    training_method="Frozen E5 + train-only scaler + explicit evidence MLP; no output rule override",
                    experiment="evidence-r1", versions=protocol["versions"], elapsed_seconds=time.perf_counter()-started,
                    deployment_status="candidate_pending_holdout", all_labels_human_reviewed=False,
                    limitations="Synthetic rubric benchmark. Explicit English context only; unresolved inputs require review. No real CV validation.")
    write_json(artifact / "manifest.json", manifest)
    stability = []
    x, y = fitted[chosen["name"]]
    for seed in (43, 44):
        model, fit = fit_head(x, y, chosen, seed, args.threads)
        result = {"seed": seed, "fit": fit}
        for split, samples in groups.items():
            b, s, _ = encoded[split]
            result[split] = detailed_metrics(samples, model.predict(combine_features(b, s, chosen["mode"])))
        result["eligible"] = eligible(result, references)
        stability.append(result)
    write_json(args.output / "seed_stability.json", stability)
    write_json(args.output / "training_complete.json", {"selected": chosen["name"], "elapsed_seconds": time.perf_counter()-started,
               "all_stability_seeds_pass": all(r["eligible"] for r in stability),
               "feature_dimension": chosen["dimension"], "artifact_classifier_sha256": file_hash(artifact / "classifier.npz")})
    print("LOCKED:", chosen["name"], "Stability:", all(r["eligible"] for r in stability), flush=True)


if __name__ == "__main__": main()
