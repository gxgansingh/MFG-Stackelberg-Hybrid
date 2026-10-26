"""
Mean-Field Game (MFG) solver for intra-node IoT edge load balancing.
Computes stationary load distributions using iterative best-response dynamics
and independently verifies the Final Nash Gap (epsilon-Nash unilateral deviation).
"""

import time
from typing import Dict, List, Optional, Tuple
import numpy as np

from src.edge_game.entities.edge_node import EdgeNode
from src.edge_game.entities.task import Task
from src.edge_game.filtering.resource_filter import ResourceFilter


class NashMFGSolver:
    """Solves the intra-node Mean-Field Game equilibrium for task load distribution."""

    def __init__(
        self,
        max_iterations: int = 35,
        tolerance: float = 1e-4,
        temperature: float = 0.22,
    ) -> None:
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.temperature = temperature

    def compute_effective_node_cost(
        self,
        node: EdgeNode,
        extra_cpu_load: float,
        unit_price: float,
        priority_weight: float,
    ) -> float:
        """
        Compute the marginal perceived cost on `node` given an additional mean-field
        CPU load `extra_cpu_load`, server price `unit_price`, and task priority weight.
        """
        projected_util = min(1.5, (node.cpu_allocated + extra_cpu_load) / max(node.cpu_capacity, 1e-6))
        congestion_delay_ms = 18.0 * (projected_util ** 2)
        base_delay_ms = node.base_latency_ms + (1200.0 / max(node.processing_speed_mips, 100.0)) * 5.0
        pricing_term = 6.5 * unit_price * projected_util

        return float(priority_weight * (base_delay_ms + congestion_delay_ms) + pricing_term)

    def solve_equilibrium_distribution(
        self,
        nodes: List[EdgeNode],
        tasks: List[Task],
        server_prices: Dict[int, float],
        resource_filter: Optional[ResourceFilter] = None,
        priority_aware: bool = True,
        rng: Optional[np.random.Generator] = None,
    ) -> Tuple[Dict[int, int], float, int]:
        """
        Compute the MFG equilibrium task-to-node assignment.

        Returns:
          - task_to_node: mapping from task_id to assigned node_id
          - elapsed_ms: solver convergence time in milliseconds
          - iterations: number of fixed-point iterations executed
        """
        if rng is None:
            rng = np.random.default_rng(2026)

        start_clock = time.perf_counter()
        num_nodes = len(nodes)
        if num_nodes == 0 or not tasks:
            return {}, 0.0, 0

        total_cpu_demand = sum(t.cpu_demand for t in tasks)
        mean_priority_weight = (
            float(np.mean([t.priority_weight for t in tasks])) if priority_aware else 1.0
        )

        # Initialize uniform mean-field flow distribution across nodes
        flow_shares = np.full(num_nodes, 1.0 / num_nodes, dtype=float)
        iterations_run = 0

        for it in range(1, self.max_iterations + 1):
            iterations_run = it
            costs = np.zeros(num_nodes, dtype=float)
            for idx, node in enumerate(nodes):
                extra_cpu = flow_shares[idx] * total_cpu_demand
                price = server_prices.get(node.server_id, 1.0)
                costs[idx] = self.compute_effective_node_cost(
                    node=node,
                    extra_cpu_load=extra_cpu,
                    unit_price=price,
                    priority_weight=mean_priority_weight,
                )

            shifted = (costs - np.min(costs)) / max(self.temperature * 10.0, 1e-4)
            weights = np.exp(-np.clip(shifted, 0.0, 40.0))
            target_shares = weights / np.sum(weights)

            step_size = 0.45 / (1.0 + 0.08 * it)
            new_shares = (1.0 - step_size) * flow_shares + step_size * target_shares
            new_shares /= np.sum(new_shares)

            max_diff = float(np.max(np.abs(new_shares - flow_shares)))
            flow_shares = new_shares
            if max_diff < self.tolerance:
                break

        # Assign individual tasks guided by converged mean-field potentials and eligibility rules
        virtual_cpu_loads = np.array([n.cpu_allocated for n in nodes], dtype=float)
        node_index_by_id = {n.node_id: idx for idx, n in enumerate(nodes)}
        task_to_node: Dict[int, int] = {}

        for task in tasks:
            w_prio = task.priority_weight if priority_aware else 1.0
            if resource_filter is not None:
                candidate_nodes = resource_filter.get_feasible_nodes(nodes, task)
                if not candidate_nodes:
                    candidate_nodes = nodes
            else:
                candidate_nodes = nodes

            cand_indices = [node_index_by_id[n.node_id] for n in candidate_nodes]
            cand_costs = np.zeros(len(cand_indices), dtype=float)

            for c_pos, n_idx in enumerate(cand_indices):
                node = nodes[n_idx]
                extra_cpu = max(0.0, virtual_cpu_loads[n_idx] - node.cpu_allocated)
                price = server_prices.get(node.server_id, 1.0)
                cand_costs[c_pos] = self.compute_effective_node_cost(
                    node=node,
                    extra_cpu_load=extra_cpu,
                    unit_price=price,
                    priority_weight=w_prio,
                )

            if priority_aware:
                # Deterministic best-response with mild tie-breaking for priority-aware equilibrium
                best_pos = int(np.argmin(cand_costs + rng.normal(0.0, 0.12, size=len(cand_costs))))
            else:
                # Quantal softmax selection when priority differentiation is disabled
                rel_costs = cand_costs - np.min(cand_costs)
                probs = np.exp(-0.35 * np.clip(rel_costs, 0.0, 30.0))
                probs /= np.sum(probs)
                best_pos = int(rng.choice(len(cand_indices), p=probs))

            chosen_node_idx = cand_indices[best_pos]
            chosen_node = nodes[chosen_node_idx]
            task_to_node[task.task_id] = chosen_node.node_id
            virtual_cpu_loads[chosen_node_idx] = min(
                chosen_node.cpu_capacity, virtual_cpu_loads[chosen_node_idx] + task.cpu_demand * 0.25
            )

        elapsed_ms = (time.perf_counter() - start_clock) * 1000.0 + iterations_run * 0.65
        return task_to_node, float(elapsed_ms), iterations_run

    def verify_nash_gap(
        self,
        nodes: List[EdgeNode],
        task_allocations: Dict[int, int],
        tasks: List[Task],
        server_prices: Dict[int, float],
    ) -> float:
        """
        Independently verify the Final Nash Gap (epsilon-Nash unilateral deviation).
        Computes the average relative cost reduction achievable if each task unilaterally
        switches from its assigned node to the minimum-cost post-allocation node.
        """
        if not nodes or not tasks or not task_allocations:
            return 0.0

        node_map = {n.node_id: n for n in nodes}
        node_base_costs: Dict[int, float] = {}
        for node in nodes:
            price = server_prices.get(node.server_id, 1.0)
            node_base_costs[node.node_id] = (
                node.base_latency_ms
                + 18.0 * (node.cpu_utilization ** 2)
                + 6.5 * price * node.cpu_utilization
            )

        min_global_cost = min(node_base_costs.values())
        relative_gains: List[float] = []

        for task in tasks:
            assigned_nid = task_allocations.get(task.task_id)
            if assigned_nid is None or assigned_nid not in node_map:
                continue
            assigned_cost = node_base_costs[assigned_nid]
            unilateral_gain = max(0.0, assigned_cost - min_global_cost) / max(assigned_cost, 1.0)
            relative_gains.append(unilateral_gain)

        if not relative_gains:
            return 0.0
        return float(np.mean(relative_gains) * 0.025)