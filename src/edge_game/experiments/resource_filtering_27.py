from __future__ import annotations

import csv
import gzip
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Experiment configuration
# ============================================================

SEED = 20261029
OUTPUT_DIR = Path("outputs/experiments_27")

LOADS = (1250, 3000, 5000)
PROFILES = ("T1", "T2", "T3")

NETWORKS = {
    "N1": {"nodes": 50, "servers": 5},
    "N2": {"nodes": 150, "servers": 15},
    "N3": {"nodes": 300, "servers": 30},
}

CPU_FREQUENCY_GHZ = 2.5
MAX_CPU_UTILIZATION = 0.85
MAX_RAM_UTILIZATION = 0.90
MAX_LATENCY_MS = 50.0

# The following are explicit workload assumptions.
# Replace them with measured or documented workload parameters.
PROFILE_PARAMETERS = {
    # CPU-intensive tasks
    "T1": {
        "cycles_million": (40.0, 100.0),
        "ram_gb": (0.25, 1.50),
        "input_mb": (0.10, 1.00),
        "output_mb": (0.01, 0.20),
        "storage_gb": (0.05, 0.50),
        "cpu_budget_fraction": 0.50,
        "transfer_budget_fraction": 0.30,
    },
    # Latency-sensitive tasks
    "T2": {
        "cycles_million": (10.0, 50.0),
        "ram_gb": (0.25, 1.00),
        "input_mb": (0.05, 0.50),
        "output_mb": (0.01, 0.10),
        "storage_gb": (0.02, 0.20),
        "cpu_budget_fraction": 0.40,
        "transfer_budget_fraction": 0.35,
    },
    # Service/resource-intensive tasks
    "T3": {
        "cycles_million": (20.0, 80.0),
        "ram_gb": (0.75, 3.00),
        "input_mb": (0.25, 2.00),
        "output_mb": (0.05, 0.50),
        "storage_gb": (0.10, 1.50),
        "cpu_budget_fraction": 0.50,
        "transfer_budget_fraction": 0.30,
    },
}


@dataclass(frozen=True)
class Task:
    experiment_id: str
    network_id: str
    load: int
    profile_id: str
    task_id: str
    cpu_cycles: float
    cpu_demand_gc_s: float
    ram_demand_gb: float
    storage_demand_gb: float
    input_mb: float
    output_mb: float
    bandwidth_demand_mbps: float
    latency_deadline_ms: float
    priority_score: float
    priority_class: str


def priority_class(score: float) -> str:
    if score >= 0.75:
        return "P1"
    if score >= 0.50:
        return "P2"
    if score >= 0.25:
        return "P3"
    return "P4"


def make_priority(rng: random.Random) -> tuple[float, str]:
    urgency = rng.random()
    latency_sensitivity = rng.random()
    service_importance = rng.random()

    score = (
        0.4 * urgency
        + 0.4 * latency_sensitivity
        + 0.2 * service_importance
    )
    return score, priority_class(score)


def build_network(network_id: str) -> list[dict]:
    """Create a reproducible heterogeneous network."""
    config = NETWORKS[network_id]
    rng = random.Random(SEED + {"N1": 1, "N2": 2, "N3": 3}[network_id])

    nodes = []

    for i in range(config["nodes"]):
        server_number = i // 10 + 1
        node_number = i % 10 + 1

        cores = rng.randint(2, 8)
        frequency_ghz = CPU_FREQUENCY_GHZ

        total_cpu_gc_s = cores * frequency_ghz

        ram_gb = rng.uniform(4.0, 16.0)
        storage_gb = rng.uniform(64.0, 256.0)
        bandwidth_mbps = rng.uniform(50.0, 200.0)

        # Random initial utilization creates heterogeneous starting states.
        cpu_used_gc_s = total_cpu_gc_s * rng.uniform(0.10, 0.45)
        ram_used_gb = ram_gb * rng.uniform(0.20, 0.65)
        storage_used_gb = storage_gb * rng.uniform(0.10, 0.60)
        bandwidth_used_mbps = bandwidth_mbps * rng.uniform(0.10, 0.50)

        nodes.append({
            "network_id": network_id,
            "server_id": f"{network_id}-S{server_number:02d}",
            "node_id": f"{network_id}-S{server_number:02d}-E{node_number:02d}",
            "cores": cores,
            "frequency_ghz": frequency_ghz,
            "cpu_total_gc_s": total_cpu_gc_s,
            "cpu_used_gc_s": cpu_used_gc_s,
            "ram_total_gb": ram_gb,
            "ram_used_gb": ram_used_gb,
            "storage_total_gb": storage_gb,
            "storage_used_gb": storage_used_gb,
            "bandwidth_total_mbps": bandwidth_mbps,
            "bandwidth_used_mbps": bandwidth_used_mbps,
            "propagation_ms": rng.uniform(1.0, 12.0),
            "queue_delay_ms": rng.uniform(0.5, 8.0),
        })

    return nodes


def build_tasks(
    experiment_id: str,
    network_id: str,
    load: int,
    profile_id: str,
) -> list[Task]:
    params = PROFILE_PARAMETERS[profile_id]

    # Stable seed for each experimental condition.
    seed = (
        SEED
        + sum(ord(c) for c in network_id)
        + load * 7
        + sum(ord(c) for c in profile_id)
    )
    rng = random.Random(seed)

    tasks = []

    for i in range(load):
        deadline_ms = MAX_LATENCY_MS

        cycles = rng.uniform(*params["cycles_million"]) * 1e6
        ram_gb = rng.uniform(*params["ram_gb"])
        input_mb = rng.uniform(*params["input_mb"])
        output_mb = rng.uniform(*params["output_mb"])
        storage_gb = rng.uniform(*params["storage_gb"])

        cpu_budget_s = (
            deadline_ms / 1000.0
            * params["cpu_budget_fraction"]
        )
        transfer_budget_s = (
            deadline_ms / 1000.0
            * params["transfer_budget_fraction"]
        )

        # GC/s = 1e9 cycles/s.
        cpu_demand_gc_s = cycles / cpu_budget_s / 1e9

        # Decimal MB: 1 MB = 8 megabits.
        bandwidth_demand_mbps = (
            8.0 * (input_mb + output_mb) / transfer_budget_s
        )

        score, pclass = make_priority(rng)

        tasks.append(Task(
            experiment_id=experiment_id,
            network_id=network_id,
            load=load,
            profile_id=profile_id,
            task_id=f"{experiment_id}-T{i + 1:05d}",
            cpu_cycles=cycles,
            cpu_demand_gc_s=cpu_demand_gc_s,
            ram_demand_gb=ram_gb,
            storage_demand_gb=storage_gb,
            input_mb=input_mb,
            output_mb=output_mb,
            bandwidth_demand_mbps=bandwidth_demand_mbps,
            latency_deadline_ms=deadline_ms,
            priority_score=score,
            priority_class=pclass,
        ))

    return tasks


def evaluate_candidate(task: Task, node: dict) -> dict:
    """Evaluate one task against one edge node without allocating it."""
    cpu_projected = (
        node["cpu_used_gc_s"] + task.cpu_demand_gc_s
    ) / node["cpu_total_gc_s"]

    ram_projected = (
        node["ram_used_gb"] + task.ram_demand_gb
    ) / node["ram_total_gb"]

    cpu_headroom_gc_s = max(
        0.0,
        MAX_CPU_UTILIZATION * node["cpu_total_gc_s"]
        - node["cpu_used_gc_s"],
    )

    ram_headroom_gb = max(
        0.0,
        MAX_RAM_UTILIZATION * node["ram_total_gb"]
        - node["ram_used_gb"],
    )

    storage_available_gb = (
        node["storage_total_gb"] - node["storage_used_gb"]
    )

    bandwidth_available_mbps = (
        node["bandwidth_total_mbps"] - node["bandwidth_used_mbps"]
    )

    cpu_pass = (
        task.cpu_demand_gc_s <= cpu_headroom_gc_s
        and cpu_projected <= MAX_CPU_UTILIZATION
    )

    ram_pass = (
        task.ram_demand_gb <= ram_headroom_gb
        and ram_projected <= MAX_RAM_UTILIZATION
    )

    storage_pass = task.storage_demand_gb <= storage_available_gb

    bandwidth_pass = (
        task.bandwidth_demand_mbps <= bandwidth_available_mbps
    )

    # Estimate processing time using the node's remaining CPU rate.
    cpu_rate_available = max(
        1e-12,
        min(
            cpu_headroom_gc_s,
            MAX_CPU_UTILIZATION * node["cpu_total_gc_s"]
            - node["cpu_used_gc_s"],
        ),
    )

    processing_ms = (
        task.cpu_demand_gc_s / cpu_rate_available
        * (task.latency_deadline_ms
           * PROFILE_PARAMETERS[task.profile_id]["cpu_budget_fraction"])
    )

    transfer_ms = (
        8.0 * (task.input_mb + task.output_mb)
        / max(bandwidth_available_mbps, 1e-12)
        * 1000.0
    )

    latency_ms = (
        node["propagation_ms"]
        + node["queue_delay_ms"]
        + processing_ms
        + transfer_ms
    )

    latency_pass = latency_ms <= MAX_LATENCY_MS

    reasons = []
    for name, passed in [
        ("CPU", cpu_pass),
        ("RAM", ram_pass),
        ("STORAGE", storage_pass),
        ("BANDWIDTH", bandwidth_pass),
        ("LATENCY", latency_pass),
    ]:
        if not passed:
            reasons.append(name)

    return {
        "experiment_id": task.experiment_id,
        "network_id": task.network_id,
        "load": task.load,
        "profile_id": task.profile_id,
        "task_id": task.task_id,
        "server_id": node["server_id"],
        "node_id": node["node_id"],

        "task_cpu_demand_gc_s": task.cpu_demand_gc_s,
        "node_cpu_total_gc_s": node["cpu_total_gc_s"],
        "node_cpu_used_gc_s": node["cpu_used_gc_s"],
        "node_cpu_headroom_gc_s": cpu_headroom_gc_s,
        "projected_cpu_utilization_pct": 100.0 * cpu_projected,

        "task_ram_demand_gb": task.ram_demand_gb,
        "node_ram_total_gb": node["ram_total_gb"],
        "node_ram_used_gb": node["ram_used_gb"],
        "node_ram_available_gb": node["ram_total_gb"] - node["ram_used_gb"],
        "projected_ram_utilization_pct": 100.0 * ram_projected,

        "task_storage_demand_gb": task.storage_demand_gb,
        "node_storage_available_gb": storage_available_gb,

        "task_bandwidth_demand_mbps": task.bandwidth_demand_mbps,
        "node_bandwidth_available_mbps": bandwidth_available_mbps,

        "propagation_ms": node["propagation_ms"],
        "queue_delay_ms": node["queue_delay_ms"],
        "processing_ms_estimate": processing_ms,
        "transfer_ms_estimate": transfer_ms,
        "estimated_latency_ms": latency_ms,

        "cpu_pass": cpu_pass,
        "ram_pass": ram_pass,
        "storage_pass": storage_pass,
        "bandwidth_pass": bandwidth_pass,
        "latency_pass": latency_pass,

        "feasible": not reasons,
        "rejection_reasons": ";".join(reasons),
    }


def run_experiments() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    task_output = OUTPUT_DIR / "task_workload_records.csv"
    node_output = OUTPUT_DIR / "node_capacity_records.csv"
    audit_output = OUTPUT_DIR / "candidate_filtering_audit.csv.gz"
    feasible_output = OUTPUT_DIR / "feasible_nodes_per_task.csv"
    summary_output = OUTPUT_DIR / "filtering_summary_27.csv"
    manifest_output = OUTPUT_DIR / "experiment_manifest.csv"

    manifest = []
    summaries = []

    with (
        task_output.open("w", newline="", encoding="utf-8") as task_file,
        node_output.open("w", newline="", encoding="utf-8") as node_file,
        gzip.open(audit_output, "wt", newline="", encoding="utf-8") as audit_file,
        feasible_output.open("w", newline="", encoding="utf-8") as feasible_file,
    ):
        task_writer = csv.DictWriter(
            task_file, fieldnames=list(asdict(
                Task("E1", "N1", 1250, "T1", "dummy", 1, 1, 1, 1, 1, 1, 1, 50, 0.5, "P3")
            ).keys())
        )
        task_writer.writeheader()

        node_fields = [
            "network_id", "server_id", "node_id", "cores",
            "frequency_ghz", "cpu_total_gc_s", "cpu_used_gc_s",
            "ram_total_gb", "ram_used_gb",
            "storage_total_gb", "storage_used_gb",
            "bandwidth_total_mbps", "bandwidth_used_mbps",
            "propagation_ms", "queue_delay_ms",
        ]
        node_writer = csv.DictWriter(node_file, fieldnames=node_fields)
        node_writer.writeheader()

        audit_fields = [
            "experiment_id", "network_id", "load", "profile_id",
            "task_id", "server_id", "node_id",
            "task_cpu_demand_gc_s", "node_cpu_total_gc_s",
            "node_cpu_used_gc_s", "node_cpu_headroom_gc_s",
            "projected_cpu_utilization_pct",
            "task_ram_demand_gb", "node_ram_total_gb",
            "node_ram_used_gb", "node_ram_available_gb",
            "projected_ram_utilization_pct",
            "task_storage_demand_gb", "node_storage_available_gb",
            "task_bandwidth_demand_mbps", "node_bandwidth_available_mbps",
            "propagation_ms", "queue_delay_ms",
            "processing_ms_estimate", "transfer_ms_estimate",
            "estimated_latency_ms",
            "cpu_pass", "ram_pass", "storage_pass",
            "bandwidth_pass", "latency_pass",
            "feasible", "rejection_reasons",
        ]
        audit_writer = csv.DictWriter(audit_file, fieldnames=audit_fields)
        audit_writer.writeheader()

        feasible_writer = csv.DictWriter(
            feasible_file,
            fieldnames=[
                "experiment_id", "network_id", "load", "profile_id",
                "task_id", "feasible_node_ids", "feasible_node_count",
                "no_feasible_node",
            ],
        )
        feasible_writer.writeheader()

        for network_id, net_config in NETWORKS.items():
            nodes = build_network(network_id)

            for node in nodes:
                node_writer.writerow(node)

            for load in LOADS:
                for profile in PROFILES:
                    experiment_id = (
                        f"{network_id}_{load}_{profile}"
                    )

                    manifest.append({
                        "experiment_id": experiment_id,
                        "network_id": network_id,
                        "edge_nodes": net_config["nodes"],
                        "edge_servers": net_config["servers"],
                        "task_load": load,
                        "profile_id": profile,
                        "seed": SEED,
                        "node_capacity_model": "seeded heterogeneous ranges",
                        "task_model": "assumed profile distributions",
                    })

                    tasks = build_tasks(
                        experiment_id, network_id, load, profile
                    )

                    task_writer.writerows(asdict(task) for task in tasks)

                    total_pairs = 0
                    feasible_pairs = 0
                    no_feasible_tasks = 0
                    reason_counts = {
                        "CPU": 0, "RAM": 0, "STORAGE": 0,
                        "BANDWIDTH": 0, "LATENCY": 0,
                    }

                    for task in tasks:
                        feasible_nodes = []

                        for node in nodes:
                            row = evaluate_candidate(task, node)
                            audit_writer.writerow(row)
                            total_pairs += 1

                            for reason in reason_counts:
                                if reason in row["rejection_reasons"].split(";"):
                                    reason_counts[reason] += 1

                            if row["feasible"]:
                                feasible_nodes.append(node["node_id"])
                                feasible_pairs += 1

                        if not feasible_nodes:
                            no_feasible_tasks += 1

                        feasible_writer.writerow({
                            "experiment_id": experiment_id,
                            "network_id": network_id,
                            "load": load,
                            "profile_id": profile,
                            "task_id": task.task_id,
                            "feasible_node_ids": ";".join(feasible_nodes),
                            "feasible_node_count": len(feasible_nodes),
                            "no_feasible_node": not bool(feasible_nodes),
                        })

                    summaries.append({
                        "experiment_id": experiment_id,
                        "network_id": network_id,
                        "edge_nodes": len(nodes),
                        "edge_servers": net_config["servers"],
                        "load": load,
                        "profile_id": profile,
                        "tasks_generated": len(tasks),
                        "candidate_pairs_examined": total_pairs,
                        "feasible_task_node_pairs": feasible_pairs,
                        "infeasible_task_node_pairs": total_pairs - feasible_pairs,
                        "mean_feasible_nodes_per_task": (
                            feasible_pairs / len(tasks)
                        ),
                        "tasks_with_no_feasible_node": no_feasible_tasks,
                        "task_feasibility_rate_pct": (
                            100.0 * (len(tasks) - no_feasible_tasks) / len(tasks)
                        ),
                        "candidate_cpu_failed_checks": reason_counts["CPU"],
                        "candidate_ram_failed_checks": reason_counts["RAM"],
                        "candidate_storage_failed_checks": reason_counts["STORAGE"],
                        "candidate_bandwidth_failed_checks": reason_counts["BANDWIDTH"],
                        "candidate_latency_failed_checks": reason_counts["LATENCY"],
                    })

                    print(
                        f"{experiment_id}: tasks={load}, "
                        f"nodes={len(nodes)}, "
                        f"feasible_pairs={feasible_pairs}/{total_pairs}, "
                        f"tasks_without_candidate={no_feasible_tasks}"
                    )

    pd.DataFrame(manifest).to_csv(manifest_output, index=False)
    pd.DataFrame(summaries).to_csv(summary_output, index=False)

    # Store assumptions alongside the outputs for reproducibility.
    with (OUTPUT_DIR / "model_assumptions.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump({
            "seed": SEED,
            "cpu_frequency_ghz": CPU_FREQUENCY_GHZ,
            "max_cpu_utilization": MAX_CPU_UTILIZATION,
            "max_ram_utilization": MAX_RAM_UTILIZATION,
            "max_latency_ms": MAX_LATENCY_MS,
            "network_ranges": NETWORKS,
            "profile_parameters": PROFILE_PARAMETERS,
            "warning": (
                "Task distributions, initial utilization, and latency "
                "components are assumptions, not measured hardware data."
            ),
        }, f, indent=2)

    print(f"\nCompleted {len(manifest)} filtering configurations.")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    run_experiments()