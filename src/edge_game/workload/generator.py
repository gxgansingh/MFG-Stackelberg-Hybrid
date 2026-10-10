import numpy as np

from config.experiment_config import PRIORITY_PROFILES
from ..entities.task import Task
from .priority import assign_priority


def generate_tasks(count: int, profile_id: str, seed: int, ticks: int) -> list[Task]:
    rng = np.random.default_rng(seed)
    profile = next(p for p in PRIORITY_PROFILES if p.profile_id == profile_id)
    tasks = []

    for task_id in range(count):
        urgency = float(rng.beta(3.0, 2.0))
        latency_sensitivity = float(rng.beta(2.8, 2.0))
        service_importance = float(rng.beta(3.0, 2.4))
        priority = assign_priority(
            urgency, latency_sensitivity, service_importance, profile.weights
        )
        tasks.append(
            Task(
                task_id=task_id,
                arrival_tick=task_id % ticks,
                cpu_required_gcps=float(rng.uniform(0.8, 4.0)),
                memory_required_gb=float(rng.uniform(0.25, 2.0)),
                bandwidth_required_mbps=float(rng.uniform(5.0, 35.0)),
                latency_limit_ms=float(rng.uniform(20.0, 65.0)),
                energy_limit_j=float(rng.uniform(35.0, 85.0)),
                queue_limit=int(rng.integers(3, 15)),
                urgency=urgency,
                latency_sensitivity=latency_sensitivity,
                service_importance=service_importance,
                priority_score=priority.score,
                priority_class=priority.priority_class,
                priority_label=priority.label,
                priority_profile=profile_id,
            )
        )
    return tasks
