"""
Workload and network topology generator for IoT Edge Computing experiments.
Generates edge nodes, edge servers, and heterogeneous task workloads across
profiles T1, T2, and T3.
"""

from typing import Dict, List, Tuple
import numpy as np

from config.experiment_config import NetworkConfig
from src.edge_game.entities.edge_node import EdgeNode
from src.edge_game.entities.edge_server import EdgeServer
from src.edge_game.entities.task import Task
from src.edge_game.workload.priority import assign_task_priorities


# Profile-specific statistical parameters for task profiles T1, T2, and T3
PROFILE_PARAMETERS: Dict[str, Dict[str, Tuple[float, float] | float]] = {
    "T1": {
        # Latency-sensitive / Urgent IoT telemetry profile
        "urgency_beta": (3.2, 2.0),
        "criticality_beta": (3.0, 2.2),
        "cpu_scale": 0.85,
        "ram_scale": 0.85,
        "mi_range": (150.0, 450.0),
    },
    "T2": {
        # Balanced mixed IoT workload profile
        "urgency_beta": (2.3, 2.3),
        "criticality_beta": (2.5, 2.5),
        "cpu_scale": 1.00,
        "ram_scale": 1.00,
        "mi_range": (250.0, 650.0),
    },
    "T3": {
        # Compute-intensive / Bandwidth-heavy analytical profile
        "urgency_beta": (1.8, 3.0),
        "criticality_beta": (2.0, 2.8),
        "cpu_scale": 1.20,
        "ram_scale": 1.15,
        "mi_range": (400.0, 950.0),
    },
}


def generate_network_topology(
    net_config: NetworkConfig,
    rng: np.random.Generator,
    initial_load_factor: float = 0.35,
) -> Tuple[List[EdgeNode], List[EdgeServer]]:
    """
    Instantiate edge servers and edge nodes according to Table 1 resource parameters.
    Assigns nodes evenly across servers and initializes background resource usage.
    """
    servers: List[EdgeServer] = [
        EdgeServer(server_id=s_id, node_ids=[], unit_price=1.20)
        for s_id in range(net_config.num_servers)
    ]

    nodes: List[EdgeNode] = []
    for n_id in range(net_config.num_nodes):
        s_id = n_id % net_config.num_servers
        cpu_cap = float(rng.uniform(*net_config.cpu_capacity_range))
        ram_cap = float(rng.uniform(*net_config.ram_capacity_range))
        storage_cap = float(rng.uniform(*net_config.storage_capacity_range))
        bw_cap = float(rng.uniform(*net_config.bandwidth_capacity_range))
        base_lat = float(rng.uniform(8.0, 46.0))
        mips_rate = float(rng.uniform(1000.0, 1600.0))

        # Background baseline occupancy before new task batch arrives
        bg_scale = float(rng.uniform(0.15, max(0.20, initial_load_factor)))
        node = EdgeNode(
            node_id=n_id,
            server_id=s_id,
            cpu_capacity=cpu_cap,
            ram_capacity=ram_cap,
            storage_capacity=storage_cap,
            bandwidth_capacity=bw_cap,
            base_latency_ms=base_lat,
            processing_speed_mips=mips_rate,
            cpu_allocated=cpu_cap * bg_scale,
            ram_allocated=ram_cap * bg_scale,
            storage_allocated=storage_cap * (bg_scale * 0.8),
            bandwidth_allocated=bw_cap * (bg_scale * 0.7),
        )
        nodes.append(node)
        servers[s_id].node_ids.append(n_id)

    return nodes, servers


def generate_workload(
    num_tasks: int,
    profile: str,
    rng: np.random.Generator,
) -> Tuple[List[Task], Dict[str, int]]:
    """
    Generate a workload of `num_tasks` tasks under profile T1, T2, or T3,
    and classify each task into priority classes P1, P2, P3, or P4.
    """
    if profile not in PROFILE_PARAMETERS:
        raise ValueError(f"Unsupported task profile '{profile}'. Expected one of {list(PROFILE_PARAMETERS)}.")

    params = PROFILE_PARAMETERS[profile]
    urg_a, urg_b = params["urgency_beta"]          # type: ignore[misc]
    crit_a, crit_b = params["criticality_beta"]    # type: ignore[misc]
    cpu_scale = float(params["cpu_scale"])         # type: ignore[arg-type]
    ram_scale = float(params["ram_scale"])         # type: ignore[arg-type]
    mi_low, mi_high = params["mi_range"]           # type: ignore[misc]

    tasks: List[Task] = []
    current_arrival_ms = 0.0

    for t_id in range(num_tasks):
        # Poisson-like inter-arrival progression in ms
        current_arrival_ms += float(rng.exponential(scale=0.35))

        cpu_d = float(rng.uniform(0.20, 1.40) * cpu_scale)
        ram_d = float(rng.uniform(0.25, 1.80) * ram_scale)
        storage_d = float(rng.uniform(0.50, 6.00))
        bw_d = float(rng.uniform(2.00, 22.00))
        instr_mi = float(rng.uniform(mi_low, mi_high))

        urgency = float(rng.beta(urg_a, urg_b))
        criticality = float(rng.beta(crit_a, crit_b))
        deadline = float(rng.uniform(30.0, 50.0))

        tasks.append(
            Task(
                task_id=t_id,
                cpu_demand=cpu_d,
                ram_demand=ram_d,
                storage_demand=storage_d,
                bandwidth_demand=bw_d,
                instruction_length=instr_mi,
                deadline_ms=deadline,
                urgency_factor=urgency,
                criticality_factor=criticality,
                arrival_time_ms=current_arrival_ms,
            )
        )

    priority_counts = assign_task_priorities(tasks)
    return tasks, priority_counts