"""
Dedicated evaluation runner for Project Domain Relevance Matching.

Evaluates deterministic project technology coverage, canonical alias normalization,
duplicate deduplication, and score bounding without requiring LLMs or embedding models.

USAGE:
    python -m evaluation.matching.evaluate_projects [--dataset PATH]
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from app.contracts.cv import ProjectItem
from app.domain.matching.project_match import evaluate_project_relevance

DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "project_cases.json"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Evaluate FutureCV Project Relevance Matching Robustness")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to project cases JSON dataset",
    )
    return parser.parse_args()


def run_project_evaluation(raw_cases: list[dict[str, Any]]) -> dict[str, int]:
    """Execute project relevance matching evaluation and print formatted report."""
    print("=" * 88)
    print("FutureCV - Dedicated Project Relevance Matching Regression Evaluation")
    print(f"Total test cases: {len(raw_cases)}")
    print("=" * 88)

    passed_count = 0
    failed_count = 0

    header = f"{'Case ID':<44} | {'Relevant (Exp/Act)':<18} | {'Score (Exp/Act)':<16} | {'Result':<8}"
    print(header)
    print("-" * 88)

    for item in raw_cases:
        cid = item.get("id", "unknown")
        raw_projects = item.get("projects", [])
        req_skills = item.get("required_skills", [])
        pref_skills = item.get("preferred_skills", [])
        expected_rel_count = int(item.get("expected_relevant_count", 0))
        expected_score = float(item.get("expected_score", 0.0))

        project_items = [ProjectItem(**p) for p in raw_projects]

        match_result = evaluate_project_relevance(
            projects=project_items,
            required_skills=req_skills,
            preferred_skills=pref_skills,
        )

        score_ok = abs(match_result.project_score - expected_score) < 0.05
        count_ok = match_result.relevant_project_count == expected_rel_count
        passed = score_ok and count_ok

        rel_str = f"{expected_rel_count} / {match_result.relevant_project_count}"
        score_str = f"{expected_score:.1f} / {match_result.project_score:.1f}"
        status_str = "PASS" if passed else "FAIL"

        if passed:
            passed_count += 1
        else:
            failed_count += 1

        print(f"{cid:<44} | {rel_str:<18} | {score_str:<16} | {status_str:<8}")

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
        print(f"[ERROR] Project dataset not found at: {args.dataset}", file=sys.stderr)
        sys.exit(1)

    try:
        with args.dataset.open(encoding="utf-8") as f:
            cases = json.load(f)
    except Exception as exc:
        print(f"[ERROR] Failed to load dataset: {exc}", file=sys.stderr)
        sys.exit(1)

    results = run_project_evaluation(cases)
    if results["failed"] > 0:
        print("[FAIL] One or more project evaluation cases failed.", file=sys.stderr)
        sys.exit(1)

    print("[SUCCESS] All project evaluation cases passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
