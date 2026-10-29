"""Pure domain vector similarity functions and experimental semantic scoring transforms."""

from collections.abc import Sequence
import math


def cosine_similarity(
    vec_a: Sequence[float],
    vec_b: Sequence[float],
) -> float:
    """
    Compute cosine similarity between two numeric vectors in pure Python.

    Edge cases handled safely without raising ZeroDivisionError:
    - Empty vectors -> 0.0
    - Dimension mismatch -> 0.0
    - Zero magnitude vectors -> 0.0
    - Non-finite vectors (containing NaN, +Inf, -Inf) -> 0.0
    - Non-numeric vectors (containing str, None, bool, etc.) -> 0.0
    """
    if not vec_a or not vec_b:
        return 0.0

    if len(vec_a) != len(vec_b):
        return 0.0

    # Guard against non-numeric and non-finite elements (str, None, bool, NaN, Inf)
    for x in vec_a:
        if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x):
            return 0.0
    for x in vec_b:
        if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x):
            return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    raw_sim = dot_product / (norm_a * norm_b)
    if not math.isfinite(raw_sim):
        return 0.0

    # Clamp to guard against floating-point inaccuracies outside [-1.0, 1.0]
    return float(max(-1.0, min(1.0, raw_sim)))


def similarity_to_semantic_score(similarity: float) -> float:
    """
    Transform cosine similarity into an uncalibrated semantic score in range [0.0, 100.0].

    EXPERIMENTAL TRANSFORM NOTE:
    Non-positive cosine similarities are clamped to zero and positive cosine similarity
    is scaled to 0-100:
        semantic_score = clamp(similarity, 0.0, 1.0) * 100.0


    This is an uncalibrated experimental heuristic and does not represent a full
    affine transform from [-1.0, 1.0] to [0.0, 100.0]. It requires empirical calibration
    against human relevance judgments.
    """
    if not isinstance(similarity, (int, float)) or isinstance(similarity, bool) or not math.isfinite(similarity):
        return 0.0

    clamped_sim = max(0.0, min(1.0, similarity))
    return round(clamped_sim * 100.0, 2)
