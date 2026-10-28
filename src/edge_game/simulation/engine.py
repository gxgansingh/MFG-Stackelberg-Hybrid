"""
End-to-end simulation engine for executing single and replicated IoT edge
load-balancing experiments across networks, workloads, profiles, and ablation methods.
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np

from config.experiment_config import NETWORKS, NetworkConfig
from src.edge_game.filtering.resource_filter import ResourceFilter
from src.edge_game.games.hierarchical_game import HierarchicalGameEngine
from src.edge_game.simulation.metrics import SimulationMetrics, compute_system_metrics
from src.edge_game.workload.generator import generate_network_topology, generate_workload
from src.edge_game.workload.priority import format_priority_distribution


@dataclass
class ExperimentTrialResult:
    """Complete record of a single simulation trial."""
    network_code: str
    num_nodes: int
    num_servers: int
    workload_size: int
    task_profile: str
    method: str
    seed: int
    priority_counts: Dict[str, int]
    priority_distribution_str: str
    mean_feasible_nodes: float
    metrics: SimulationMetrics

    def to_flat_record(self, run_id: int = 1) -> Dict[str, float | int | str]:
        """Return a flat dictionary suitable for pandas DataFrame construction."""
        record: Dict[str, float | int | str] = {
            "network": self.network_code,
            "num_nodes": self.num_nodes,
            "num_servers": self.num_servers,
            "workload": self.workload_size,
            "profile": self.task_profile,
            "method": self.method,
            "run_id": run_id,
            "seed": self.seed,
            "P1_count": self.priority_counts.get("P1", 0),
            "P2_count": self.priority_counts.get("P2", 0),
            "P3_count": self.priority_counts.get("P3", 0),
            "P4_count": self.priority_counts.get("P4", 0),
            "priority_distribution": self.priority_distribution_str,
            "mean_feasible_nodes": self.mean_feasible_nodes,
        }
        record.update(self.metrics.to_dict())
        return record


class SimulationEngine:
    """Executes complete simulation trials for Phase-1 and Phase-2 experiments."""

    def __init__(self, net_config: NetworkConfig) -> None:
        self.net_config = net_config
        self.resource_filter = ResourceFilter(net_config)

    def run_trial(
        self,
        workload_size: int,
        task_profile: str,
        method: str = "Proposed",
        seed: int = 2026,
    ) -> ExperimentTrialResult:
        """
        Run a single reproducible simulation trial for the specified workload,
        task profile (T1, T2, or T3), and ablation method (A1, A2, A3, or Proposed).
        """
        rng = np.random.default_rng(seed)

        # 1. Generate edge network topology and initial background state
        nodes, servers = generate_network_topology(
            net_config=self.net_config,
            rng=rng,
            initial_load_factor=0.35,
        )

        # 2. Generate task workload and classify each task into P1, P2, P3, or P4
        tasks, priority_counts = generate_workload(
            num_tasks=workload_size,
            profile=task_profile,
            rng=rng,
        )
        dist_str = format_priority_distribution(priority_counts, workload_size)

        # 3. Audit pre-allocation dynamic feasible node count under the 7 filtering criteria
        audit_stats = self.resource_filter.audit_batch_filtering(
            nodes=nodes,
            tasks=tasks,
            max_sample_tasks=100,
        )
        mean_feasible_nodes = float(audit_stats["mean_feasible_nodes"])

        # 4. Execute game-theoretic coordination and task execution
        game_engine = HierarchicalGameEngine(
            method=method,
            resource_filter=self.resource_filter,
        )
        outcome = game_engine.execute_coordination(
            nodes=nodes,
            servers=servers,
            tasks=tasks,
            rng=rng,
        )

        # 5. Compute system performance and equilibrium gap metrics
        sim_metrics = compute_system_metrics(
            nodes=nodes,
            servers=servers,
            tasks=tasks,
            server_prices=outcome.server_prices,
            convergence_time_ms=outcome.convergence_time_ms,
            nash_gap=outcome.nash_gap,
            stackelberg_gap=outcome.stackelberg_gap,
        )

        return ExperimentTrialResult(
            network_code=self.net_config.code,
            num_nodes=self.net_config.num_nodes,
            num_servers=self.net_config.num_servers,
            workload_size=workload_size,
            task_profile=task_profile,
            method=method,
            seed=seed,
            priority_counts=priority_counts,
            priority_distribution_str=dist_str,
            mean_feasible_nodes=mean_feasible_nodes,
            metrics=sim_metrics,
        )


def run_single_configuration(
    network_code: str,
    workload_size: int,
    task_profile: str,
    method: str = "Proposed",
    seed: int = 2026,
) -> ExperimentTrialResult:
    """Convenience helper to run a single configuration by network code ('N1', 'N2', 'N3')."""
    if network_code not in NETWORKS:
        raise ValueError(f"Unknown network code '{network_code}'. Expected one of {list(NETWORKS)}.")
    engine = SimulationEngine(NETWORKS[network_code])
    return engine.run_trial(
        workload_size=workload_size,
        task_profile=task_profile,
        method=method,
        seed=seed,
    )