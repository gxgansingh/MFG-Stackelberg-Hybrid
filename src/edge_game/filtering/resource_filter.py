"""
Multi-criteria resource filtering engine for edge node eligibility evaluation.
Implements the 7 filtering criteria defined in Table 2 of the specification.
"""

from dataclasses import dataclass
from typing import Dict, List
from config.experiment_config import NetworkConfig
from src.edge_game.entities.edge_node import EdgeNode
from src.edge_game.entities.task import Task


@dataclass(frozen=True)
class EligibilityResult:
    """Detailed rule-by-rule eligibility outcome for a (node, task) pair."""
    node_id: int
    task_id: int
    cpu_ok: bool
    ram_ok: bool
    storage_ok: bool
    bandwidth_ok: bool
    latency_ok: bool
    cpu_utilization_ok: bool
    ram_utilization_ok: bool

    @property
    def is_feasible(self) -> bool:
        """Return True if and only if all 7 filtering criteria are satisfied."""
        return (
            self.cpu_ok
            and self.ram_ok
            and self.storage_ok
            and self.bandwidth_ok
            and self.latency_ok
            and self.cpu_utilization_ok
            and self.ram_utilization_ok
        )

    def as_dict(self) -> Dict[str, bool]:
        """Return a dictionary mapping each of the 7 criteria keys to its boolean result."""
        return {
            "cpu_ok": self.cpu_ok,
            "ram_ok": self.ram_ok,
            "storage_ok": self.storage_ok,
            "bandwidth_ok": self.bandwidth_ok,
            "latency_ok": self.latency_ok,
            "cpu_utilization_ok": self.cpu_utilization_ok,
            "ram_utilization_ok": self.ram_utilization_ok,
        }


class ResourceFilter:
    """Evaluates edge node eligibility against task resource and QoS requirements."""

    def __init__(self, net_config: NetworkConfig) -> None:
        self.net_config = net_config

    def evaluate_node_for_task(self, node: EdgeNode, task: Task) -> EligibilityResult:
        """
        Check all 7 eligibility rules from Table 2 for a specific node and task:
          1. Available CPU >= task demand
          2. Available RAM >= task demand
          3. Available storage >= task demand
          4. Available bandwidth >= task demand
          5. Estimated latency <= 50 ms
          6. Projected CPU utilization <= 85%
          7. Projected RAM utilization <= 90%
        """
        cpu_ok = node.available_cpu >= task.cpu_demand
        ram_ok = node.available_ram >= task.ram_demand
        storage_ok = node.available_storage >= task.storage_demand
        bandwidth_ok = node.available_bandwidth >= task.bandwidth_demand

        estimated_latency = node.estimate_latency_ms(task)
        latency_ok = estimated_latency <= self.net_config.max_latency_ms

        proj_cpu_util = node.projected_cpu_utilization(task.cpu_demand)
        cpu_util_ok = proj_cpu_util <= self.net_config.max_cpu_utilization

        proj_ram_util = node.projected_ram_utilization(task.ram_demand)
        ram_util_ok = proj_ram_util <= self.net_config.max_ram_utilization

        return EligibilityResult(
            node_id=node.node_id,
            task_id=task.task_id,
            cpu_ok=cpu_ok,
            ram_ok=ram_ok,
            storage_ok=storage_ok,
            bandwidth_ok=bandwidth_ok,
            latency_ok=latency_ok,
            cpu_utilization_ok=cpu_util_ok,
            ram_utilization_ok=ram_util_ok,
        )

    def get_feasible_nodes(self, nodes: List[EdgeNode], task: Task) -> List[EdgeNode]:
        """Return the subset of edge nodes that satisfy all 7 eligibility rules for `task`."""
        return [
            node
            for node in nodes
            if self.evaluate_node_for_task(node, task).is_feasible
        ]

    def audit_batch_filtering(
        self,
        nodes: List[EdgeNode],
        tasks: List[Task],
        max_sample_tasks: int = 250,
    ) -> Dict[str, float]:
        """
        Evaluate a sample of tasks across all nodes and return the pass rate (in %)
        for each of the 7 rules as well as the mean dynamic feasible node count.
        """
        sampled_tasks = tasks[: min(len(tasks), max_sample_tasks)]
        if not sampled_tasks or not nodes:
            return {
                "cpu_ok": 0.0,
                "ram_ok": 0.0,
                "storage_ok": 0.0,
                "bandwidth_ok": 0.0,
                "latency_ok": 0.0,
                "cpu_utilization_ok": 0.0,
                "ram_utilization_ok": 0.0,
                "mean_feasible_nodes": 0.0,
            }

        rule_counts: Dict[str, int] = {
            "cpu_ok": 0,
            "ram_ok": 0,
            "storage_ok": 0,
            "bandwidth_ok": 0,
            "latency_ok": 0,
            "cpu_utilization_ok": 0,
            "ram_utilization_ok": 0,
        }
        feasible_node_counts: List[int] = []
        total_pairs = len(sampled_tasks) * len(nodes)

        for task in sampled_tasks:
            feasible_for_task = 0
            for node in nodes:
                res = self.evaluate_node_for_task(node, task)
                for key, passed in res.as_dict().items():
                    if passed:
                        rule_counts[key] += 1
                if res.is_feasible:
                    feasible_for_task += 1
            feasible_node_counts.append(feasible_for_task)

        summary: Dict[str, float] = {
            key: (count / total_pairs) * 100.0 for key, count in rule_counts.items()
        }
        summary["mean_feasible_nodes"] = float(
            sum(feasible_node_counts) / len(feasible_node_counts)
        )
        return summary