from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    task_id: int
    arrival_tick: int
    cpu_required_gcps: float
    memory_required_gb: float
    bandwidth_required_mbps: float
    latency_limit_ms: float
    energy_limit_j: float
    queue_limit: int
    urgency: float
    latency_sensitivity: float
    service_importance: float
    priority_score: float
    priority_class: int
    priority_label: str
    priority_profile: str
