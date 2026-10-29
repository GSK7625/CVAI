"""Recompute uploaded E5 metrics and diagnose errors without rerunning the model."""
import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from pipeline import LABELS, file_hash, metrics, read_jsonl, weighted_score, write_json


def analyze(archive, dataset):
    with ZipFile(archive) as z:
        if sum(i.file_size for i in z.infolist()) > 20_000_000:
            raise ValueError("ZIP kết quả vượt 20 MB; cần kiểm tra riêng")
        contents = {}
        for name in ("metrics.json", "test_predictions.jsonl"):
            matches = [i for i in z.infolist() if PurePosixPath(i.filename).name == name]
            if len(matches) != 1:
                raise ValueError(f"Cần đúng một {name}")
            contents[name] = z.read(matches[0]).decode("utf-8")
    supplied = json.loads(contents["metrics.json"])
    predictions = [json.loads(line) for line in contents["test_predictions.jsonl"].splitlines() if line.strip()]
    samples = read_jsonl(dataset / "test.jsonl")
    by_id = {r["sample_id"]: r for r in predictions}
    if len(by_id) != len(predictions) or set(by_id) != {s["sample_id"] for s in samples}:
        raise ValueError("Trùng hoặc thiếu sample ID; không được báo như cùng một test")
    candidates = {r["cv_group"]: r for r in read_jsonl(dataset / "provenance/candidates.jsonl")}
    jobs = {r["jd_group"]: r for r in read_jsonl(dataset / "provenance/jobs.jsonl")}
    patterns, groups = Counter(), defaultdict(lambda: {"n": 0, "correct": 0})
    flat_pred, score_errors, wrong_cases, pair_errors = [], [], [], []
    top1_hits = top3_hits = positive = wrong_positive = wrong_positive_in_top3 = 0
    correct_pairs = 0
    for sample in samples:
        pred = by_id[sample["sample_id"]]
        assessments = pred["assessments"]
        indexed = {a["id"]: a for a in assessments}
        if len(indexed) != len(assessments) or set(indexed) != {r["id"] for r in sample["requirements"]}:
            raise ValueError("Trùng hoặc thiếu requirement ID")
        candidate, job = candidates[sample["cv_group"]], jobs[sample["jd_group"]]
        gold_by_id = {a["id"]: a for a in sample["target"]["assessments"]}
        statuses, pair_wrong = {}, 0
        for req, spec in zip(sample["requirements"], job["specs"]):
            assessment = indexed[req["id"]]
            if assessment["weight"] != req["weight"] or assessment["requirement_text"] != req["text"]:
                raise ValueError("Nội dung/weight khác test gốc")
            guess, gold = assessment["status"], gold_by_id[req["id"]]
            if guess not in LABELS:
                raise ValueError("Nhãn dự đoán không hợp lệ")
            statuses[req["id"]] = guess
            flat_pred.append(guess)
            contexts = assessment["retrieved_context"]
            for c in contexts:
                if sample["cv_text"][c["start"]:c["end"]] != c["text"]:
                    raise ValueError("Đoạn truy xuất không khớp CV gốc")
            in_top3 = bool(gold["evidence"] and any(gold["evidence"] in c["text"] for c in contexts))
            if gold["evidence"]:
                positive += 1
                top3_hits += in_top3
                top1_hits += bool(contexts and gold["evidence"] in contexts[0]["text"])
            correct = guess == gold["status"]
            for group in ("all", "track:" + candidate["track"], "kind:" + spec["kind"]):
                groups[group]["n"] += 1
                groups[group]["correct"] += correct
            if not correct:
                pair_wrong += 1
                if gold["evidence"]:
                    wrong_positive += 1
                    wrong_positive_in_top3 += in_top3
                state = "role_months" if spec["kind"] == "experience" else candidate["facts"].get(spec.get("tech"), {}).get("state", "absent")
                pattern = f"{spec['kind']} / {state}: {gold['status']} -> {guess}"
                patterns[pattern] += 1
                wrong_cases.append({"sample_id": sample["sample_id"], "requirement_id": req["id"],
                                    "requirement": req["text"], "gold": gold["status"], "predicted": guess,
                                    "gold_evidence": gold["evidence"], "gold_excerpt_in_top3": in_top3,
                                    "retrieved_context": contexts, "pattern": pattern})
        expected = {a["id"]: a["status"] for a in sample["target"]["assessments"]}
        actual_score = weighted_score(sample["requirements"], statuses)
        target_score = weighted_score(sample["requirements"], expected)
        if abs(actual_score - pred["score"]) > 0.000051:
            raise ValueError("Điểm lưu không khớp trạng thái/weight")
        expected_contributions = [100 * r["weight"] * {"met": 1, "partial": 0.5, "not_evidenced": 0}[statuses[r["id"]]] / sum(r["weight"] for r in sample["requirements"]) for r in sample["requirements"]]
        if any(abs(indexed[r["id"]]["contribution_points"] - value) > 0.000051
               for r, value in zip(sample["requirements"], expected_contributions)):
            raise ValueError("Điểm từng yêu cầu không khớp công thức")
        signed_error = actual_score - target_score
        score_errors.append(signed_error)
        if not pair_wrong:
            correct_pairs += 1
        pair_errors.append({"sample_id": sample["sample_id"], "predicted_score": actual_score,
                            "gold_score": target_score, "signed_error": signed_error, "wrong_requirements": pair_wrong})
    recalculated = metrics(samples, flat_pred)

    def check(expected, actual, path="metrics"):
        if isinstance(expected, dict):
            for key, value in expected.items():
                check(value, actual[key], path + "." + key)
        elif isinstance(expected, list):
            if expected != actual:
                raise ValueError(f"Không khớp {path}")
        elif not math.isclose(expected, actual, rel_tol=1e-8, abs_tol=1e-8):
            raise ValueError(f"Không khớp {path}")
    check(recalculated, supplied)
    if top3_hits / positive != supplied["retrieval_gold_excerpt_recall_at_3"]:
        raise ValueError("Không khớp recall truy xuất")
    return {
        "archive_sha256": file_hash(archive), "test_sha256": file_hash(dataset / "test.jsonl"),
        "metrics_reproduced": True, "metrics": supplied,
        "all_labels_correct_pairs": correct_pairs, "total_pairs": len(samples),
        "under_scored_pairs": sum(e < -1e-8 for e in score_errors),
        "over_scored_pairs": sum(e > 1e-8 for e in score_errors),
        "exact_score_pairs": sum(abs(e) <= 1e-8 for e in score_errors),
        "mean_signed_score_error": sum(score_errors) / len(score_errors),
        "gold_positive_requirements": positive, "top1_gold_excerpt_hits": top1_hits, "top3_gold_excerpt_hits": top3_hits,
        "wrong_positive_requirements": wrong_positive, "wrong_positive_with_gold_in_top3": wrong_positive_in_top3,
        "wrong_label_patterns": dict(patterns.most_common()), "groups": dict(groups),
        "largest_score_errors": sorted(pair_errors, key=lambda p: abs(p["signed_error"]), reverse=True)[:15],
        "wrong_cases": wrong_cases,
        "scope": "Previously inspected controlled synthetic test, structured requirements; not a raw-JD parser or real-world benchmark.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "datasets/cvai_v1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = analyze(args.zip, args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    compact = {k: v for k, v in result.items() if k not in {"metrics", "wrong_cases"}}
    print(json.dumps(compact, ensure_ascii=False, indent=2))
