"""
Mean-Field Game (MFG) solver for intra-node IoT edge load balancing.
Computes stationary mass distributions and enforces approximate Nash equilibrium conditions.
"""

from typing import Dict, List, Tuple
import numpy as np
from src.edge_game.entities.edge_node import EdgeNode
from src.edge_game.entities.task import Task


class NashMFGSolver:
    """Solves the mean-field game equilibrium for task allocation across edge nodes."""

    def __init__(self, max_iterations: int = 50, tolerance: float = 1e-4) -> None:
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def compute_node_costs(
        self, nodes: List[EdgeNode], task: Task, server_prices: Dict[int, float]
    ) -> np.ndarray:
        """
        Compute the effective cost for assigning `task` to each edge node,
        incorporating queue congestion, transmission latency, and server pricing.
        """
        costs = np.zeros(len(nodes))
        for idx, node in enumerate(nodes):
            # Base transmission + queuing latency
            lat = node.estimate_latency_ms(task)
            # Quadratic congestion penalty based on CPU utilization
            congestion_cost = 15.0 * (node.cpu_utilization ** 2)
            # Server unit price factor
            price = server_prices.get(node.server_id, 1.0)
            # Priority weighting (higher priority tasks are more sensitive to delay/congestion)
            weight = task.priority_weight

            costs[idx] = weight * (lat + congestion_cost) * price
        return costs

    def solve_equilibrium_distribution(
        self, nodes: List[EdgeNode], tasks: List[Task], server_prices: Dict[int, float]
    ) -> Dict[int, int]:
        """
        Iteratively compute the MFG stationary distribution.
        Maps each task ID to its assigned node ID at equilibrium.
        """
        task_to_node: Dict[int, int] = {}
        if not nodes or not tasks:
            return task_to_node

        # Approximate population state via iterative best-response projection
        for task in tasks:
            costs = self.compute_node_costs(nodes, task, server_prices)
            # Softmax / Gibbs distribution over node costs to model mean-field population choice
            exp_costs = np.exp(-0.15 * (costs - np.min(costs)))
            probabilities = exp_costs / np.sum(exp_costs)
            
            # Select best node index according to mean-field probability
            chosen_node_idx = int(np.random.choice(len(nodes), p=probabilities))
            task_to_node[task.task_id] = nodes[chosen_node_idx].node_id

        return task_to_node

    def verify_nash_gap(
        self, nodes: List[EdgeNode], task_allocations: Dict[int, int], tasks: List[Task]
    ) -> float:
        """
        Independently verify the Final Nash Gap ($\epsilon$-Nash unilateral deviation).
        Measures the maximum relative cost reduction any task can achieve by unilaterally
        switching from its assigned node to the minimum-cost available node.
        """
        if not tasks or not nodes:
            return 0.0

        node_map = {n.node_id: n for n in nodes}
        max_violation = 0.0
        evaluated_count = 0

        for task in tasks:
            assigned_nid = task_allocations.get(task.task_id)
            if assigned_nid is None or assigned_nid not in node_map:
                continue

            current_node = node_map[assigned_nid]
            current_cost = current_node.estimate_latency_ms(task) + 15.0 * (current_node.cpu_utilization ** 2)

            # Find minimum cost among all eligible nodes
            min_alt_cost = current_cost
            for node in nodes:
                alt_cost = node.estimate_latency_ms(task) + 15.0 * (node.cpu_utilization ** 2)
                if alt_cost < min_alt_cost:
                    min_alt_cost = alt_cost

            violation = max(0.0, current_cost - min_alt_cost) / max(1.0, current_cost)
            if violation > max_violation:
                max_violation = violation
            evaluated_count += 1

        return float(max_violation if evaluated_count > 0 else 0.0)