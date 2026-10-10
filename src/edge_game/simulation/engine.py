from time import perf_counter

from ..filtering.filtering_audit import build_filtering_record
from ..filtering.resource_filter import ResourceFilter
from ..games.hierarchical_game import HierarchicalGame
from .metrics import compute_run_metrics, safe_utility


class SimulationEngine:
    def __init__(
        self,
        environment,
        policy_variant="PROPOSED",
    ):
        self.environment = environment
        self.filter = ResourceFilter()
        self.game = HierarchicalGame(
            policy_variant=policy_variant
        )
        self.policy_variant = policy_variant

    def run(self, tasks, duration_ticks):
        records = []
        filtering_records = []
        start = perf_counter()

        for task in tasks:
            feasible_by_server = {}

            # Filter nodes before running the allocation game.
            for server in self.environment.servers:
                feasible_nodes = []

                for node in server.nodes:
                    result = self.filter.evaluate(
                        task,
                        node,
                    )

                    filtering_records.append(
                        build_filtering_record(
                            task,
                            node,
                            result,
                        )
                    )

                    if result.feasible:
                        feasible_nodes.append(node)

                if feasible_nodes:
                    feasible_by_server[server.server_id] = (
                        feasible_nodes
                    )

            # Skip tasks for which no node is feasible.
            if not feasible_by_server:
                continue

            # Measure allocation overhead separately from the
            # MFG convergence time reported by the game.
            allocation_start = perf_counter()

            decision = self.game.allocate(
                task,
                self.environment.servers,
                feasible_by_server,
            )

            allocation_time = (
                perf_counter() - allocation_start
            )

            server = next(
                server
                for server in self.environment.servers
                if server.server_id == decision.server_id
            )

            node = next(
                node
                for node in server.nodes
                if node.node_id == decision.node_id
            )

            response_time = (
                server.network_latency_ms
                + node.latency_ms
                + 4.0 * (1.0 + node.queue_pressure)
            )

            utility = safe_utility(
                task,
                node,
                decision,
            )

            # Apply the selected allocation to the environment.
            self.environment.apply_allocation(
                task,
                decision.server_id,
                decision.node_id,
            )

            records.append(
                {
                    "task_id": task.task_id,
                    "priority_profile": task.priority_profile,
                    "priority_class": task.priority_label,
                    "priority_score": task.priority_score,
                    "policy_variant": self.policy_variant,

                    "server_id": decision.server_id,
                    "node_id": decision.node_id,

                    "utility": utility,
                    "node_state": decision.mfg_state,
                    "mfg_control": decision.mfg_control,
                    "mfg_cost": decision.mfg_cost,
                    "mfg_iterations": decision.mfg_iterations,

                    "allocation_time_seconds": allocation_time,

                    "mfg_convergence_time_seconds": (
                        decision.mfg_convergence_time_seconds
                    ),

                    "nash_gap": decision.nash_gap,
                    "nash_best_response_cost": (
                        decision.nash_best_response_cost
                    ),
                    "nash_selected_cost": (
                        decision.nash_selected_cost
                    ),
                    "nash_best_alternative_cost": (
                        decision.nash_best_alternative_cost
                    ),
                    "nash_deviation_margin": (
                        decision.nash_deviation_margin
                    ),

                    "stackelberg_gap": (
                        decision.stackelberg_gap
                    ),
                    "stackelberg_margin": (
                        decision.stackelberg_margin
                    ),
                    "stackelberg_leader_cost": (
                        decision.stackelberg_leader_cost
                    ),
                    "stackelberg_best_alternative_cost": (
                        decision.stackelberg_best_alternative_cost
                    ),
                    "stackelberg_deviation_margin": (
                        decision.stackelberg_deviation_margin
                    ),

                    "response_time_ms": response_time,
                    "completed": 1,
                }
            )

        if not records:
            raise ValueError(
                "No tasks were allocated. Check the workload, "
                "resource constraints, and filtering configuration."
            )

        # Include all nodes, not just nodes that received tasks.
        all_nodes = [
            node
            for server in self.environment.servers
            for node in server.nodes
        ]

        metrics = compute_run_metrics(
            records,
            duration_ticks,
            all_nodes=all_nodes,
        )

        metrics["wall_clock_seconds"] = (
            perf_counter() - start
        )

        metrics["policy_variant"] = self.policy_variant

        return (
            metrics,
            records,
            filtering_records,
        )