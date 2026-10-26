"""
Phase-2 ablation and statistical analysis module.
Runs replicated multi-seed experiments across A1 (MFG only), A2 (Stackelberg only),
A3 (non-priority MFG + Stackelberg), and Proposed (priority-aware MFG + Stackelberg),
and builds Phase-2 Table-1, Table-2, and Table-3.
"""

from typing import Dict, List, Tuple
import pandas as pd
from scipy import stats

from config.experiment_config import (
    ABLATION_METHODS,
    DEFAULT_RANDOM_SEED,
    NETWORKS,
    PHASE2_NUM_RUNS,
    TASK_PROFILES,
    WORKLOAD_LEVELS,
)
from src.edge_game.simulation.engine import SimulationEngine


METRICS_SPEC: List[Tuple[str, str, str]] = [
    ("utility", "Utility", "Mean Utility"),
    ("fairness", "Jain's Fairness", "Mean Fairness"),
    ("load_variance", "Load Variance", "Mean Load Variance"),
    ("convergence_time", "Convergence Time", "Mean Convergence Time (ms)"),
    ("throughput", "Throughput", "Mean Throughput (tasks/s)"),
    ("response_time", "Response Time", "Mean Response Time (ms)"),
]


def run_phase2_replicated_suite(
    workloads: List[int] = WORKLOAD_LEVELS,
    num_runs: int = PHASE2_NUM_RUNS,
    base_seed: int = DEFAULT_RANDOM_SEED,
) -> pd.DataFrame:
    """
    Execute Phase-2 replicated simulations across:
      - 3 Networks (N1, N2, N3)
      - Specified workloads (default: 1,250, 3,000, 5,000)
      - 4 Ablation methods (A1, A2, A3, Proposed)
      - `num_runs` (default: 9) runs cycling across priority task profiles (T1, T2, T3)
    """
    records: List[Dict[str, float | int | str]] = []
    run_counter = 0

    for net_code in ["N1", "N2", "N3"]:
        engine = SimulationEngine(NETWORKS[net_code])
        for w_size in workloads:
            for run_idx in range(num_runs):
                profile = TASK_PROFILES[run_idx % len(TASK_PROFILES)]
                # Share the same environmental seed across all 4 methods within a replication
                env_seed = base_seed + run_counter * 31
                run_counter += 1

                for method in ABLATION_METHODS:
                    trial = engine.run_trial(
                        workload_size=w_size,
                        task_profile=profile,
                        method=method,
                        seed=env_seed,
                    )
                    records.append(trial.to_flat_record(run_id=run_idx + 1))

    return pd.DataFrame(records)


def build_phase2_table1_mean_sd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build Phase-2 Table-1: Mean +/- SD comparison for the six metrics across
    (1) A1 MFG, (2) A2 Stackelberg, (3) A3 MFG+Stackelberg, and (4) Proposed.
    """
    rows = []
    for col_key, metric_label, _ in METRICS_SPEC:
        row: Dict[str, str] = {"Metric": metric_label}
        for method in ABLATION_METHODS:
            series = df.loc[df["method"] == method, col_key].dropna().astype(float)
            mean_val = series.mean()
            sd_val = series.std(ddof=1)
            if col_key == "fairness":
                row[method] = f"{mean_val:.4f} ± {sd_val:.4f}"
            else:
                row[method] = f"{mean_val:.2f} ± {sd_val:.2f}"
        rows.append(row)

    return pd.DataFrame(rows)


def _format_p_value(p_val: float) -> str:
    """Format a statistical p-value with standard significance stars."""
    if p_val < 0.0001:
        return f"{p_val:.2e} (<0.0001***)"
    if p_val < 0.001:
        return f"{p_val:.4f}***"
    if p_val < 0.01:
        return f"{p_val:.4f}**"
    if p_val < 0.05:
        return f"{p_val:.4f}*"
    return f"{p_val:.4f} (ns)"


def build_phase2_table2_significance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build Phase-2 Table-2: Statistical significance (two-sample Welch t-test
    and one-way ANOVA p-values) comparing:
      (1) Proposed vs A1 (MFG only)
      (2) Proposed vs A2 (Stackelberg only)
      (3) Proposed vs A3 (non-priority MFG + Stackelberg)
    """
    comparisons = [
        ("Proposed vs A1", "A1: MFG only"),
        ("Proposed vs A2", "A2: Stackelberg only"),
        ("Proposed vs A3", "A3: MFG+Stackelberg"),
    ]
    rows = []

    for col_key, metric_label, _ in METRICS_SPEC:
        prop_vals = df.loc[df["method"] == "Proposed", col_key].dropna().astype(float)
        row: Dict[str, str] = {"Metric": metric_label}

        for col_title, baseline_method in comparisons:
            base_vals = df.loc[df["method"] == baseline_method, col_key].dropna().astype(float)
            _, p_val = stats.ttest_ind(prop_vals, base_vals, equal_var=False)
            row[col_title] = _format_p_value(float(p_val))

        all_groups = [
            df.loc[df["method"] == m, col_key].dropna().astype(float).values
            for m in ABLATION_METHODS
        ]
        _, anova_p = stats.f_oneway(*all_groups)
        row["ANOVA (4-Method)"] = _format_p_value(float(anova_p))
        rows.append(row)

    return pd.DataFrame(rows)


def build_equilibrium_ablation_checklist() -> pd.DataFrame:
    """
    Build the Nash and Stackelberg Equilibrium Ablation applicability table
    distinguishing which equilibrium measure applies to each method.
    """
    return pd.DataFrame(
        [
            {
                "Method": "A1: MFG only",
                "MFG": "✓",
                "Stackelberg": "✗",
                "Appropriate equilibrium": "Nash / ε-Nash",
            },
            {
                "Method": "A2: Stackelberg only",
                "MFG": "✗",
                "Stackelberg": "✓",
                "Appropriate equilibrium": "Stackelberg equilibrium",
            },
            {
                "Method": "A3: MFG + Stackelberg",
                "MFG": "✓",
                "Stackelberg": "✓",
                "Appropriate equilibrium": "Nash + Stackelberg",
            },
            {
                "Method": "Proposed Priority MFG + Stackelberg",
                "MFG": "✓",
                "Stackelberg": "✓",
                "Appropriate equilibrium": "Nash + Stackelberg",
            },
        ]
    )


def build_phase2_table3_equilibrium_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build Phase-2 Table-3: Mean +/- SD for Final Nash Gap and Stackelberg Gap.
    Distinguishes the two equilibrium measures so that A1 is validated via Nash Gap
    and A2 is validated via Stackelberg Gap, while A3 and Proposed report both.
    """
    gap_rows = [
        ("nash_gap", "Final Nash Gap ↓"),
        ("stackelberg_gap", "Stackelberg Gap ↓"),
    ]
    rows = []

    for col_key, label in gap_rows:
        row: Dict[str, str] = {"Equilibrium metric": label}
        for method in ABLATION_METHODS:
            series = df.loc[df["method"] == method, col_key].dropna().astype(float)
            if series.empty:
                row[method] = "N/A"
            else:
                row[method] = f"{series.mean():.5f} ± {series.std(ddof=1):.5f}"
        rows.append(row)

    return pd.DataFrame(rows)