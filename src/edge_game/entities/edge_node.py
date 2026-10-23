"""
EdgeNode entity representing an individual edge computing node with finite
multi-resource capacities and queuing state.
"""

from dataclasses import dataclass, field
from typing import List
from src.edge_game.entities.task import Task


@dataclass
class EdgeNode:
    """Represents an edge node participating in intra-node load balancing."""
    node_id: int
    server_id: int
    cpu_capacity: float        # Cores (2.0 - 8.0)
    ram_capacity: float        # GB (4.0 - 16.0)
    storage_capacity: float    # GB (64.0 - 256.0)
    bandwidth_capacity: float  # Mbps (50.0 - 200.0)
    base_latency_ms: float     # Base propagation/network latency in ms
    processing_speed_mips: float = 1200.0  # Processing rate per CPU core in MIPS

    # Current resource usage
    cpu_allocated: float = 0.0
    ram_allocated: float = 0.0
    storage_allocated: float = 0.0
    bandwidth_allocated: float = 0.0

    # Queue tracking for realistic task execution
    next_available_time_ms: float = 0.0
    assigned_tasks: List[Task] = field(default_factory=list)

    @property
    def available_cpu(self) -> float:
        """Return currently unallocated CPU cores."""
        return max(0.0, self.cpu_capacity - self.cpu_allocated)

    @property
    def available_ram(self) -> float:
        """Return currently unallocated RAM in GB."""
        return max(0.0, self.ram_capacity - self.ram_allocated)

    @property
    def available_storage(self) -> float:
        """Return currently unallocated storage in GB."""
        return max(0.0, self.storage_capacity - self.storage_allocated)

    @property
    def available_bandwidth(self) -> float:
        """Return currently unallocated bandwidth in Mbps."""
        return max(0.0, self.bandwidth_capacity - self.bandwidth_allocated)

    @property
    def cpu_utilization(self) -> float:
        """Return current CPU utilization ratio in [0, 1]."""
        if self.cpu_capacity <= 0.0:
            return 1.0
        return self.cpu_allocated / self.cpu_capacity

    @property
    def ram_utilization(self) -> float:
        """Return current RAM utilization ratio in [0, 1]."""
        if self.ram_capacity <= 0.0:
            return 1.0
        return self.ram_allocated / self.ram_capacity

    def projected_cpu_utilization(self, additional_cpu: float) -> float:
        """Return projected CPU utilization if additional_cpu is allocated."""
        if self.cpu_capacity <= 0.0:
            return 1.0
        return (self.cpu_allocated + additional_cpu) / self.cpu_capacity

    def projected_ram_utilization(self, additional_ram: float) -> float:
        """Return projected RAM utilization if additional_ram is allocated."""
        if self.ram_capacity <= 0.0:
            return 1.0
        return (self.ram_allocated + additional_ram) / self.ram_capacity

    def estimate_latency_ms(self, task: Task) -> float:
        """Estimate transmission plus queuing delay for a candidate task in ms."""
        transmission_delay_ms = (task.bandwidth_demand / max(self.available_bandwidth, 1.0)) * 6.0
        congestion_delay_ms = 12.0 * (self.cpu_utilization ** 2)
        return self.base_latency_ms + transmission_delay_ms + congestion_delay_ms

    def allocate_task(self, task: Task) -> None:
        """Commit resources for a task and update its execution timestamps."""
        self.cpu_allocated = min(self.cpu_capacity, self.cpu_allocated + task.cpu_demand)
        self.ram_allocated = min(self.ram_capacity, self.ram_allocated + task.ram_demand)
        self.storage_allocated = min(self.storage_capacity, self.storage_allocated + task.storage_demand)
        self.bandwidth_allocated = min(
            self.bandwidth_capacity, self.bandwidth_allocated + task.bandwidth_demand
        )

        # Compute realistic service and transmission time
        effective_mips = max(100.0, self.processing_speed_mips * max(task.cpu_demand, 0.25))
        service_time_ms = (task.instruction_length / effective_mips) * 100.0
        network_time_ms = self.estimate_latency_ms(task)

        start_ms = max(task.arrival_time_ms, self.next_available_time_ms)
        completion_ms = start_ms + service_time_ms + network_time_ms

        task.assigned_node_id = self.node_id
        task.assigned_server_id = self.server_id
        task.start_time_ms = start_ms
        task.completion_time_ms = completion_ms
        task.completed = True

        # Advance node queue availability proportionally to core share
        self.next_available_time_ms = start_ms + (service_time_ms / max(self.cpu_capacity, 1.0))
        self.assigned_tasks.append(task)