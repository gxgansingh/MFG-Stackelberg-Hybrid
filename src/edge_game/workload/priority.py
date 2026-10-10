from dataclasses import dataclass


@dataclass(frozen=True)
class PriorityAssignment:
    score: float
    priority_class: int
    label: str


def calculate_priority_score(
    urgency: float,
    latency_sensitivity: float,
    service_importance: float,
    weights: tuple[float, float, float],
) -> float:
    score = (
        weights[0] * urgency
        + weights[1] * latency_sensitivity
        + weights[2] * service_importance
    )
    return max(0.0, min(1.0, score))


def classify_priority(score: float) -> tuple[int, str]:
    if score >= 0.75:
        return 4, "P1 Critical"
    if score >= 0.55:
        return 3, "P2 High"
    if score >= 0.30:
        return 2, "P3 Medium"
    return 1, "P4 Low"


def assign_priority(urgency, latency_sensitivity, service_importance, weights):
    score = calculate_priority_score(
        urgency, latency_sensitivity, service_importance, weights
    )
    priority_class, label = classify_priority(score)
    return PriorityAssignment(score, priority_class, label)
