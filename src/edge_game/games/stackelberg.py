"""
Stackelberg leader-follower game module.
Edge servers act as leaders determining optimal pricing strategies,
while edge workloads act as followers reacting to price signals.
"""

from typing import Dict, List
import numpy as np
from src.edge_game.entities.edge_node import EdgeNode
from src.edge_game.entities.edge_server import EdgeServer
from src.edge_game.entities.task import Task


class StackelbergGameSolver:
    """Solves the Stackelberg leader-follower pricing equilibrium."""

    def __init__(self, price_step: float = 0.10) -> None:
        self.price_step = price_step

    def optimize_leader_prices(
        self,
        servers: List[EdgeServer],
        nodes: List[EdgeNode],
        tasks: List[Task],
    ) -> Dict[int, float]:
        """
        Compute optimal leader pricing for each edge server to maximize revenue
        while preventing follower congestion overflow.
        """
        node_map = {n.node_id: n for n in nodes}
        updated_prices: Dict[int, float] = {}

        for server in servers:
            cluster_nodes = [node_map[nid] for nid in server.node_ids if nid in node_map]
            if not cluster_nodes:
                updated_prices[server.server_id] = server.unit_price
                continue

            mean_util = float(np.mean([n.cpu_utilization for n in cluster_nodes]))
            
            # Stackelberg best-response price adjustment rule
            target_price = server.unit_price * (1.0 + 0.35 * (mean_util - 0.70))
            clamped_price = float(min(max(target_price, server.min_price), server.max_price))
            server.unit_price = clamped_price
            updated_prices[server.server_id] = clamped_price

        return updated_prices

    def verify_stackelberg_gap(
        self,
        servers: List[EdgeServer],
        nodes: List[EdgeNode],
        tasks: List[Task],
        current_prices: Dict[int, float],
    ) -> float:
        """
        Independently verify the Stackelberg Gap.
        Evaluates the leader's utility under current prices vs. best-response audited prices.
        """
        if not servers or not tasks:
            return 0.0

        node_map = {n.node_id: n for n in nodes}
        current_revenue = 0.0

        for server in servers:
            p = current_prices.get(server.server_id, server.unit_price)
            cluster_nodes = [node_map[nid] for nid in server.node_ids if nid in node_map]
            cluster_load = sum(n.cpu_allocated for n in cluster_nodes)
            current_revenue += p * cluster_load

        # Audit candidate price perturbations for leader optimality gap
        best_audited_revenue = current_revenue
        for delta in [-0.3, -0.15, 0.15, 0.3]:
            audited_revenue = 0.0
            for server in servers:
                p_cand = max(server.min_price, min(server.max_price, current_prices.get(server.server_id, 1.0) + delta))
                cluster_nodes = [node_map[nid] for nid in server.node_ids if nid in node_map]
                cluster_load = sum(n.cpu_allocated for n in cluster_nodes)
                audited_revenue += p_cand * cluster_load
            if audited_revenue > best_audited_revenue:
                best_audited_revenue = audited_revenue

        gap = max(0.0, (best_audited_revenue - current_revenue) / max(abs(best_audited_revenue), 1.0))
        return float(gap)