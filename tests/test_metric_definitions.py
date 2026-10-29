"""
Unit tests for mathematical metric definitions: Jain's Fairness Index,
Load Variance, and System Metrics computation.
"""

import numpy as np
from config.experiment_config import NETWORKS
from src.edge_game.simulation.metrics import (
    compute_jains_fairness_index,
    compute_load_variance,
    compute_system_metrics,
)
from src.edge_game.workload.generator import generate_network_topology, generate_workload


def test_jains_fairness_index_bounds_and_identities() -> None:
    """Verify Jain's Fairness Index is 1.0 for equal allocations and bounded in (0, 1]."""
    uniform_load = np.array([0.5, 0.5, 0.5, 0.5])
    assert np.isclose(compute_jains_fairness_index(uniform_load), 1.0)

    skewed_load = np.array([0.9, 0.1, 0.1, 0.1])
    fairness = compute_jains_fairness_index(skewed_load)
    assert 0.25 <= fairness < 1.0


def test_load_variance_zero_for_identical_utilizations() -> None:
    """Verify Load Variance is 0.0 when all nodes have identical utilization."""
    uniform_load = np.array([0.65, 0.65, 0.65, 0.65, 0.65])
    assert np.isclose(compute_load_variance(uniform_load), 0.0)


def test_compute_system_metrics_returns_valid_values() -> None:
    """Verify compute_system_metrics produces finite values for all 6 performance metrics."""
    rng = np.random.default_rng(2026)
    nodes, servers = generate_network_topology(NETWORKS["N1"], rng)
    tasks, _ = generate_workload(num_tasks=50, profile="T1", rng=rng)

    for idx, task in enumerate(tasks):
        nodes[idx % len(nodes)].allocate_task(task)

    server_prices = {s.server_id: s.unit_price for s in servers}
    metrics = compute_system_metrics(
        nodes=nodes,
        servers=servers,
        tasks=tasks,
        server_prices=server_prices,
        convergence_time_ms=25.0,
        nash_gap=0.0008,
        stackelberg_gap=0.0021,
    )

    assert metrics.utility > 0.0
    assert 0.0 < metrics.jains_fairness <= 1.0
    assert metrics.load_variance >= 0.0
    assert metrics.convergence_time_ms == 25.0
    assert metrics.throughput_tasks_per_sec > 0.0
    assert metrics.response_time_ms > 0.0