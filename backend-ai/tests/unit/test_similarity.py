"""Unit tests for pure domain vector cosine similarity and semantic score mapping."""

import math

from app.domain.matching.similarity import cosine_similarity, similarity_to_semantic_score


def test_cosine_similarity_identical_vectors():
    """Verify identical non-zero vectors yield cosine similarity 1.0."""
    vec = [0.6, 0.8]
    assert math.isclose(cosine_similarity(vec, vec), 1.0, rel_tol=1e-5)


def test_cosine_similarity_orthogonal_vectors():
    """Verify perpendicular vectors yield cosine similarity 0.0."""
    vec_a = [1.0, 0.0]
    vec_b = [0.0, 1.0]
    assert math.isclose(cosine_similarity(vec_a, vec_b), 0.0, abs_tol=1e-5)


def test_cosine_similarity_opposite_vectors():
    """Verify opposite vectors yield cosine similarity -1.0."""
    vec_a = [1.0, 0.0]
    vec_b = [-1.0, 0.0]
    assert math.isclose(cosine_similarity(vec_a, vec_b), -1.0, rel_tol=1e-5)


def test_cosine_similarity_empty_vectors_safe():
    """Rule: Empty vector input returns 0.0 safely without exception."""
    assert cosine_similarity([], [1.0, 2.0]) == 0.0
    assert cosine_similarity([1.0, 2.0], []) == 0.0
    assert cosine_similarity([], []) == 0.0


def test_cosine_similarity_dimension_mismatch_safe():
    """Rule: Dimension mismatch returns 0.0 safely without exception."""
    assert cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0


def test_cosine_similarity_zero_magnitude_vector_safe():
    """Rule: Zero magnitude vector returns 0.0 without raising ZeroDivisionError."""
    assert cosine_similarity([0.0, 0.0, 0.0], [1.0, 2.0, 3.0]) == 0.0
    assert cosine_similarity([1.0, 2.0, 3.0], [0.0, 0.0, 0.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_similarity_to_semantic_score_mapping():
    """Verify experimental transform mapping: non-positive clamped to 0, positive scaled 0-100."""
    assert similarity_to_semantic_score(1.0) == 100.0
    assert similarity_to_semantic_score(0.75) == 75.0
    assert similarity_to_semantic_score(0.50) == 50.0
    assert similarity_to_semantic_score(0.0) == 0.0
    # Negative cosine similarity clamped to 0.0
    assert similarity_to_semantic_score(-0.25) == 0.0
    assert similarity_to_semantic_score(-1.0) == 0.0
    # Overflows clamped to 100.0
    assert similarity_to_semantic_score(1.05) == 100.0


def test_cosine_similarity_nan_safe():
    """Rule: Vector containing NaN returns 0.0 safely without raising or fabricating positive similarity."""
    assert cosine_similarity([float("nan"), 1.0], [1.0, 1.0]) == 0.0
    assert cosine_similarity([1.0, 1.0], [float("nan"), 1.0]) == 0.0
    assert cosine_similarity([float("nan")], [float("nan")]) == 0.0


def test_cosine_similarity_inf_safe():
    """Rule: Vector containing +Infinity returns 0.0 safely without raising or fabricating positive similarity."""
    assert cosine_similarity([float("inf"), 1.0], [1.0, 1.0]) == 0.0
    assert cosine_similarity([1.0, 1.0], [float("inf"), 1.0]) == 0.0
    assert cosine_similarity([float("inf")], [float("inf")]) == 0.0


def test_cosine_similarity_negative_inf_safe():
    """Rule: Vector containing -Infinity returns 0.0 safely without raising or fabricating positive similarity."""
    assert cosine_similarity([float("-inf"), 1.0], [1.0, 1.0]) == 0.0
    assert cosine_similarity([1.0, 1.0], [float("-inf"), 1.0]) == 0.0
    assert cosine_similarity([float("-inf")], [float("-inf")]) == 0.0


def test_cosine_similarity_both_non_finite_safe():
    """Rule: Mixed non-finite vectors return 0.0 safely."""
    assert cosine_similarity([float("nan"), float("inf")], [float("inf"), float("nan")]) == 0.0


def test_cosine_similarity_non_numeric_elements_safe():
    """Rule: Non-numeric vectors (str, None, bool, list) return 0.0 safely without raising TypeError."""
    assert cosine_similarity([1.0, "bad", 0.5], [1.0, 1.0, 1.0]) == 0.0  # type: ignore[list-item]
    assert cosine_similarity([1.0, 1.0, 1.0], [1.0, None, 0.5]) == 0.0  # type: ignore[list-item]
    assert cosine_similarity([1.0, True, 0.5], [1.0, 1.0, 1.0]) == 0.0  # type: ignore[list-item]
    assert cosine_similarity([1.0, [0.5], 0.5], [1.0, 1.0, 1.0]) == 0.0  # type: ignore[list-item]


def test_similarity_to_semantic_score_non_finite_safe():
    """Rule: Non-finite similarity values (NaN, +Inf, -Inf) map to 0.0."""
    assert similarity_to_semantic_score(float("nan")) == 0.0
    assert similarity_to_semantic_score(float("inf")) == 0.0
    assert similarity_to_semantic_score(float("-inf")) == 0.0


def test_similarity_to_semantic_score_non_numeric_safe():
    """Rule: Non-numeric similarity inputs safely map to 0.0 without exception."""
    assert similarity_to_semantic_score("bad") == 0.0  # type: ignore[arg-type]
    assert similarity_to_semantic_score(None) == 0.0  # type: ignore[arg-type]
    assert similarity_to_semantic_score(True) == 0.0  # type: ignore[arg-type]
