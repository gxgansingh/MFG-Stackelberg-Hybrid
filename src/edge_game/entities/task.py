"""
Task entity definition with multi-resource demands, priority classification,
and execution lifecycle tracking.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    """Represents an individual IoT computational task submitted to the edge network."""
    task_id: int
    cpu_demand: float          # Required CPU cores
    ram_demand: float          # Required RAM in GB
    storage_demand: float      # Required storage in GB
    bandwidth_demand: float    # Required bandwidth in Mbps
    instruction_length: float  # Computational size in Million Instructions (MI)
    deadline_ms: float         # Maximum tolerable latency in ms
    urgency_factor: float      # Normalized urgency in [0, 1]
    criticality_factor: float  # Normalized criticality in [0, 1]
    priority_score: float = 0.0
    priority_class: str = "P4"

    # Execution and scheduling state
    assigned_node_id: Optional[int] = None
    assigned_server_id: Optional[int] = None
    arrival_time_ms: float = 0.0
    start_time_ms: Optional[float] = None
    completion_time_ms: Optional[float] = None
    completed: bool = False

    @property
    def response_time_ms(self) -> Optional[float]:
        """Return total turnaround time (waiting + service + transmission) in ms."""
        if self.completion_time_ms is None:
            return None
        return max(0.0, self.completion_time_ms - self.arrival_time_ms)

    @property
    def priority_weight(self) -> float:
        """Return numerical scheduling weight associated with the task priority class."""
        weights = {
            "P1": 1.60,
            "P2": 1.25,
            "P3": 1.00,
            "P4": 0.75,
        }
        return weights.get(self.priority_class, 1.00)