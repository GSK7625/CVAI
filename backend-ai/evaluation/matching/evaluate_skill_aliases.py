"""
Dedicated evaluation runner for Skill Normalization and Alias Equivalence.

Evaluates high-confidence alias equivalence and strict false-positive prevention
without requiring LLMs or embedding models (100% deterministic domain logic).

USAGE:
    python -m evaluation.matching.evaluate_skill_aliases [--dataset PATH]
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from app.domain.matching.skill_match import calculate_skill_match

DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "skill_alias_cases.json"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Evaluate FutureCV Skill Normalization and Alias Robustness")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to skill alias cases JSON dataset",
    )
    return parser.parse_args()


def run_skill_alias_evaluation(raw_cases: list[dict[str, Any]]) -> dict[str, int]:
    """Execute skill alias evaluation and print formatted verification report."""
    print("=" * 80)
    print("FutureCV - Dedicated Skill Alias Regression Evaluation")
    print(f"Total test cases: {len(raw_cases)}")
    print("=" * 80)

    passed_count = 0
    failed_count = 0
    false_positives = 0
    false_negatives = 0

    header = f"{'Case ID':<38} | {'Expected':<12} | {'Actual':<12} | {'Result':<8}"
    print(header)
    print("-" * 80)

    for item in raw_cases:
        cid = item.get("id", "unknown")
        cand_skills = item.get("candidate_skills", [])
        req_skills = item.get("required_skills", [])
        expected_matched = item.get("expected_matched", False)

        result = calculate_skill_match(
            candidate_skills=cand_skills,
            required_skills=req_skills,
        )

        actual_matched = (
            result.matched_required_count == result.total_required_count and result.total_required_count > 0
        )

        exp_str = "MATCHED" if expected_matched else "NOT MATCHED"
        act_str = "MATCHED" if actual_matched else "NOT MATCHED"

        if actual_matched == expected_matched:
            verdict = "PASS"
            passed_count += 1
        else:
            verdict = "FAIL"
            failed_count += 1
            if actual_matched and not expected_matched:
                false_positives += 1
            elif not actual_matched and expected_matched:
                false_negatives += 1

        print(f"{cid:<38} | {exp_str:<12} | {act_str:<12} | {verdict:<8}")

    print("=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Cases:     {len(raw_cases)}")
    print(f"Passed:          {passed_count}")
    print(f"Failed:          {failed_count}")
    print(f"False Positives: {false_positives}")
    print(f"False Negatives: {false_negatives}")
    print("=" * 80)

    return {
        "total": len(raw_cases),
        "passed": passed_count,
        "failed": failed_count,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    if not args.dataset.exists():
        print(f"Error: Dataset not found at '{args.dataset}'", file=sys.stderr)
        sys.exit(1)

    with args.dataset.open(encoding="utf-8") as f:
        cases = json.load(f)

    metrics = run_skill_alias_evaluation(cases)
    if metrics["failed"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
