import pandas as pd

from config.experiment_config import (
    LOADS,
    OUTPUT_ROOT,
    PRIORITY_PROFILES,
    TICKS,
)

from ..simulation.environment import Network1Environment
from ..simulation.engine import SimulationEngine
from ..workload.generator import generate_tasks


def run_network1():
    raw_dir = OUTPUT_ROOT / "raw"
    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_rows = []
    task_rows = []
    filter_rows = []

    for load in LOADS:
        for profile_index, profile in enumerate(
            PRIORITY_PROFILES
        ):
            seed = (
                20261007
                + load
                + profile_index * 101
            )

            tasks = generate_tasks(
                load,
                profile.profile_id,
                seed,
                TICKS,
            )

            metrics, records, filtering_records = (
                SimulationEngine(
                    Network1Environment.create(seed)
                ).run(
                    tasks,
                    TICKS,
                )
            )

            run_id = (
                f"N1_{load}_{profile.profile_id}"
            )

            for task in tasks:
                task_rows.append(
                    {
                        "run_id": run_id,
                        "load": load,
                        "profile_id": profile.profile_id,
                        "profile_name": profile.name,
                        "task_id": task.task_id,
                        "urgency": task.urgency,
                        "latency_sensitivity": (
                            task.latency_sensitivity
                        ),
                        "service_importance": (
                            task.service_importance
                        ),
                        "priority_score": (
                            task.priority_score
                        ),
                        "priority_class": (
                            task.priority_label
                        ),
                    }
                )

            for record in filtering_records:
                record.update(
                    {
                        "run_id": run_id,
                        "load": load,
                        "profile_id": profile.profile_id,
                    }
                )

                filter_rows.append(record)

            run_rows.append(
                {
                    "run_id": run_id,
                    "network": "Network-1",
                    "load": load,
                    "load_label": {
                        1250: "Small",
                        2500: "Medium",
                        5000: "Large",
                    }[load],
                    "profile_id": profile.profile_id,
                    "profile_name": profile.name,
                    "priority_weights": str(
                        profile.weights
                    ),
                    **metrics,
                }
            )

    frames = {
        "runs": pd.DataFrame(run_rows),
        "tasks": pd.DataFrame(task_rows),
        "filtering": pd.DataFrame(filter_rows),
    }

    frames["runs"].to_csv(
        raw_dir / "nine_run_results.csv",
        index=False,
    )

    frames["tasks"].to_csv(
        raw_dir / "task_priority_records.csv",
        index=False,
    )

    frames["filtering"].to_csv(
        raw_dir / "resource_filtering_audit.csv",
        index=False,
    )

    equilibrium_columns = [
        "run_id",
        "load",
        "profile_id",

        "nash_gap",
        "nash_deviation_margin",
        "nash_best_response_cost",
        "nash_selected_cost",
        "nash_best_alternative_cost",

        "stackelberg_gap",
        "stackelberg_margin",
        "stackelberg_deviation_margin",
        "stackelberg_leader_cost",
        "stackelberg_best_alternative_cost",
    ]

    frames["runs"][
        equilibrium_columns
    ].to_csv(
        raw_dir / "equilibrium_results.csv",
        index=False,
    )

    return frames