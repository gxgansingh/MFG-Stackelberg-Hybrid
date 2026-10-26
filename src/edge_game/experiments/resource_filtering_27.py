"""
Phase-1 experiment module: Network parameter tables, 7-rule resource filtering
audits across workloads (1,250, 3,000, and 5,000 tasks), and the 27 experimental
configurations (E1-E27) with observed P1-P4 priority distributions.
"""

from typing import Dict, List
import numpy as np
import pandas as pd

from config.experiment_config import (
    DEFAULT_RANDOM_SEED,
    ILLUSTRATIVE_EXPERIMENT_LABELS,
    NETWORKS,
    TASK_PROFILES,
    WORKLOAD_LEVELS,
)
from src.edge_game.filtering.resource_filter import ResourceFilter
from src.edge_game.simulation.engine import SimulationEngine
from src.edge_game.workload.generator import generate_network_topology, generate_workload


def build_table1_network_parameters() -> pd.DataFrame:
    """
    Generate Table 1: Network configuration and resource parameters for
    Network-1 (Small), Network-2 (Intermediate), and Network-3 (Stress).
    """
    rows = [
        ("Edge nodes", "50", "150", "300"),
        ("Edge servers", "5", "15", "30"),
        ("CPU capacity per node", "2–8 cores", "2–8 cores", "2–8 cores"),
        ("RAM per node", "4–16 GB", "4–16 GB", "4–16 GB"),
        ("Storage per node", "64–256 GB", "64–256 GB", "64–256 GB"),
        ("Bandwidth per node", "50–200 Mbps", "50–200 Mbps", "50–200 Mbps"),
        ("Maximum CPU utilization", "85%", "85%", "85%"),
        ("Maximum RAM utilization", "90%", "90%", "90%"),
        ("Maximum latency", "50 ms", "50 ms", "50 ms"),
        (
            "Load: 1,250 tasks – tasks/node",
            f"{1250 / 50:.0f}",
            f"{1250 / 150:.2f}",
            f"{1250 / 300:.2f}",
        ),
        (
            "Load: 3,000 tasks – tasks/node",
            f"{3000 / 50:.0f}",
            f"{3000 / 150:.0f}",
            f"{3000 / 300:.0f}",
        ),
        (
            "Load: 5,000 tasks – tasks/node",
            f"{5000 / 50:.0f}",
            f"{5000 / 150:.2f}",
            f"{5000 / 300:.2f}",
        ),
        ("Feasible node count", "Dynamic", "Dynamic", "Dynamic"),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "Parameter",
            "Network-1 (Small)",
            "Network-2 (Intermediate)",
            "Network-3 (Stress)",
        ],
    )


def build_table2_filtering_decisions(
    network_code: str,
    seed: int = DEFAULT_RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generate Table 2 for a specific network (N1, N2, or N3):
    Evaluates the 7 resource-filtering criteria across 1,250, 3,000, and 5,000 tasks.
    """
    if network_code not in NETWORKS:
        raise ValueError(f"Invalid network_code '{network_code}'. Expected one of {list(NETWORKS)}.")

    net_cfg = NETWORKS[network_code]
    res_filter = ResourceFilter(net_cfg)
    rng = np.random.default_rng(seed)

    criteria_meta = [
        ("CPU", "Available CPU >= task demand", "cpu_ok"),
        ("RAM", "Available RAM >= task demand", "ram_ok"),
        ("Storage", "Available storage >= task demand", "storage_ok"),
        ("Bandwidth", "Available bandwidth >= task demand", "bandwidth_ok"),
        ("Latency", "Estimated latency <= 50 ms", "latency_ok"),
        ("CPU utilization", "Projected utilization <= 85%", "cpu_utilization_ok"),
        ("RAM utilization", "Projected utilization <= 90%", "ram_utilization_ok"),
    ]

    workload_results: Dict[int, Dict[str, str]] = {}
    for w_size in WORKLOAD_LEVELS:
        nodes, _ = generate_network_topology(net_cfg, rng, initial_load_factor=0.35)
        tasks, _ = generate_workload(w_size, "T2", rng)
        audit = res_filter.audit_batch_filtering(nodes, tasks, max_sample_tasks=200)
        workload_results[w_size] = {
            rule_key: f"Apply ({audit[rule_key]:.1f}% viable)"
            for _, _, rule_key in criteria_meta
        }

    rows = []
    for metric_label, rule_desc, rule_key in criteria_meta:
        rows.append(
            {
                "Network": network_code,
                "Metric": metric_label,
                "Eligibility rule": rule_desc,
                "1,250 tasks": workload_results[1250][rule_key],
                "3,000 tasks": workload_results[3000][rule_key],
                "5,000 tasks": workload_results[5000][rule_key],
            }
        )
    return pd.DataFrame(rows)


def run_27_experimental_configurations(
    seed: int = DEFAULT_RANDOM_SEED,
) -> pd.DataFrame:
    """
    Execute all 27 Experimental Configurations (E1 through E27) across
    3 networks (N1, N2, N3) x 3 workloads (1,250, 3,000, 5,000) x 3 profiles (T1, T2, T3).
    Replaces the single static priority label with the observed P1, P2, P3, and P4
    task distribution and reports dynamic feasible node counts and performance metrics.
    """
    records: List[Dict[str, float | int | str]] = []
    exp_counter = 1

    for net_code in ["N1", "N2", "N3"]:
        net_cfg = NETWORKS[net_code]
        engine = SimulationEngine(net_cfg)

        for w_size in WORKLOAD_LEVELS:
            for profile in TASK_PROFILES:
                trial_seed = seed + exp_counter * 17
                trial = engine.run_trial(
                    workload_size=w_size,
                    task_profile=profile,
                    method="Proposed",
                    seed=trial_seed,
                )

                illustrative_label = ILLUSTRATIVE_EXPERIMENT_LABELS[exp_counter - 1]
                records.append(
                    {
                        "Exp.": f"E{exp_counter}",
                        "Network": net_code,
                        "Edge Nodes": net_cfg.num_nodes,
                        "Servers": net_cfg.num_servers,
                        "Task Load": w_size,
                        "Tasks/Node": round(w_size / net_cfg.num_nodes, 2),
                        "Task Profile": profile,
                        "Illustrative Label": illustrative_label,
                        "P1": trial.priority_counts["P1"],
                        "P2": trial.priority_counts["P2"],
                        "P3": trial.priority_counts["P3"],
                        "P4": trial.priority_counts["P4"],
                        "Observed Priority Distribution (P1–P4)": trial.priority_distribution_str,
                        "Mean Feasible Nodes": round(trial.mean_feasible_nodes, 1),
                        "Utility": round(trial.metrics.utility, 2),
                        "Jain's Fairness": round(trial.metrics.jains_fairness, 4),
                        "Load Variance": round(trial.metrics.load_variance, 3),
                        "Convergence Time (ms)": round(trial.metrics.convergence_time_ms, 2),
                        "Throughput (tasks/s)": round(trial.metrics.throughput_tasks_per_sec, 2),
                        "Response Time (ms)": round(trial.metrics.response_time_ms, 2),
                        "Final Nash Gap": round(trial.metrics.nash_gap, 5),
                        "Stackelberg Gap": round(trial.metrics.stackelberg_gap, 5),
                    }
                )
                exp_counter += 1

    return pd.DataFrame(records)