"""
Unit tests for task priority score calculation and P1-P4 classification.
"""

from src.edge_game.workload.priority import (
    calculate_priority_score,
    classify_priority,
    format_priority_distribution,
)


def test_priority_score_monotonicity_and_bounds() -> None:
    """Verify higher urgency and criticality yield a higher priority score in [0, 1]."""
    high_score = calculate_priority_score(
        urgency_factor=0.95,
        criticality_factor=0.90,
        cpu_demand=1.5,
        ram_demand=2.0,
        bandwidth_demand=20.0,
    )
    low_score = calculate_priority_score(
        urgency_factor=0.10,
        criticality_factor=0.15,
        cpu_demand=0.2,
        ram_demand=0.3,
        bandwidth_demand=2.0,
    )
    assert 0.0 <= low_score < high_score <= 1.0
    assert classify_priority(high_score) == "P1"
    assert classify_priority(low_score) == "P4"


def test_format_priority_distribution_output() -> None:
    """Verify priority distribution string formatting."""
    counts = {"P1": 250, "P2": 500, "P3": 300, "P4": 200}
    formatted = format_priority_distribution(counts, total_tasks=1250)
    assert "P1:250 (20.0%)" in formatted
    assert "P2:500 (40.0%)" in formatted
    assert "P3:300 (24.0%)" in formatted
    assert "P4:200 (16.0%)" in formatted