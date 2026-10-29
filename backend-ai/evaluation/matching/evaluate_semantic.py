"""
Dedicated evaluation runner for Semantic Text Representation & Similarity Infrastructure.

Evaluates deterministic cosine similarity computation, non-finite vector safety (NaN, Inf),
boundary handling (empty, zero norm, dimension mismatch), and score mapping without
requiring external LLMs or third-party embedding APIs.

NOTE: This evaluation validates engineering robustness, vector safety, and numerical bounds.
It is an infrastructure regression check, NOT a semantic model retrieval quality evaluation.

USAGE:
    python -m evaluation.matching.evaluate_semantic [--dataset PATH]
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from app.domain.matching.similarity import cosine_similarity, similarity_to_semantic_score

DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "semantic_cases.json"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Evaluate FutureCV Semantic Infrastructure Robustness")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to semantic cases JSON dataset",
    )
    return parser.parse_args()


def _parse_vector(raw: list[Any]) -> list[float]:
    """Parse JSON numbers and string representations of non-finite floats."""
    return [float(item) for item in raw]


def run_semantic_evaluation(raw_cases: list[dict[str, Any]]) -> dict[str, int]:
    """Execute semantic infrastructure evaluation and print formatted report."""
    print("=" * 88)
    print("FutureCV - Dedicated Semantic Infrastructure Regression Evaluation")
    print(f"Total test cases: {len(raw_cases)}")
    print("=" * 88)

    passed_count = 0
    failed_count = 0

    header = f"{'Case ID':<44} | {'Sim (Exp/Act)':<16} | {'Score (Exp/Act)':<16} | {'Result':<8}"
    print(header)
    print("-" * 88)

    for item in raw_cases:
        cid = item.get("id", "unknown")
        raw_a = item.get("vec_a", [])
        raw_b = item.get("vec_b", [])
        expected_sim = float(item.get("expected_sim", 0.0))
        expected_score = float(item.get("expected_score", 0.0))

        vec_a = _parse_vector(raw_a)
        vec_b = _parse_vector(raw_b)

        act_sim = cosine_similarity(vec_a, vec_b)
        act_score = similarity_to_semantic_score(act_sim)

        sim_ok = abs(act_sim - expected_sim) < 0.001
        score_ok = abs(act_score - expected_score) < 0.05
        passed = sim_ok and score_ok

        sim_str = f"{expected_sim:.2f} / {act_sim:.2f}"
        score_str = f"{expected_score:.1f} / {act_score:.1f}"
        status_str = "PASS" if passed else "FAIL"

        if passed:
            passed_count += 1
        else:
            failed_count += 1

        print(f"{cid:<44} | {sim_str:<16} | {score_str:<16} | {status_str:<8}")

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
        print(f"[ERROR] Semantic dataset not found at: {args.dataset}", file=sys.stderr)
        sys.exit(1)

    try:
        with args.dataset.open(encoding="utf-8") as f:
            raw_cases = json.load(f)
    except Exception as exc:
        print(f"[ERROR] Failed to load dataset {args.dataset}: {exc}", file=sys.stderr)
        sys.exit(1)

    results = run_semantic_evaluation(raw_cases)
    if results["failed"] > 0:
        print(f"[FAILURE] {results['failed']} semantic evaluation cases failed.", file=sys.stderr)
        sys.exit(1)
    else:
        print("[SUCCESS] All semantic evaluation cases passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
