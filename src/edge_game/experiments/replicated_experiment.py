
import pandas as pd

from config.experiment_config import (
    LOADS,
    OUTPUT_ROOT,
    PRIORITY_PROFILES,
    REPLICATED_SEEDS,
    TICKS,
)

from ..simulation.environment import Network1Environment
from ..simulation.engine import SimulationEngine
from ..workload.generator import generate_tasks


def run_replicated_experiment():
    output_dir = OUTPUT_ROOT / "replicated"
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    run_rows = []
    task_rows = []
    filtering_rows = []

    for load in LOADS:
        for profile in PRIORITY_PROFILES:
            for seed_id in REPLICATED_SEEDS:
                seed = (
                    20261007
                    + load
                    + seed_id * 1009
                    + sum(ord(char) for char in profile.profile_id)
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
                    ).run(tasks, TICKS)
                )

                run_id = (
                    f"N1_{load}_{profile.profile_id}"
                    f"_seed{seed_id}"
                )

                run_rows.append(
                    {
                        "run_id": run_id,
                        "network": "Network-1",
                        "load": load,
                        "profile_id": profile.profile_id,
                        "profile_name": profile.name,
                        "seed_id": seed_id,
                        "seed": seed,
                        "priority_weights": str(profile.weights),
                        **metrics,
                    }
                )

                for record in records:
                    task_rows.append(
                        {
                            "run_id": run_id,
                            "load": load,
                            "profile_id": profile.profile_id,
                            "seed_id": seed_id,
                            **record,
                        }
                    )

                for record in filtering_records:
                    filtering_rows.append(
                        {
                            "run_id": run_id,
                            "load": load,
                            "profile_id": profile.profile_id,
                            "seed_id": seed_id,
                            **record,
                        }
                    )

    runs = pd.DataFrame(run_rows)
    tasks = pd.DataFrame(task_rows)
    filtering = pd.DataFrame(filtering_rows)

    runs.to_csv(raw_dir / "replicated_run_results.csv", index=False)
    tasks.to_csv(raw_dir / "replicated_task_records.csv", index=False)
    filtering.to_csv(
        raw_dir / "replicated_filtering_audit.csv",
        index=False,
    )

    return runs, tasks, filtering


if __name__ == "__main__":
    runs, _, _ = run_replicated_experiment()
    print(f"Replicated experiment completed: {len(runs)} runs")
    print(f"Results: {OUTPUT_ROOT / 'replicated' / 'raw'}")
