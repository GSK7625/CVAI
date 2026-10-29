"""
Command-line evaluation runner for Candidate Job Matching (v0 vs v1).

USAGE:
    python -m evaluation.matching.evaluate [--provider mock|openai] [--dataset PATH]

DISCLAIMER:
    When executed with --provider mock (default), embeddings are generated via
    deterministic SHA-256 token hashing. Mock results serve strictly for regression
    testing and behavioral verification. They must NOT be used as evidence of
    improved semantic retrieval quality over matching-v0.
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Any

from app.application.matching_service import MatchingService
from app.application.semantic_representation import build_cv_semantic_text
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob
from app.core.config import Settings
from app.infrastructure.embeddings.providers.mock_provider import MockEmbeddingProvider
from app.infrastructure.embeddings.providers.openai_provider import OpenAiEmbeddingProvider
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.ports.embeddings import EmbeddingPort
from evaluation.matching.metrics import (
    compute_pairwise_accuracy,
    compute_range_compliance,
    compute_semantic_discrimination_delta,
    compute_statistics,
)

DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "matching_sanity_cases.json"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate FutureCV Candidate Job Matching (matching-v0 vs matching-v1-experimental)"
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "openai"],
        default="mock",
        help="Embedding provider to use for matching-v1 (default: mock)",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to evaluation cases JSON dataset",
    )
    return parser.parse_args()


async def run_evaluation(provider_name: str, dataset_name: str, raw_cases: list[dict[str, Any]]) -> int:
    """Execute evaluation and print formatted comparison report."""
    print("=" * 80)
    print("FutureCV - Candidate Job Matching Evaluation")
    print(f"Dataset: {dataset_name} ({len(raw_cases)} test cases)")
    print(f"Embedding Provider under test: {provider_name.upper()}")

    if provider_name == "mock":
        print("[NOTE] Running in OFFLINE MOCK MODE. Results represent deterministic regression checks.")
    print("=" * 80)

    # Initialize providers
    mock_llm = MockLlmProvider()

    embedding_provider: EmbeddingPort
    if provider_name == "mock":
        embedding_provider = MockEmbeddingProvider(dimension=64)
    else:
        settings = Settings(ENV="development", EMBEDDING_PROVIDER="openai")
        embedding_provider = OpenAiEmbeddingProvider(settings=settings)

    v0_service = MatchingService(
        llm=mock_llm,
        embedding_provider=None,
        matching_algorithm="matching-v0",
    )
    v1_service = MatchingService(
        llm=mock_llm,
        embedding_provider=embedding_provider,
        matching_algorithm="matching-v1-experimental",
    )

    results: list[dict[str, Any]] = []
    v0_scores_by_id: dict[str, int] = {}
    v1_scores_by_id: dict[str, int] = {}
    pii_leak_count = 0

    print(f"{'ID':<38} | {'Category':<22} | {'v0':<5} | {'v1':<5} | {'Diff':<6}")
    print("-" * 80)

    for item in raw_cases:
        case_id = item["id"]
        category = item["category"]
        cv = StructuredCv.model_validate(item["cv"])
        job = StructuredJob.model_validate(item["job"])

        # PII Protection verification
        semantic_cv = build_cv_semantic_text(cv)
        if cv.email and cv.email in semantic_cv:
            pii_leak_count += 1
        if cv.phone and cv.phone in semantic_cv:
            pii_leak_count += 1
        if cv.full_name and cv.full_name in semantic_cv:
            pii_leak_count += 1

        # Run v0 (generate_explanation=False for fast evaluation)
        v0_res = await v0_service.match(cv=cv, job=job, generate_explanation=False)
        # Run v1
        v1_res = await v1_service.match(cv=cv, job=job, generate_explanation=False)

        v0_score = v0_res.match_score
        v1_score = v1_res.match_score
        diff = v1_score - v0_score
        diff_str = f"+{diff}" if diff > 0 else str(diff)

        v0_scores_by_id[case_id] = v0_score
        v1_scores_by_id[case_id] = v1_score

        results.append(
            {
                "id": case_id,
                "category": category,
                "v0_score": v0_score,
                "v1_score": v1_score,
                "expected_v0_range": item.get("expected_v0_score_range", [0, 100]),
                "expected_v1_range": item.get("expected_v1_score_range", [0, 100]),
            }
        )

        print(f"{case_id:<38} | {category:<22} | {v0_score:<5} | {v1_score:<5} | {diff_str:<6}")

    print("-" * 80)

    # Compute comparative metrics
    v0_scores = list(v0_scores_by_id.values())
    v1_scores = list(v1_scores_by_id.values())

    v0_stats = compute_statistics(v0_scores)
    v1_stats = compute_statistics(v1_scores)

    v0_compliance = compute_range_compliance(results, "v0_score", "expected_v0_range")
    v1_compliance = compute_range_compliance(results, "v1_score", "expected_v1_range")

    v0_pairwise = compute_pairwise_accuracy(v0_scores_by_id)
    v1_pairwise = compute_pairwise_accuracy(v1_scores_by_id)

    v0_delta = compute_semantic_discrimination_delta(results, "v0_score")
    v1_delta = compute_semantic_discrimination_delta(results, "v1_score")

    print("\n" + "=" * 80)
    print("COMPARATIVE METRICS SUMMARY")
    print("=" * 80)
    print(f"{'Metric':<35} | {'matching-v0':<18} | {'matching-v1-experimental':<22}")
    print("-" * 80)
    print(f"{'Algorithm Role':<35} | {'Heuristic Baseline':<18} | {'Experimental Hypothesis':<22}")
    print(f"{'Embedding Provider':<35} | {'None (0 calls)':<18} | {embedding_provider.provider_name:<22}")
    print(f"{'Embedding Model':<35} | {'None':<18} | {embedding_provider.model_name:<22}")
    mean_v0 = f"{v0_stats.mean:.1f} +/- {v0_stats.std_dev:.1f}"
    mean_v1 = f"{v1_stats.mean:.1f} +/- {v1_stats.std_dev:.1f}"

    print(f"{'Score Mean +/- StdDev':<35} | {mean_v0:<18} | {mean_v1:<22}")

    range_v0 = f"[{v0_stats.min_score}, {v0_stats.max_score}]"
    range_v1 = f"[{v1_stats.min_score}, {v1_stats.max_score}]"
    print(f"{'Score Range [Min, Max]':<35} | {range_v0:<18} | {range_v1:<22}")
    print(f"{'Expected Range Compliance':<35} | {v0_compliance:.1f}%              | {v1_compliance:.1f}%")
    print(f"{'Pairwise Ranking Accuracy':<35} | {v0_pairwise:.1f}%              | {v1_pairwise:.1f}%")
    print(f"{'High-Fit vs Mismatch Delta':<35} | +{v0_delta:.1f} pts            | +{v1_delta:.1f} pts")
    print(f"{'PII Leakage Detected':<35} | {'0 instances':<18} | {f'{pii_leak_count} instances':<22}")

    print("=" * 80)

    await embedding_provider.aclose()
    return 0


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    if not args.dataset.exists():
        print(f"Error: Dataset not found at {args.dataset}", file=sys.stderr)
        sys.exit(1)

    with args.dataset.open(encoding="utf-8") as f:
        raw_cases: list[dict[str, Any]] = json.load(f)

    exit_code = asyncio.run(run_evaluation(args.provider, args.dataset.name, raw_cases))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
