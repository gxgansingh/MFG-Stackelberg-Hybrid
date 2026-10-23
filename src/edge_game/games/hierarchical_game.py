"""
Hierarchical game coordination engine combining MFG Nash equilibrium
and Stackelberg pricing with priority-aware scheduling.
"""

from typing import Dict, List, Tuple
import numpy as np
from src.edge_game.entities.edge_node import EdgeNode
from src.edge_game.entities.edge_server import EdgeServer
from src.edge_game.entities.task import Task
from src.edge_game.games.nash_mfg import NashMFGSolver
from src.edge_game.games.stackelberg import StackelbergGameSolver


class HierarchicalGameEngine:
    """Coordinates the hierarchical MFG + Stackelberg game execution across ablation methods."""

    def __init__(self, method: str) -> None:
        self.method = method
        self.nash_solver = NashMFGSolver()
        self.stackelberg_solver = StackelbergGameSolver()

    def execute_coordination(
        self,
        nodes: List[EdgeNode],
        servers: List[EdgeServer],
        tasks: List[Task],
    ) -> Tuple[Dict[int, int], Dict[int, float], float, float]:
        """
        Execute the game coordination according to the selected ablation method:
          - 'A1: MFG only': MFG Nash solver without Stackelberg pricing or priority weighting.
          - 'A2: Stackelberg only': Stackelberg pricing without MFG intra-node redistribution.
          - 'A3: MFG+Stackelberg': Joint MFG + Stackelberg without priority differentiation.
          - 'Proposed': Priority-aware MFG + Stackelberg.
        """
        server_prices = {s.server_id: s.unit_price for s in servers}
        node_map = {n.node_id: n for n in nodes}

        # Sort tasks based on method capability
        if self.method == "Proposed":
            # Priority-aware sorting (P1 highest priority)
            sorted_tasks = sorted(tasks, key=lambda t: t.priority_weight, reverse=True)
        else:
            sorted_tasks = list(tasks)

        # 1. Stackelberg Leader Pricing Phase (active for A2, A3, Proposed)
        if self.method in ["A2: Stackelberg only", "A3: MFG+Stackelberg", "Proposed"]:
            server_prices = self.stackelberg_solver.optimize_leader_prices(servers, nodes, sorted_tasks)

        # 2. MFG Nash Equilibrium Phase (active for A1, A3, Proposed)
        if self.method in ["A1: MFG only", "A3: MFG+Stackelberg", "Proposed"]:
            allocations = self.nash_solver.solve_equilibrium_distribution(nodes, sorted_tasks, server_prices)
        elif self.method == "A2: Stackelberg only":
            # Fallback greedy round-robin distribution when MFG is ablated
            allocations = {}
            for idx, task in enumerate(sorted_tasks):
                target_node = nodes[idx % len(nodes)]
                allocations[task.task_id] = target_node.node_id
        else:
            raise ValueError(f"Unknown ablation method '{self.method}'")

        # 3. Commit allocations to nodes and execute task lifecycles
        for task in sorted_tasks:
            nid = allocations.get(task.task_id, nodes[0].node_id)
            if nid in node_map:
                node_map[nid].allocate_task(task)

        # 4. Independent equilibrium gap verification
        nash_gap = 0.0
        stack_gap = 0.0

        if self.method in ["A1: MFG only", "A3: MFG+Stackelberg", "Proposed"]:
            nash_gap = self.nash_solver.verify_nash_gap(nodes, allocations, sorted_tasks)
        else:
            nash_gap = float("nan")

        if self.method in ["A2: Stackelberg only", "A3: MFG+Stackelberg", "Proposed"]:
            stack_gap = self.stackelberg_solver.verify_stackelberg_gap(servers, nodes, sorted_tasks, server_prices)
        else:
            stack_gap = float("nan")

        return allocations, server_prices, nash_gap, stack_gap