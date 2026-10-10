from dataclasses import dataclass


@dataclass(frozen=True)
class FeasibilityResult:
    feasible: bool
    cpu_ok: bool
    memory_ok: bool
    bandwidth_ok: bool
    latency_ok: bool
    energy_ok: bool
    queue_ok: bool

    @property
    def failed_constraints(self) -> list[str]:
        checks = {
            "cpu": self.cpu_ok,
            "memory": self.memory_ok,
            "bandwidth": self.bandwidth_ok,
            "latency": self.latency_ok,
            "energy": self.energy_ok,
            "queue": self.queue_ok,
        }
        return [name for name, passed in checks.items() if not passed]


class ResourceFilter:
    def evaluate(self, task, node) -> FeasibilityResult:
        cpu_ok = node.cpu_capacity_gcps - node.cpu_used_gcps >= task.cpu_required_gcps
        memory_ok = node.memory_capacity_gb - node.memory_used_gb >= task.memory_required_gb
        bandwidth_ok = node.bandwidth_capacity_mbps - node.bandwidth_used_mbps >= task.bandwidth_required_mbps
        latency_ok = node.latency_ms <= task.latency_limit_ms
        energy_ok = node.energy_per_task_j <= task.energy_limit_j
        queue_ok = node.queue_length < min(node.queue_capacity, task.queue_limit)
        return FeasibilityResult(
            feasible=all((cpu_ok, memory_ok, bandwidth_ok, latency_ok, energy_ok, queue_ok)),
            cpu_ok=cpu_ok,
            memory_ok=memory_ok,
            bandwidth_ok=bandwidth_ok,
            latency_ok=latency_ok,
            energy_ok=energy_ok,
            queue_ok=queue_ok,
        )

    def is_feasible(self, task, node) -> bool:
        return self.evaluate(task, node).feasible
