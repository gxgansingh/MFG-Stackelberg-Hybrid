from dataclasses import dataclass


@dataclass
class EdgeNode:
    node_id: str
    server_id: str
    cpu_capacity_gcps: float
    memory_capacity_gb: float
    bandwidth_capacity_mbps: float
    latency_ms: float
    energy_per_task_j: float
    queue_capacity: int
    cpu_used_gcps: float = 0.0
    memory_used_gb: float = 0.0
    bandwidth_used_mbps: float = 0.0
    queue_length: int = 0

    @property
    def cpu_load(self) -> float:
        return self.cpu_used_gcps / self.cpu_capacity_gcps

    @property
    def memory_load(self) -> float:
        return self.memory_used_gb / self.memory_capacity_gb

    @property
    def bandwidth_load(self) -> float:
        return self.bandwidth_used_mbps / self.bandwidth_capacity_mbps

    @property
    def queue_pressure(self) -> float:
        return self.queue_length / self.queue_capacity

    @property
    def energy_pressure(self) -> float:
        return min(self.energy_per_task_j / 100.0, 1.0)

    def utilization_state(self) -> float:
        return (
            0.30 * self.cpu_load
            + 0.20 * self.memory_load
            + 0.15 * self.bandwidth_load
            + 0.20 * self.queue_pressure
            + 0.15 * self.energy_pressure
        )

    def reserve(self, task) -> None:
        self.cpu_used_gcps += task.cpu_required_gcps
        self.memory_used_gb += task.memory_required_gb
        self.bandwidth_used_mbps += task.bandwidth_required_mbps
        self.queue_length += 1

    def release_fraction(self, fraction: float) -> None:
        self.cpu_used_gcps *= fraction
        self.memory_used_gb *= fraction
        self.bandwidth_used_mbps *= fraction
        self.queue_length = int(round(self.queue_length * fraction))
