
from pathlib import Path

import numpy as np
import pandas as pd

METRICS = [
    "utility_mean",
    "jain_fairness",
    "load_variance",
    "convergence_time_seconds",
    "throughput",
    "response_time_mean",
]


def mean_sd_by_load(runs):
    rows = []

    for load, group in runs.groupby("load"):
        row = {"load": load}

        for metric in METRICS:
            values = group[metric].to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_sd"] = (
                float(np.std(values, ddof=1))
                if len(values) > 1 else 0.0
            )

        rows.append(row)

    return pd.DataFrame(rows)


def priority_profile_statistics(runs):
    columns = ["load", "profile_id", "profile_name", *METRICS]
    return runs[columns].copy()


def equilibrium_statistics(runs):
    rows = []

    for load, group in runs.groupby("load"):
        row = {"load": load}

        for metric in [
            "nash_gap",
            "nash_deviation_margin",
            "stackelberg_gap",
            "stackelberg_deviation_margin",
            "stackelberg_margin",
        ]:
            if metric not in group.columns:
                continue

            values = group[metric].to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_sd"] = (
                float(np.std(values, ddof=1))
                if len(values) > 1 else 0.0
            )

        rows.append(row)

    return pd.DataFrame(rows)


def replicated_statistics(runs):
    """Summarize independent seeds within each load/profile combination."""
    rows = []

    for (load, profile_id), group in runs.groupby(
        ["load", "profile_id"],
        sort=True,
    ):
        row = {
            "load": load,
            "profile_id": profile_id,
            "profile_name": group["profile_name"].iloc[0],
            "replication_count": int(group["seed_id"].nunique()),
        }

        for metric in METRICS:
            values = group[metric].to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_sd"] = (
                float(np.std(values, ddof=1))
                if len(values) > 1 else 0.0
            )

        rows.append(row)

    return pd.DataFrame(rows)


def run_statistics(runs, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    tables = {
        "mean_sd_by_load": mean_sd_by_load(runs),
        "priority_profile_statistics": priority_profile_statistics(runs),
        "equilibrium_statistics": equilibrium_statistics(runs),
    }

    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)

    return tables


def run_replicated_statistics(runs, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = replicated_statistics(runs)
    summary.to_csv(
        output_dir / "replicated_mean_sd_by_profile.csv",
        index=False,
    )

    return summary
