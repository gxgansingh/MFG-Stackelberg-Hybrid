import numpy as np


def jain_fairness(values: list[float]) -> float:
    """Calculate Jain's fairness index for a collection of values."""
    array = np.asarray(values, dtype=float)

    if array.size == 0:
        return 1.0

    if not np.all(np.isfinite(array)):
        raise ValueError("Fairness values must be finite.")

    if np.any(array < 0):
        raise ValueError("Fairness values cannot be negative.")

    denominator = len(array) * np.sum(array**2)

    if denominator == 0:
        return 1.0

    return float(np.sum(array) ** 2 / denominator)


def _mean_available(records: list[dict], key: str) -> float:
    """Calculate the mean of available finite values for a metric."""
    values = np.asarray(
        [
            record[key]
            for record in records
            if key in record and record[key] is not None
        ],
        dtype=float,
    )

    values = values[np.isfinite(values)]

    if values.size == 0:
        return float("nan")

    return float(np.mean(values))


def compute_run_metrics(
    records: list[dict],
    duration_ticks: int,
    all_nodes: list | None = None,
) -> dict:
    """
    Compute run-level metrics.

    When all_nodes is supplied, fairness includes every node in the
    network, including nodes that received no tasks. Load variance
    uses the final utilization of every node.

    The optional all_nodes parameter preserves compatibility with
    older callers, although production simulations should supply it.
    """
    if not records:
        raise ValueError(
            "Cannot compute metrics from an empty record set."
        )

    utilities = np.asarray(
        [record["utility"] for record in records],
        dtype=float,
    )

    response_times = np.asarray(
        [record["response_time_ms"] for record in records],
        dtype=float,
    )

    # Initialize every network node with zero assignments so that
    # idle nodes are included in the fairness calculation.
    if all_nodes is not None:
        assignment_counts = {
            node.node_id: 0
            for node in all_nodes
        }
    else:
        # Compatibility fallback for older callers.
        assignment_counts = {
            record["node_id"]: 0
            for record in records
        }

    for record in records:
        node_id = record["node_id"]
        assignment_counts[node_id] = (
            assignment_counts.get(node_id, 0) + 1
        )

    assignment_counts_array = np.asarray(
        list(assignment_counts.values()),
        dtype=float,
    )

    # Measure final utilization across the entire network.
    if all_nodes is not None:
        final_node_loads = np.asarray(
            [
                node.utilization_state()
                for node in all_nodes
            ],
            dtype=float,
        )
    else:
        # Compatibility fallback. This is not the preferred
        # production definition because records are task-level.
        final_node_loads = np.asarray(
            [
                record["node_state"]
                for record in records
            ],
            dtype=float,
        )

    return {
        "utility_mean": float(np.mean(utilities)),

        "jain_fairness": jain_fairness(
            assignment_counts_array.tolist()
        ),

        "load_variance": float(
            np.var(final_node_loads)
        ),

        # Allocation time measures the allocation decision overhead.
        # It is distinct from MFG convergence time.
        "allocation_time_seconds": _mean_available(
            records,
            "allocation_time_seconds",
        ),

        "mfg_convergence_time_seconds": _mean_available(
            records,
            "mfg_convergence_time_seconds",
        ),

        "throughput": float(
            sum(record["completed"] for record in records)
            / max(duration_ticks, 1)
        ),

        "response_time_mean": float(
            np.mean(response_times)
        ),

        "nash_gap": _mean_available(
            records,
            "nash_gap",
        ),

        "nash_best_response_cost": _mean_available(
            records,
            "nash_best_response_cost",
        ),

        "nash_selected_cost": _mean_available(
            records,
            "nash_selected_cost",
        ),

        "nash_best_alternative_cost": _mean_available(
            records,
            "nash_best_alternative_cost",
        ),

        "nash_deviation_margin": _mean_available(
            records,
            "nash_deviation_margin",
        ),

        "stackelberg_gap": _mean_available(
            records,
            "stackelberg_gap",
        ),

        "stackelberg_margin": _mean_available(
            records,
            "stackelberg_margin",
        ),

        "stackelberg_leader_cost": _mean_available(
            records,
            "stackelberg_leader_cost",
        ),

        "stackelberg_best_alternative_cost": _mean_available(
            records,
            "stackelberg_best_alternative_cost",
        ),

        "stackelberg_deviation_margin": _mean_available(
            records,
            "stackelberg_deviation_margin",
        ),

        "completed_tasks": int(
            sum(record["completed"] for record in records)
        ),
    }


def safe_utility(task, node, decision) -> float:
    """Calculate a common evaluation utility for every policy."""
    resource_term = max(
        0.0,
        min(
            1.0,
            1.0 - node.utilization_state(),
        ),
    )

    latency_limit = max(
        float(task.latency_limit_ms),
        1.0,
    )

    latency_term = max(
        0.0,
        min(
            1.0,
            1.0 - node.latency_ms / latency_limit,
        ),
    )

    priority_term = max(
        0.0,
        min(
            1.0,
            float(task.priority_score),
        ),
    )

    # Use the same evaluation formula for every policy.
    # Internal optimization costs are deliberately excluded.
    return float(
        0.40 * resource_term
        + 0.30 * latency_term
        + 0.30 * priority_term
    )