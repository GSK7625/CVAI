"""
Dedicated evaluation runner for Experience Matching and Scoring.

Evaluates deterministic experience duration merging, ongoing tokens, career gaps,
precedence rules, and score bounding without requiring LLMs or embedding models.

USAGE:
    python -m evaluation.matching.evaluate_experience [--dataset PATH]
"""

import argparse
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any

from app.contracts.cv import WorkExperienceItem
from app.domain.matching.experience_match import (
    calculate_experience_match,
    calculate_total_experience_years,
)

DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "experience_cases.json"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Evaluate FutureCV Experience Matching and Scoring Robustness")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to experience cases JSON dataset",
    )
    return parser.parse_args()


def run_experience_evaluation(raw_cases: list[dict[str, Any]]) -> dict[str, int]:
    """Execute experience matching evaluation and print formatted verification report."""
    print("=" * 88)
    print("FutureCV - Dedicated Experience Matching & Scoring Regression Evaluation")
    print(f"Total test cases: {len(raw_cases)}")
    print("=" * 88)

    passed_count = 0
    failed_count = 0

    header = f"{'Case ID':<38} | {'Years (Exp/Act)':<16} | {'Score (Exp/Act)':<16} | {'Result':<8}"
    print(header)
    print("-" * 88)

    for item in raw_cases:
        cid = item.get("id", "unknown")
        raw_exps = item.get("work_experience", [])
        req_years = item.get("required_years")
        ref_date_str = item.get("reference_date", "2025-01-01")
        expected_years = float(item.get("expected_candidate_years", 0.0))
        expected_score = float(item.get("expected_score", 0.0))

        ref_date = date.fromisoformat(ref_date_str)
        work_items = [WorkExperienceItem(**exp) for exp in raw_exps]

        actual_years = calculate_total_experience_years(work_items, reference_date=ref_date)
        match_result = calculate_experience_match(
            candidate_years=actual_years,
            required_years=req_years,
        )

        years_ok = abs(actual_years - expected_years) < 0.05
        score_ok = abs(match_result.score - expected_score) < 0.05
        passed = years_ok and score_ok

        years_str = f"{expected_years:.1f} / {actual_years:.1f}"
        score_str = f"{expected_score:.1f} / {match_result.score:.1f}"
        status_str = "PASS" if passed else "FAIL"

        if passed:
            passed_count += 1
        else:
            failed_count += 1

        print(f"{cid:<38} | {years_str:<16} | {score_str:<16} | {status_str:<8}")

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
    args = parse_args()
    if not args.dataset.exists():
        print(f"[ERROR] Experience dataset not found at: {args.dataset}", file=sys.stderr)
        sys.exit(1)

    try:
        with args.dataset.open(encoding="utf-8") as f:
            cases = json.load(f)
    except Exception as exc:
        print(f"[ERROR] Failed to load dataset: {exc}", file=sys.stderr)
        sys.exit(1)

    results = run_experience_evaluation(cases)
    if results["failed"] > 0:
        print("[FAIL] One or more experience evaluation cases failed.", file=sys.stderr)
        sys.exit(1)

    print("[SUCCESS] All experience evaluation cases passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
