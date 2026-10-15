import json
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from config.experiment_config import (
    LOADS,
    NETWORKS,
    PRIORITY_PROFILES,
    REPLICATED_SEEDS,
    TICKS,
)

from src.edge_game.games.hierarchical_game import POLICY_VARIANTS
from src.edge_game.simulation.engine import SimulationEngine
from src.edge_game.simulation.environment import Network1Environment
from src.edge_game.workload.generator import generate_tasks


OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments_27"


POLICY_LABELS = {
    "A1_MFG_ONLY": "MFG",
    "A2_STACKELBERG_ONLY": "Stackelberg",
    "A3_MFG_STACKELBERG": "NonPriorityHybrid",
    "PROPOSED": "Proposed",
}

POLICIES = tuple(POLICY_LABELS)


def make_seed(network_id, load, profile_id, seed_id):
    """Generate reproducible seeds for experiment configurations."""

    network_offset = {
        "N1": 100000,
        "N2": 200000,
        "N3": 300000,
    }

    profile_offset = {
        "T1": 1000,
        "T2": 2000,
        "T3": 3000,
    }

    return (
        20261007
        + network_offset[network_id]
        + load
        + profile_offset[profile_id]
        + seed_id * 1009
    )


def summarize_filtering(records):
    """Summarize filtering records without assuming unknown field names."""

    result = {
        "filter_audit_rows": len(records),
        "filter_feasible_rows": None,
        "filter_infeasible_rows": None,
        "filter_feasible_rate": float("nan"),
    }

    if not records:
        result.update({
            "filter_feasible_rows": 0,
            "filter_infeasible_rows": 0,
            "filter_feasible_rate": float("nan"),
        })
        return result

    feasible_key = next(
        (
            key
            for key in (
                "feasible",
                "is_feasible",
                "resource_feasible",
            )
            if key in records[0]
        ),
        None,
    )

    if feasible_key is None:
        return result

    flags = [
        bool(record.get(feasible_key, False))
        for record in records
    ]

    feasible_count = sum(flags)

    result.update({
        "filter_feasible_rows": feasible_count,
        "filter_infeasible_rows": len(flags) - feasible_count,
        "filter_feasible_rate": feasible_count / len(flags),
    })

    return result


def run_experiments():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run_rows = []
    allocation_rows = []
    filter_rows = []
    workload_rows = []

    expected_runs = (
        len(NETWORKS)
        * len(LOADS)
        * len(PRIORITY_PROFILES)
        * len(REPLICATED_SEEDS)
        * len(POLICIES)
    )

    completed_runs = 0

    for network_id, network_config in NETWORKS.items():

        for load in LOADS:

            for profile in PRIORITY_PROFILES:

                for seed_id in REPLICATED_SEEDS:

                    seed = make_seed(
                        network_id,
                        load,
                        profile.profile_id,
                        seed_id,
                    )

                    experiment_id = (
                        f"{network_id}_{load}_{profile.profile_id}"
                    )

                    run_id = f"{experiment_id}_seed{seed_id}"

                    # Generate one workload per configuration and seed.
                    # Every policy in this block receives the same tasks.
                    tasks = generate_tasks(
                        count=load,
                        profile_id=profile.profile_id,
                        seed=seed,
                        ticks=TICKS,
                    )

                    for task in tasks:
                        workload_rows.append({
                            "experiment_id": experiment_id,
                            "network_id": network_id,
                            "load": load,
                            "profile_id": profile.profile_id,
                            "seed_id": seed_id,
                            "seed": seed,
                            "task_id": task.task_id,
                            "arrival_tick": task.arrival_tick,
                            "cpu_required_gcps": (
                                task.cpu_required_gcps
                            ),
                            "memory_required_gb": (
                                task.memory_required_gb
                            ),
                            "bandwidth_required_mbps": (
                                task.bandwidth_required_mbps
                            ),
                            "latency_limit_ms": (
                                task.latency_limit_ms
                            ),
                            "energy_limit_j": task.energy_limit_j,
                            "queue_limit": task.queue_limit,
                            "priority_score": task.priority_score,
                            "priority_class": task.priority_label,
                            "urgency": task.urgency,
                            "latency_sensitivity": (
                                task.latency_sensitivity
                            ),
                            "service_importance": (
                                task.service_importance
                            ),
                        })

                    for policy in POLICIES:

                        # Reset environment for each policy.
                        environment = Network1Environment.create(
                            seed=seed,
                            network_id=network_id,
                        )

                        engine = SimulationEngine(
                            environment,
                            policy_variant=policy,
                        )

                        metrics, records, filtering_records = (
                            engine.run(
                                tasks,
                                duration_ticks=TICKS,
                            )
                        )

                        allocated = int(
                            metrics["completed_tasks"]
                        )

                        submitted = len(tasks)
                        rejected = submitted - allocated
                        label = POLICY_LABELS[policy]

                        filter_metrics = summarize_filtering(
                            filtering_records
                        )

                        run_rows.append({
                            "experiment_id": experiment_id,
                            "run_id": run_id,
                            "network_id": network_id,
                            "server_count": (
                                network_config["server_count"]
                            ),
                            "nodes_per_server": (
                                network_config["nodes_per_server"]
                            ),
                            "total_nodes": (
                                network_config["server_count"]
                                * network_config["nodes_per_server"]
                            ),
                            "load": load,
                            "profile_id": profile.profile_id,
                            "profile_name": profile.name,
                            "seed_id": seed_id,
                            "seed": seed,
                            "policy_variant": label,
                            "implementation_policy_variant": policy,
                            "submitted_tasks": submitted,
                            "allocated_tasks": allocated,
                            "rejected_tasks": rejected,
                            "allocation_success_ratio": (
                                allocated / submitted
                                if submitted else float("nan")
                            ),
                            # Alias expected by the analysis script.
                            "decision_time_seconds": metrics.get(
                                "allocation_time_seconds",
                                float("nan"),
                            ),
                            **metrics,
                            **filter_metrics,
                        })

                        for record in records:
                            allocation_rows.append({
                                "experiment_id": experiment_id,
                                "run_id": run_id,
                                "network_id": network_id,
                                "load": load,
                                "profile_id": profile.profile_id,
                                "seed_id": seed_id,
                                "policy_variant": label,
                                **record,
                            })

                        filter_rows.append({
                            "experiment_id": experiment_id,
                            "run_id": run_id,
                            "network_id": network_id,
                            "load": load,
                            "profile_id": profile.profile_id,
                            "seed_id": seed_id,
                            "policy_variant": label,
                            **filter_metrics,
                        })

                        completed_runs += 1

                        print(
                            f"[{completed_runs}/{expected_runs}] "
                            f"{run_id} | {label} | "
                            f"allocated={allocated}/{submitted}"
                        )

    runs = pd.DataFrame(run_rows)
    allocations = pd.DataFrame(allocation_rows)
    filtering = pd.DataFrame(filter_rows)
    workloads = pd.DataFrame(workload_rows)

    # Validate completeness before writing final outputs.
    if len(runs) != expected_runs:
        raise RuntimeError(
            f"Expected {expected_runs} runs, got {len(runs)}."
        )

    if set(runs["implementation_policy_variant"].unique()) != set(POLICIES):
        raise RuntimeError("One or more policy variants are missing.")

    if runs.duplicated(
        ["experiment_id", "seed_id", "policy_variant"]
    ).any():
        raise RuntimeError(
            "Duplicate experiment/seed/policy combinations detected."
        )

    runs.to_csv(
        OUTPUT_DIR / "policy_run_metrics.csv",
        index=False,
    )

    allocations.to_csv(
        OUTPUT_DIR / "task_allocation_records.csv",
        index=False,
    )

    filtering.to_csv(
        OUTPUT_DIR / "filtering_summary_27.csv",
        index=False,
    )

    workloads.drop_duplicates(
        ["experiment_id", "seed_id", "task_id"]
    ).to_csv(
        OUTPUT_DIR / "task_workload_records.csv",
        index=False,
    )

    manifest = {
        "expected_runs": expected_runs,
        "completed_runs": len(runs),
        "networks": NETWORKS,
        "loads": list(LOADS),
        "profiles": [
            {
                "profile_id": p.profile_id,
                "name": p.name,
                "weights": list(p.weights),
            }
            for p in PRIORITY_PROFILES
        ],
        "seed_ids": list(REPLICATED_SEEDS),
        "policy_mapping": POLICY_LABELS,
        "ticks": TICKS,
        "warning": (
            "N2 and N3 topology sizes are provisional. "
            "Confirm them against the research design before reporting results."
        ),
    }

    (OUTPUT_DIR / "experiment_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(f"\nCompleted {len(runs)} simulation runs.")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("Next: python .\\analyze_27_experiments.py")

    return runs, allocations, filtering


if __name__ == "__main__":
    run_experiments()