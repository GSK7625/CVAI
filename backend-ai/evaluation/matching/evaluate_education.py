"""
Dedicated evaluation runner for Education Matching and Scoring.

Evaluates deterministic 5-tier ordinal education hierarchy, word-boundary protection,
highest-degree wins semantics, unknown degrees, and score bounding without requiring LLMs
or embedding models.

USAGE:
    python -m evaluation.matching.evaluate_education [--dataset PATH]
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from app.domain.matching.education_match import (
    calculate_education_match,
)

DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "education_cases.json"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Evaluate FutureCV Education Matching and Scoring Robustness")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to education cases JSON dataset",
    )
    return parser.parse_args()


def run_education_evaluation(raw_cases: list[dict[str, Any]]) -> dict[str, int]:
    """Execute education matching evaluation and print formatted verification report."""
    print("=" * 88)
    print("FutureCV - Dedicated Education Matching & Scoring Regression Evaluation")
    print(f"Total test cases: {len(raw_cases)}")
    print("=" * 88)

    passed_count = 0
    failed_count = 0

    header = f"{'Case ID':<40} | {'Req Edu':<24} | {'Score (Exp/Act)':<16} | {'Result':<8}"
    print(header)
    print("-" * 96)

    for item in raw_cases:
        cid = item.get("id", "unknown")
        cand_degrees = item.get("candidate_degrees", [])
        req_edu = item.get("required_education")
        expected_score = float(item.get("expected_score", 0.0))

        match_result = calculate_education_match(
            candidate_degrees=cand_degrees,
            required_education=req_edu,
        )

        score_ok = abs(match_result.score - expected_score) < 0.05
        passed = score_ok

        raw_req_str = str(req_edu) if req_edu is not None else "None (Neutral)"
        req_str = (raw_req_str[:21] + "...") if len(raw_req_str) > 24 else raw_req_str
        score_str = f"{expected_score:.1f} / {match_result.score:.1f}"
        status_str = "PASS" if passed else "FAIL"

        if passed:
            passed_count += 1
        else:
            failed_count += 1

        print(f"{cid:<40} | {req_str:<24} | {score_str:<16} | {status_str:<8}")

    print("=" * 88)
    print("EVALUATION SUMMARY")
    print("=" * 88)
    print(f"Total Cases:     {len(raw_cases)}")
    print(f"Passed:          {passed_count}")
    print(f"Failed:          {failed_count}")
    print("=" * 88)

    return {"total": len(raw_cases), "passed": passed_count, "failed": failed_count}


def main() -> None:
    """Main CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    if not args.dataset.exists():
        print(f"[ERROR] Education dataset not found at: {args.dataset}", file=sys.stderr)
        sys.exit(1)

    try:
        with args.dataset.open(encoding="utf-8") as f:
            cases = json.load(f)
    except Exception as exc:
        print(f"[ERROR] Failed to load dataset: {exc}", file=sys.stderr)
        sys.exit(1)

    results = run_education_evaluation(cases)
    if results["failed"] > 0:
        print("[FAIL] One or more education evaluation cases failed.", file=sys.stderr)
        sys.exit(1)

    print("[SUCCESS] All education evaluation cases passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
