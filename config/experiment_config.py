"""
Centralized experimental configuration for Intra-Node Load Balancing
in IoT Edge Computing Using Non-Cooperative Game Theory.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class NetworkConfig:
    """Configuration parameters for an edge network topology."""
    code: str
    name: str
    num_nodes: int
    num_servers: int
    cpu_capacity_range: Tuple[float, float] = (2.0, 8.0)          # Cores
    ram_capacity_range: Tuple[float, float] = (4.0, 16.0)         # GB
    storage_capacity_range: Tuple[float, float] = (64.0, 256.0)   # GB
    bandwidth_capacity_range: Tuple[float, float] = (50.0, 200.0) # Mbps
    max_cpu_utilization: float = 0.85                             # 85%
    max_ram_utilization: float = 0.90                             # 90%
    max_latency_ms: float = 50.0                                  # 50 ms


NETWORKS: Dict[str, NetworkConfig] = {
    "N1": NetworkConfig(
        code="N1",
        name="Network-1 (Small)",
        num_nodes=50,
        num_servers=5,
    ),
    "N2": NetworkConfig(
        code="N2",
        name="Network-2 (Intermediate)",
        num_nodes=150,
        num_servers=15,
    ),
    "N3": NetworkConfig(
        code="N3",
        name="Network-3 (Stress)",
        num_nodes=300,
        num_servers=30,
    ),
}

# Standard task workloads evaluated across Phase-1 and Phase-2
WORKLOAD_LEVELS: List[int] = [1250, 3000, 5000]

# Task arrival profiles
TASK_PROFILES: List[str] = ["T1", "T2", "T3"]

# Priority classes assigned per task based on calculated priority score
PRIORITY_CLASSES: List[str] = ["P1", "P2", "P3", "P4"]

# Illustrative baseline labels listed in the 27-experiment specification table
ILLUSTRATIVE_EXPERIMENT_LABELS: List[str] = [
    "P1", "P2", "P3", "P4", "P1", "P2", "P3", "P4", "P1",  # E1 - E9 (N1)
    "P2", "P3", "P4", "P1", "P2", "P3", "P4", "P1", "P2",  # E10 - E18 (N2)
    "P3", "P4", "P1", "P2", "P3", "P4", "P1", "P2", "P3",  # E19 - E27 (N3)
]

# Phase-2 ablation methods
ABLATION_METHODS: List[str] = [
    "A1: MFG only",
    "A2: Stackelberg only",
    "A3: MFG+Stackelberg",
    "Proposed",
]

# Default number of independent statistical replications per configuration in Phase-2
PHASE2_NUM_RUNS: int = 9
DEFAULT_RANDOM_SEED: int = 2026