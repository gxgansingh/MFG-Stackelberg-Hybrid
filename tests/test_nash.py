"""
Unit tests for the Mean-Field Game (MFG) Nash equilibrium solver and Nash gap verification.
"""

import numpy as np
from config.experiment_config import NETWORKS
from src.edge_game.filtering.resource_filter import ResourceFilter
from src.edge_game.games.nash_mfg import NashMFGSolver
from src.edge_game.workload.generator import generate_network_topology, generate_workload


def test_nash_mfg_solver_assigns_all_tasks_and_computes_non_negative_gap() -> None:
    """Verify that NashMFGSolver assigns every task to a valid node and computes a finite Nash gap."""
    rng = np.random.default_rng(2026)
    net_cfg = NETWORKS["N1"]
    nodes, servers = generate_network_topology(net_cfg, rng)
    tasks, _ = generate_workload(num_tasks=120, profile="T2", rng=rng)
    server_prices = {s.server_id: s.unit_price for s in servers}

    solver = NashMFGSolver(max_iterations=25, tolerance=1e-4)
    res_filter = ResourceFilter(net_cfg)

    allocations, elapsed_ms, iterations = solver.solve_equilibrium_distribution(
        nodes=nodes,
        tasks=tasks,
        server_prices=server_prices,
        resource_filter=res_filter,
        priority_aware=True,
        rng=rng,
    )

    assert len(allocations) == len(tasks)
    assert elapsed_ms > 0.0
    assert 1 <= iterations <= 25

    node_map = {n.node_id: n for n in nodes}
    for task in tasks:
        node_map[allocations[task.task_id]].allocate_task(task)

    nash_gap = solver.verify_nash_gap(
        nodes=nodes,
        task_allocations=allocations,
        tasks=tasks,
        server_prices=server_prices,
    )
    assert not np.isnan(nash_gap)
    assert 0.0 <= nash_gap < 0.05