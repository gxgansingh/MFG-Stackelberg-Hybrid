from dataclasses import dataclass

import numpy as np

from config.experiment_config import (
    MFG_MAX_ITERATIONS,
    MFG_TOLERANCE,
    MFG_UTILITY_WEIGHTS,
)


@dataclass(frozen=True)
class MFGDecision:
    node_id: str
    server_id: str
    state: float
    control: float
    mean_field: float
    cost: float
    rank: int
    iterations: int


@dataclass(frozen=True)
class NashDiagnostics:
    converged: bool
    iterations: int
    distribution_residual: float
    policy_residual: float
    nash_gap: float
    best_response_cost: float = 0.0
    selected_cost: float = 0.0
    best_alternative_cost: float = 0.0


class MeanFieldGame:
    def __init__(
        self,
        utility_weights=None,
        tolerance=MFG_TOLERANCE,
        max_iterations=MFG_MAX_ITERATIONS,
    ):
        self.weights = dict(
            utility_weights or MFG_UTILITY_WEIGHTS
        )
        self.tolerance = tolerance
        self.max_iterations = max_iterations

    def node_state(self, node) -> float:
        return node.utilization_state()

    @staticmethod
    def _latency_suitability(task, node) -> float:
        """Return normalized latency suitability in [0, 1]."""
        latency_limit = max(float(task.latency_limit_ms), 1.0)
        ratio = node.latency_ms / latency_limit
        return max(0.0, min(1.0, 1.0 - ratio))

    def running_cost(self, task, node, mean_field: float) -> float:
        state = self.node_state(node)
        control = max(0.0, min(1.0, 1.0 - state))

        priority_level = max(
            0.0,
            min(1.0, task.priority_class / 4.0),
        )

        latency_suitability = self._latency_suitability(
            task,
            node,
        )

        # Priority reward depends on the candidate node. A higher-priority
        # task gains more from a node with spare capacity and suitable
        # latency. Unlike a task-only constant, this can change node ranking.
        priority_reward = (
            self.weights["priority"]
            * priority_level
            * (
                0.5 * control
                + 0.5 * latency_suitability
            )
        )

        latency_cost = (
            self.weights["latency"]
            * task.latency_sensitivity
            * state**2
        )

        resource_cost = (
            self.weights["resource"]
            * (1.0 - control) ** 2
        )

        queue_cost = (
            self.weights["queue"]
            * mean_field**2
        )

        energy_cost = (
            self.weights["energy"]
            * node.energy_pressure
            * control**2
        )

        return (
            latency_cost
            + resource_cost
            + queue_cost
            + energy_cost
            - priority_reward
        )

    def solve(self, task, feasible_nodes):
        if not feasible_nodes:
            raise ValueError("MFG received no feasible nodes.")

        mean_field = float(
            np.mean(
                [
                    self.node_state(node)
                    for node in feasible_nodes
                ]
            )
        )

        previous_node = None
        policy_residual = float("inf")
        distribution_residual = float("inf")
        iteration = self.max_iterations

        for iteration in range(
            1,
            self.max_iterations + 1,
        ):
            scored = sorted(
                (
                    (
                        self.running_cost(
                            task,
                            node,
                            mean_field,
                        ),
                        node,
                    )
                    for node in feasible_nodes
                ),
                key=lambda item: (
                    item[0],
                    item[1].node_id,
                ),
            )

            _, best_node = scored[0]

            next_mean_field = float(
                np.mean(
                    [
                        0.5 * self.node_state(node)
                        + 0.5 * (1.0 - node.cpu_load)
                        for node in feasible_nodes
                    ]
                )
            )

            distribution_residual = abs(
                next_mean_field - mean_field
            )

            policy_residual = (
                0.0
                if previous_node == best_node.node_id
                else 0.5
            )

            previous_node = best_node.node_id
            mean_field = next_mean_field

            if (
                distribution_residual <= self.tolerance
                and policy_residual <= self.tolerance
            ):
                break

        final_scores = sorted(
            (
                (
                    self.running_cost(
                        task,
                        node,
                        mean_field,
                    ),
                    node,
                )
                for node in feasible_nodes
            ),
            key=lambda item: (
                item[0],
                item[1].node_id,
            ),
        )

        selected_cost, selected_node = final_scores[0]

        rank = next(
            index
            for index, (_, node) in enumerate(
                final_scores,
                start=1,
            )
            if node.node_id == selected_node.node_id
        )

        state = self.node_state(selected_node)
        control = max(
            0.0,
            min(1.0, 1.0 - state),
        )

        best_response_cost = final_scores[0][0]

        if len(final_scores) > 1:
            best_alternative_cost = final_scores[1][0]
        else:
            best_alternative_cost = selected_cost

        # This is a candidate-ranking regret diagnostic, not by itself
        # proof of a Nash equilibrium for the coupled mean-field game.
        nash_gap = max(
            0.0,
            selected_cost - best_alternative_cost,
        )

        converged = (
            distribution_residual <= self.tolerance
            and policy_residual <= self.tolerance
        )

        decision = MFGDecision(
            node_id=selected_node.node_id,
            server_id=selected_node.server_id,
            state=state,
            control=control,
            mean_field=mean_field,
            cost=selected_cost,
            rank=rank,
            iterations=iteration,
        )

        diagnostics = NashDiagnostics(
            converged=converged,
            iterations=iteration,
            distribution_residual=distribution_residual,
            policy_residual=policy_residual,
            nash_gap=nash_gap,
            best_response_cost=best_response_cost,
            selected_cost=selected_cost,
            best_alternative_cost=best_alternative_cost,
        )

        return decision, diagnostics
