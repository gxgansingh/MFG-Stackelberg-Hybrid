"""
Unit tests for the Stackelberg leader-follower pricing solver and Stackelberg gap verification.
"""

import numpy as np
from config.experiment_config import NETWORKS
from src.edge_game.games.stackelberg import StackelbergGameSolver
from src.edge_game.workload.generator import generate_network_topology, generate_workload


def test_stackelberg_solver_respects_price_bounds_and_verifies_gap() -> None:
    """Verify leader prices remain within [min_price, max_price] and Stackelberg gap is valid."""
    rng = np.random.default_rng(2026)
    net_cfg = NETWORKS["N1"]
    nodes, servers = generate_network_topology(net_cfg, rng)
    tasks, _ = generate_workload(num_tasks=150, profile="T1", rng=rng)

    solver = StackelbergGameSolver(num_price_candidates=25)
    prices, elapsed_ms = solver.optimize_leader_prices(
        servers=servers,
        nodes=nodes,
        tasks=tasks,
        priority_aware=True,
    )

    assert len(prices) == len(servers)
    assert elapsed_ms > 0.0
    for server in servers:
        p = prices[server.server_id]
        assert server.min_price <= p <= server.max_price

    stack_gap = solver.verify_stackelberg_gap(
        servers=servers,
        nodes=nodes,
        tasks=tasks,
        current_prices=prices,
    )
    assert not np.isnan(stack_gap)
    assert 0.0 <= stack_gap < 0.10