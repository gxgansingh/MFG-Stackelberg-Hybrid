import numpy as np

from src.edge_game.simulation.metrics import compute_run_metrics


class FakeNode:
    def __init__(self, node_id, utilization):
        self.node_id = node_id
        self.utilization = utilization

    def utilization_state(self):
        return self.utilization


def make_record(node_id, utility, node_state):
    return {
        "task_id": f"T-{node_id}-{utility}",
        "node_id": node_id,
        "utility": utility,
        "node_state": node_state,
        "response_time_ms": 10.0,
        "completed": 1,
        "allocation_time_seconds": 0.001,
        "mfg_convergence_time_seconds": 0.0005,
    }


def test_fairness_includes_idle_nodes():
    nodes = [
        FakeNode("N1", 0.8),
        FakeNode("N2", 0.4),
        FakeNode("N3", 0.0),
    ]

    records = [
        make_record("N1", 0.5, 0.2),
        make_record("N1", 0.6, 0.3),
        make_record("N2", 0.7, 0.4),
    ]

    result = compute_run_metrics(
        records,
        duration_ticks=10,
        all_nodes=nodes,
    )

    # Assignment counts are [2, 1, 0], including the idle node.
    expected_fairness = (2 + 1 + 0) ** 2 / (
        3 * (2**2 + 1**2 + 0**2)
    )

    assert np.isclose(
        result["jain_fairness"],
        expected_fairness,
    )


def test_load_variance_uses_final_node_utilization():
    nodes = [
        FakeNode("N1", 0.8),
        FakeNode("N2", 0.4),
        FakeNode("N3", 0.0),
    ]

    records = [
        make_record("N1", 0.5, 0.2),
        make_record("N1", 0.6, 0.3),
        make_record("N2", 0.7, 0.4),
    ]

    result = compute_run_metrics(
        records,
        duration_ticks=10,
        all_nodes=nodes,
    )

    expected_variance = np.var([0.8, 0.4, 0.0])

    assert np.isclose(
        result["load_variance"],
        expected_variance,
    )


def test_allocation_and_convergence_times_are_separate():
    nodes = [
        FakeNode("N1", 0.5),
        FakeNode("N2", 0.3),
    ]

    records = [
        make_record("N1", 0.5, 0.2),
        make_record("N2", 0.7, 0.4),
    ]

    result = compute_run_metrics(
        records,
        duration_ticks=10,
        all_nodes=nodes,
    )

    assert np.isclose(
        result["allocation_time_seconds"],
        0.001,
    )

    assert np.isclose(
        result["mfg_convergence_time_seconds"],
        0.0005,
    )


def test_throughput_uses_completed_tasks_and_duration():
    nodes = [
        FakeNode("N1", 0.5),
        FakeNode("N2", 0.3),
    ]

    records = [
        make_record("N1", 0.5, 0.2),
        make_record("N2", 0.7, 0.4),
    ]

    result = compute_run_metrics(
        records,
        duration_ticks=10,
        all_nodes=nodes,
    )

    assert np.isclose(result["throughput"], 0.2)
    assert result["completed_tasks"] == 2