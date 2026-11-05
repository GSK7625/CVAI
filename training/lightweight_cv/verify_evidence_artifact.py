"""Verify frozen export, serving semantics and real single-process CPU latency."""
import argparse
import importlib.util
import json
import time
from pathlib import Path
import numpy as np

from evidence_features import analyze, combine_features
from pipeline import (ClassifierHead, Reviewer, file_hash, read_jsonl, write_json)

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    a = p.parse_args()
    output = a.run / "serving_verification.json"
    if output.exists(): raise FileExistsError(output)
    started = time.perf_counter()
    reviewer = Reviewer(a.run / "selected_artifact", device="cpu", threads=2)
    loaded = time.perf_counter()-started
    example = json.loads((ROOT / "example_raw_input.json").read_text(encoding="utf-8"))
    reviews, latency = [], []
    for _ in range(6):
        begin = time.perf_counter()
        reviews.append(reviewer.review(example))
        latency.append(time.perf_counter()-begin)
    for r in reviews:
        assert r["status"] == "ready"
        assert {x["requirement_text"]: x["status"] for x in r["assessments"]} == {
            "Paid experience in backend developer totaling 12 months or more.": "partial",
            "Foundational understanding of Docker.": "met",
            "Evidence of Python used during paid employment.": "met",
            "Project-level experience applying SQL.": "met"}
        assert abs(r["score"] - 87.5) < 1e-6
        assert abs(sum(x["contribution_points"] for x in r["assessments"]) - r["score"]) < .001
    write_json(a.run / "example_review.json", reviews[0])
    unknown = {"sample_id": "unknown-context", "cv_text": "A team mentioned Python; my own use is unspecified.",
               "requirements": [{"id": "r1", "text": "Basic familiarity with Python.", "weight": 1}]}
    assert reviewer.review(unknown)["score"] is None
    # Same runtime head reloaded from numeric arrays must retain frozen dev predictions.
    head = ClassifierHead(a.run / "selected_artifact/classifier.npz")
    for split in ("old_validation", "new_validation"):
        with np.load(a.run / f"features/{split}.npz", allow_pickle=False) as x:
            features = combine_features(x["base"], x["structured"], reviewer.manifest["feature_mode"])
            np.testing.assert_array_equal(head.predict(features), x["labels"])
    # Distinguish raw classifier metrics from the scores actually released to users.
    samples = read_jsonl(a.run / "evaluation/holdout_context.jsonl")
    excluded = read_jsonl(a.run / "evaluation/holdout_excluded.jsonl")
    withheld = {s["pair_id"] for s in excluded}
    unresolved = []
    for s in samples:
        for req in s["requirements"]:
            reasons = analyze(s["cv_text"], req["text"])["review_reasons"]
            if reasons:
                withheld.add(s["sample_id"])
                unresolved.append({"pair_id": s["sample_id"], "id": req["id"], "reasons": reasons})
    coverage = {"raw_pairs": len(samples), "raw_requirements": sum(len(s["requirements"]) for s in samples)+len(excluded),
                "eligible_requirements": sum(len(s["requirements"]) for s in samples),
                "eligible_but_requires_review": len(unresolved), "unresolved_gold_requirements": len(excluded),
                "score_ready_pairs": len(samples)-len(withheld), "score_withheld_pairs": len(withheld),
                "details": unresolved, "all_raw_classifier_predictions_correct_is_not_full_coverage": True}
    write_json(a.run / "evaluation/deployment_coverage.json", coverage)
    rss = None
    if importlib.util.find_spec("psutil"):
        import psutil
        rss = psutil.Process().memory_info().rss / 1024**2
    result = {"classifier_sha256": file_hash(a.run / "selected_artifact/classifier.npz"),
              "feature_parser_sha256": file_hash(ROOT / "evidence_features.py"),
              "serving_pipeline_sha256": file_hash(ROOT / "pipeline.py"),
              "cold_load_seconds": loaded, "request_seconds": latency,
              "warm_p50_seconds": float(np.median(latency[1:])), "warm_p95_seconds": float(np.percentile(latency[1:], 95)),
              "current_process_rss_mib": rss, "cpu_threads": 2, "environment": "local Windows CPU, not the target VPS",
              "raw_jd_demo_score": reviews[0]["score"], "unknown_context_score_withheld": True,
              "validation_numeric_reload_matches": True,
              "baseline_classifier_sha256": file_hash(ROOT / "e5-small-classifier-v1-deploy/artifact/classifier.npz")}
    write_json(output, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
