"""
Task priority scoring and P1-P4 classification module.
Computes individual priority scores for each task and aggregates
observed P1, P2, P3, and P4 distributions across workloads.
"""

from typing import Dict, List
from src.edge_game.entities.task import Task


# Thresholds for mapping normalized priority scores in [0, 1] to priority classes
P1_THRESHOLD: float = 0.70
P2_THRESHOLD: float = 0.52
P3_THRESHOLD: float = 0.35


def calculate_priority_score(
    urgency_factor: float,
    criticality_factor: float,
    cpu_demand: float,
    ram_demand: float,
    bandwidth_demand: float,
) -> float:
    """
    Calculate a normalized multi-attribute priority score in [0, 1] for a single task.

    Weights:
      - Deadline urgency: 45%
      - Application criticality: 35%
      - Normalized resource intensity: 20%
    """
    norm_cpu = min(1.0, max(0.0, cpu_demand / 2.0))
    norm_ram = min(1.0, max(0.0, ram_demand / 2.5))
    norm_bw = min(1.0, max(0.0, bandwidth_demand / 30.0))
    resource_intensity = (norm_cpu + norm_ram + norm_bw) / 3.0

    score = (
        0.45 * min(1.0, max(0.0, urgency_factor))
        + 0.35 * min(1.0, max(0.0, criticality_factor))
        + 0.20 * resource_intensity
    )
    return float(min(1.0, max(0.0, score)))


def classify_priority(score: float) -> str:
    """Map a numerical priority score in [0, 1] to priority class P1, P2, P3, or P4."""
    if score >= P1_THRESHOLD:
        return "P1"
    if score >= P2_THRESHOLD:
        return "P2"
    if score >= P3_THRESHOLD:
        return "P3"
    return "P4"


def assign_task_priorities(tasks: List[Task]) -> Dict[str, int]:
    """
    Compute and assign priority_score and priority_class for every task in the list.
    Returns the observed count dictionary for classes P1, P2, P3, and P4.
    """
    counts: Dict[str, int] = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    for task in tasks:
        score = calculate_priority_score(
            urgency_factor=task.urgency_factor,
            criticality_factor=task.criticality_factor,
            cpu_demand=task.cpu_demand,
            ram_demand=task.ram_demand,
            bandwidth_demand=task.bandwidth_demand,
        )
        p_class = classify_priority(score)
        task.priority_score = score
        task.priority_class = p_class
        counts[p_class] += 1
    return counts


def format_priority_distribution(counts: Dict[str, int], total_tasks: int) -> str:
    """Format the observed P1-P4 task counts and percentages into a summary string."""
    if total_tasks <= 0:
        return "P1:0 (0.0%), P2:0 (0.0%), P3:0 (0.0%), P4:0 (0.0%)"
    parts = [
        f"{cls}:{counts.get(cls, 0)} ({(counts.get(cls, 0) / total_tasks) * 100.0:.1f}%)"
        for cls in ["P1", "P2", "P3", "P4"]
    ]
    return ", ".join(parts)