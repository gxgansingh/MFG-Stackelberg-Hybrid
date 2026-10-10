from dataclasses import dataclass
from time import perf_counter

import numpy as np

from config.experiment_config import MFG_UTILITY_WEIGHTS
from .nash_mfg import MeanFieldGame, MFGDecision, NashDiagnostics
from .stackelberg import StackelbergGame


POLICY_VARIANTS = (
    "A1_MFG_ONLY",
    "A2_STACKELBERG_ONLY",
    "A3_MFG_STACKELBERG",
    "PROPOSED",
)


@dataclass(frozen=True)
class HierarchicalDecision:
    server_id: str
    node_id: str

    nash_gap: float
    stackelberg_gap: float
    stackelberg_margin: float

    mfg_state: float
    mfg_control: float
    mfg_cost: float
    mfg_iterations: int

    nash_best_response_cost: float
    nash_selected_cost: float
    nash_best_alternative_cost: float

    stackelberg_leader_cost: float
    stackelberg_best_alternative_cost: float

    nash_deviation_margin: float = 0.0
    stackelberg_deviation_margin: float = 0.0
    mfg_convergence_time_seconds: float = 0.0
    policy_variant: str = "PROPOSED"


class HierarchicalGame:
    def __init__(self, policy_variant="PROPOSED"):
        if policy_variant not in POLICY_VARIANTS:
            raise ValueError(
                f"Unknown policy variant: {policy_variant}. "
                f"Expected one of {POLICY_VARIANTS}."
            )

        self.policy_variant = policy_variant
        self.stackelberg = StackelbergGame()

        priority_weights = dict(MFG_UTILITY_WEIGHTS)
        priority_weights["priority"] = 0.0

        self.unprioritized_mfg = MeanFieldGame(
            utility_weights=priority_weights
        )
        self.priority_aware_mfg = MeanFieldGame()

    @staticmethod
    def _all_feasible_nodes(feasible_by_server):
        return [
            node
            for nodes in feasible_by_server.values()
            for node in nodes
        ]

    @staticmethod
    def _heuristic_cost(node):
        return (
            0.45 * node.utilization_state()
            + 0.25 * min(node.latency_ms / 100.0, 1.0)
            + 0.20 * node.energy_pressure
            + 0.10 * min(node.queue_pressure, 1.0)
        )

    @staticmethod
    def _empty_nash_diagnostics():
        return NashDiagnostics(
            converged=False,
            iterations=0,
            distribution_residual=float("nan"),
            policy_residual=float("nan"),
            nash_gap=float("nan"),
            best_response_cost=float("nan"),
            selected_cost=float("nan"),
            best_alternative_cost=float("nan"),
        )

    @staticmethod
    def _make_decision(
        server_id,
        mfg_decision,
        nash_diag,
        leader_cost,
        alternative_leader_cost,
        stackelberg_margin,
        elapsed,
        policy_variant,
        stackelberg_gap=float("nan"),
    ):
        selected_cost = nash_diag.selected_cost
        alternative_cost = nash_diag.best_alternative_cost

        return HierarchicalDecision(
            server_id=server_id,
            node_id=mfg_decision.node_id,
            nash_gap=nash_diag.nash_gap,
            stackelberg_gap=stackelberg_gap,
            stackelberg_margin=stackelberg_margin,
            mfg_state=mfg_decision.state,
            mfg_control=mfg_decision.control,
            mfg_cost=mfg_decision.cost,
            mfg_iterations=mfg_decision.iterations,
            nash_best_response_cost=nash_diag.best_response_cost,
            nash_selected_cost=selected_cost,
            nash_best_alternative_cost=alternative_cost,
            stackelberg_leader_cost=leader_cost,
            stackelberg_best_alternative_cost=alternative_leader_cost,
            nash_deviation_margin=(
                selected_cost - alternative_cost
                if np.isfinite(selected_cost)
                and np.isfinite(alternative_cost)
                else float("nan")
            ),
            stackelberg_deviation_margin=(
                leader_cost - alternative_leader_cost
                if np.isfinite(leader_cost)
                and np.isfinite(alternative_leader_cost)
                else float("nan")
            ),
            mfg_convergence_time_seconds=elapsed,
            policy_variant=policy_variant,
        )

    def _allocate_mfg_only(self, task, feasible_by_server):
        nodes = self._all_feasible_nodes(feasible_by_server)
        start = perf_counter()

        decision, diagnostics = self.unprioritized_mfg.solve(
            task, nodes
        )

        elapsed = perf_counter() - start

        return self._make_decision(
            server_id=decision.server_id,
            mfg_decision=decision,
            nash_diag=diagnostics,
            leader_cost=float("nan"),
            alternative_leader_cost=float("nan"),
            stackelberg_margin=float("nan"),
            elapsed=elapsed,
            policy_variant=self.policy_variant,
        )

    def _allocate_stackelberg_only(
        self, task, servers, feasible_by_server
    ):
        server_decisions = []

        for server in servers:
            nodes = feasible_by_server.get(server.server_id, [])
            if not nodes:
                continue

            selected_node = min(
                nodes,
                key=lambda node: (
                    self._heuristic_cost(node),
                    node.node_id,
                ),
            )

            cost = self._heuristic_cost(selected_node)
            state = selected_node.utilization_state()

            follower = MFGDecision(
                node_id=selected_node.node_id,
                server_id=selected_node.server_id,
                state=state,
                control=max(0.0, min(1.0, 1.0 - state)),
                mean_field=float("nan"),
                cost=cost,
                rank=1,
                iterations=0,
            )

            server_decisions.append(
                (
                    server.server_id,
                    follower,
                    self._empty_nash_diagnostics(),
                    server,
                )
            )

        stack_decision = self.stackelberg.choose_server(
            task, server_decisions
        )

        return self._make_decision(
            server_id=stack_decision.server_id,
            mfg_decision=next(
                item[1]
                for item in server_decisions
                if item[0] == stack_decision.server_id
            ),
            nash_diag=self._empty_nash_diagnostics(),
            leader_cost=stack_decision.leader_cost,
            alternative_leader_cost=(
                stack_decision.best_alternative_cost
            ),
            stackelberg_margin=stack_decision.margin,
            stackelberg_gap=stack_decision.stackelberg_gap,
            elapsed=0.0,
            policy_variant=self.policy_variant,
        )

    def _allocate_hierarchical(
        self, task, servers, feasible_by_server
    ):
        server_decisions = []
        total_mfg_time = 0.0

        mfg = (
            self.priority_aware_mfg
            if self.policy_variant == "PROPOSED"
            else self.unprioritized_mfg
        )

        for server in servers:
            nodes = feasible_by_server.get(server.server_id, [])
            if not nodes:
                continue

            start = perf_counter()
            mfg_decision, diagnostics = mfg.solve(task, nodes)
            total_mfg_time += perf_counter() - start

            server_decisions.append(
                (
                    server.server_id,
                    mfg_decision,
                    diagnostics,
                    server,
                )
            )

        if not server_decisions:
            raise ValueError(
                "No feasible server remains after resource filtering."
            )

        stack_decision = self.stackelberg.choose_server(
            task, server_decisions
        )

        _, mfg_decision, diagnostics, _ = next(
            item
            for item in server_decisions
            if item[0] == stack_decision.server_id
        )

        return self._make_decision(
            server_id=stack_decision.server_id,
            mfg_decision=mfg_decision,
            nash_diag=diagnostics,
            leader_cost=stack_decision.leader_cost,
            alternative_leader_cost=(
                stack_decision.best_alternative_cost
            ),
            stackelberg_margin=stack_decision.margin,
            stackelberg_gap=stack_decision.stackelberg_gap,
            elapsed=total_mfg_time,
            policy_variant=self.policy_variant,
        )

    def allocate(self, task, servers, feasible_by_server):
        if not self._all_feasible_nodes(feasible_by_server):
            raise ValueError(
                "No feasible nodes remain after resource filtering."
            )

        if self.policy_variant == "A1_MFG_ONLY":
            return self._allocate_mfg_only(task, feasible_by_server)

        if self.policy_variant == "A2_STACKELBERG_ONLY":
            return self._allocate_stackelberg_only(
                task, servers, feasible_by_server
            )

        return self._allocate_hierarchical(
            task, servers, feasible_by_server
        )
