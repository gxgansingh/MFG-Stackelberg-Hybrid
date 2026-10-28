"""
Unit tests for 7-rule resource filtering and P1-P4 priority classification.
"""

import numpy as np
from config.experiment_config import NETWORKS
from src.edge_game.entities.edge_node import EdgeNode
from src.edge_game.entities.task import Task
from src.edge_game.filtering.resource_filter import ResourceFilter
from src.edge_game.workload.generator import generate_workload


def _make_sample_node(
    cpu_allocated: float = 2.0,
    ram_allocated: float = 4.0,
    base_latency_ms: float = 15.0,
) -> EdgeNode:
    return EdgeNode(
        node_id=0,
        server_id=0,
        cpu_capacity=4.0,
        ram_capacity=8.0,
        storage_capacity=128.0,
        bandwidth_capacity=100.0,
        base_latency_ms=base_latency_ms,
        cpu_allocated=cpu_allocated,
        ram_allocated=ram_allocated,
        storage_allocated=20.0,
        bandwidth_allocated=10.0,
    )


def _make_sample_task(
    cpu_demand: float = 1.0,
    ram_demand: float = 1.0,
) -> Task:
    return Task(
        task_id=1,
        cpu_demand=cpu_demand,
        ram_demand=ram_demand,
        storage_demand=2.0,
        bandwidth_demand=5.0,
        instruction_length=300.0,
        deadline_ms=45.0,
        urgency_factor=0.8,
        criticality_factor=0.8,
    )


def test_eligible_node_passes_all_seven_rules() -> None:
    """Verify that a node well within capacity and latency limits passes all 7 rules."""
    res_filter = ResourceFilter(NETWORKS["N1"])
    node = _make_sample_node(cpu_allocated=1.0, ram_allocated=2.0, base_latency_ms=12.0)
    task = _make_sample_task(cpu_demand=0.5, ram_demand=1.0)

    result = res_filter.evaluate_node_for_task(node, task)
    assert result.is_feasible is True
    assert all(result.as_dict().values())


def test_projected_cpu_utilization_limit_enforced() -> None:
    """Verify that projected CPU utilization above 85% fails eligibility."""
    res_filter = ResourceFilter(NETWORKS["N1"])
    # Node has 4.0 cores, 3.0 allocated (75%). Adding 0.6 cores -> 3.6/4.0 = 90% (> 85%)
    node = _make_sample_node(cpu_allocated=3.0, ram_allocated=2.0, base_latency_ms=10.0)
    task = _make_sample_task(cpu_demand=0.6, ram_demand=0.5)

    result = res_filter.evaluate_node_for_task(node, task)
    assert result.cpu_ok is True
    assert result.cpu_utilization_ok is False
    assert result.is_feasible is False


def test_projected_ram_utilization_limit_enforced() -> None:
    """Verify that projected RAM utilization above 90% fails eligibility."""
    res_filter = ResourceFilter(NETWORKS["N1"])
    # Node has 8.0 GB RAM, 6.8 GB allocated (85%). Adding 0.8 GB -> 7.6/8.0 = 95% (> 90%)
    node = _make_sample_node(cpu_allocated=1.0, ram_allocated=6.8, base_latency_ms=10.0)
    task = _make_sample_task(cpu_demand=0.4, ram_demand=0.8)

    result = res_filter.evaluate_node_for_task(node, task)
    assert result.ram_ok is True
    assert result.ram_utilization_ok is False
    assert result.is_feasible is False


def test_latency_threshold_enforced() -> None:
    """Verify that estimated latency exceeding 50 ms fails eligibility."""
    res_filter = ResourceFilter(NETWORKS["N1"])
    node = _make_sample_node(cpu_allocated=1.0, ram_allocated=2.0, base_latency_ms=49.5)
    task = _make_sample_task(cpu_demand=0.5, ram_demand=0.5)

    result = res_filter.evaluate_node_for_task(node, task)
    assert result.latency_ok is False
    assert result.is_feasible is False


def test_workload_priority_distribution_sums_to_total_load() -> None:
    """Verify that generated workloads produce observed P1-P4 counts summing to workload size."""
    rng = np.random.default_rng(1234)
    tasks, counts = generate_workload(num_tasks=1250, profile="T1", rng=rng)
    assert len(tasks) == 1250
    assert sum(counts.values()) == 1250
    assert set(counts.keys()) == {"P1", "P2", "P3", "P4"}