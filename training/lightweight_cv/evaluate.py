"""Evaluate a frozen full artifact once; include first-request and warm latency."""
import argparse
import json
import time
from pathlib import Path

import numpy as np

from pipeline import Reviewer, features_for_samples, load_splits, metrics, render_review, threshold_predict, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    output = args.artifact_dir / f"evaluation_{args.device}"
    if output.exists():
        raise FileExistsError("Đã có đánh giá. Giữ nguyên kết quả; dùng bản sao artifact cho lần đo khác.")
    splits, hashes = load_splits(args.data_dir)
    started = time.perf_counter()
    reviewer = Reviewer(args.artifact_dir, device=args.device, threads=args.threads)
    load_seconds = time.perf_counter() - started
    if hashes != reviewer.manifest["data_hashes"]:
        raise ValueError("Dataset đã đổi so với lúc train; không ghi đè benchmark cũ")
    output.mkdir()
    predicted, baseline, latency, records, reviews = [], [], [], [], []
    for index, sample in enumerate(splits["test"]):
        started = time.perf_counter()
        features, retrieved = features_for_samples([sample], reviewer.encoder)
        labels = reviewer.head.predict(features)
        latency.append(time.perf_counter() - started)
        predicted.extend(labels.tolist())
        baseline.extend(threshold_predict(features[:, -3], *reviewer.manifest["baseline_thresholds"]).tolist())
        records.extend(retrieved)
        statuses = dict(zip([r["id"] for r in sample["requirements"]], labels))
        reviews.append(render_review(sample, statuses, retrieved))
        if (index + 1) % 25 == 0:
            print(f"Test: {index + 1}/{len(splits['test'])}", flush=True)
    result = metrics(splits["test"], predicted)
    supports = {(s["sample_id"], a["id"]): a["evidence"] for s in splits["test"] for a in s["target"]["assessments"] if a["evidence"]}
    hits = sum(any(evidence in c["text"] for c in r["retrieved"])
               for r in records if (evidence := supports.get((r["sample_id"], r["requirement_id"]))))
    result.update(device=args.device, threads=args.threads, encoder_load_seconds=load_seconds,
                  first_request_seconds=latency[0], warm_latency_p50_seconds=float(np.median(latency[1:] or latency)),
                  warm_latency_p95_seconds=float(np.percentile(latency[1:] or latency, 95)),
                  retrieval_gold_excerpt_recall_at_3=hits / len(supports) if supports else None,
                  retrieval_support=len(supports), human_reviewed=False, external_real_world_validation=False)
    result["cosine_baseline"] = metrics(splits["test"], baseline)
    result["model_profile"] = {key: reviewer.manifest[key] for key in
                               ("feature_version", "encoder_revision", "classifier_sha256")}
    result["data_hashes"] = hashes
    try:
        import resource
        import sys
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result["peak_process_rss_mib"] = peak / (1024 * 1024 if sys.platform == "darwin" else 1024)
    except ImportError:
        result["peak_process_rss_mib"] = None
    write_json(output / "metrics.json", result)
    (output / "test_predictions.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in reviews), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
