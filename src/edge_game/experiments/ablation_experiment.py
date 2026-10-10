import pandas as pd

from config.experiment_config import (
    LOADS,
    OUTPUT_ROOT,
    PRIORITY_PROFILES,
    REPLICATED_SEEDS,
    TICKS,
)
from ..games.hierarchical_game import POLICY_VARIANTS
from ..simulation.environment import Network1Environment
from ..simulation.engine import SimulationEngine
from ..workload.generator import generate_tasks


def _append_records(path, rows, metadata):
    """Append one run's records without accumulating every run in memory."""
    if not rows:
        return

    frame = pd.DataFrame(rows)

    for key, value in metadata.items():
        if key in frame.columns:
            frame[key] = value
        else:
            frame.insert(0, key, value)

    frame.to_csv(
        path,
        mode="a",
        header=not path.exists(),
        index=False,
    )


def run_ablation_experiment():
    output_dir = OUTPUT_ROOT / "ablation"
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    run_path = raw_dir / "ablation_run_results.csv"
    task_path = raw_dir / "ablation_task_records.csv"
    filtering_path = raw_dir / "ablation_filtering_audit.csv"

    # Clear only this experiment's previous outputs.
    for path in (run_path, task_path, filtering_path):
        if path.exists():
            path.unlink()

    run_rows = []

    total_runs = (
        len(LOADS)
        * len(PRIORITY_PROFILES)
        * len(REPLICATED_SEEDS)
        * len(POLICY_VARIANTS)
    )
    completed_runs = 0

    for load in LOADS:
        for profile in PRIORITY_PROFILES:
            for seed_id in REPLICATED_SEEDS:
                # All methods share the same workload for this condition.
                seed = 20261007 + load + seed_id * 1009

                tasks = generate_tasks(
                    load,
                    profile.profile_id,
                    seed,
                    TICKS,
                )

                for variant in POLICY_VARIANTS:
                    # Start every method from a fresh, identically
                    # initialized environment.
                    environment = Network1Environment.create(seed)

                    engine = SimulationEngine(
                        environment,
                        policy_variant=variant,
                    )

                    metrics, records, filtering_records = engine.run(
                        tasks,
                        TICKS,
                    )

                    run_id = (
                        f"N1_{load}_{profile.profile_id}"
                        f"_seed{seed_id}_{variant}"
                    )

                    metadata = {
                        "run_id": run_id,
                        "network": "Network-1",
                        "load": load,
                        "profile_id": profile.profile_id,
                        "profile_name": profile.name,
                        "seed_id": seed_id,
                        "seed": seed,
                        "policy_variant": variant,
                        "priority_weights": str(profile.weights),
                    }

                    run_rows.append({**metadata, **metrics})

                    _append_records(
                        task_path,
                        records,
                        metadata,
                    )
                    _append_records(
                        filtering_path,
                        filtering_records,
                        metadata,
                    )

                    completed_runs += 1
                    print(
                        f"[{completed_runs}/{total_runs}] "
                        f"load={load}, profile={profile.profile_id}, "
                        f"seed_id={seed_id}, policy={variant}"
                    )

    runs = pd.DataFrame(run_rows)
    runs.to_csv(run_path, index=False)

    if len(runs) != total_runs:
        raise RuntimeError(
            f"Expected {total_runs} runs but recorded {len(runs)}."
        )

    if runs["run_id"].duplicated().any():
        raise RuntimeError("Duplicate run IDs detected.")

    print(f"\nAblation experiment completed: {len(runs)} runs")
    print(f"Raw results: {raw_dir}")

    from .ablation_analysis import run_ablation_analysis

    run_ablation_analysis(runs)

    return runs


if __name__ == "__main__":
    run_ablation_experiment()
