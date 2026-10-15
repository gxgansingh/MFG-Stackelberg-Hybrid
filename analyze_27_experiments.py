from pathlib import Path
import sys

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_ROOT / "outputs" / "experiments_27"
OUTPUT_DIR = INPUT_DIR / "analysis"

INPUT_FILE = INPUT_DIR / "policy_run_metrics.csv"

POLICY_NAME_MAP = {
    "A1_MFG_ONLY": "MFG",
    "A2_STACKELBERG_ONLY": "Stackelberg",
    "A3_MFG_STACKELBERG": "NonPriorityHybrid",
    "PROPOSED": "Proposed",
}

EXPECTED_POLICIES = [
    "MFG",
    "Stackelberg",
    "NonPriorityHybrid",
    "Proposed",
]


# ============================================================
# HELPERS
# ============================================================

def print_section(title):
    print("\n" + "=" * 75)
    print(title)
    print("=" * 75)


def find_column(df, candidates, required=True):
    """Find a column using a list of possible names."""
    for column in candidates:
        if column in df.columns:
            return column

    if required:
        raise ValueError(
            f"Could not find any of these columns: {candidates}\n"
            f"Available columns: {list(df.columns)}"
        )

    return None


def save_csv(df, filename):
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved: {path}")


def normalize_policy_names(df):
    """Normalize internal policy IDs and friendly policy labels."""
    column = find_column(
        df,
        ["policy_variant", "policy", "policy_name"],
    )

    df[column] = (
        df[column]
        .astype(str)
        .str.strip()
        .replace(POLICY_NAME_MAP)
    )

    if column != "policy_variant":
        df["policy_variant"] = df[column]

    return df


def to_numeric_if_present(df, columns):
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")


# ============================================================
# LOAD AND VALIDATE DATA
# ============================================================

def load_data():
    print_section("LOADING EXPERIMENT RESULTS")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}\n\n"
            "Make sure the experiment runner has generated "
            "outputs/experiments_27/policy_run_metrics.csv."
        )

    df = pd.read_csv(INPUT_FILE)

    if df.empty:
        raise ValueError(f"The input CSV is empty: {INPUT_FILE}")

    print(f"Input file: {INPUT_FILE}")
    print(f"Rows loaded: {len(df)}")
    print(f"Columns found: {len(df.columns)}")

    df = normalize_policy_names(df)

    # Check that all four policies are represented.
    actual_policies = sorted(df["policy_variant"].dropna().unique())
    expected_policies = sorted(EXPECTED_POLICIES)

    print(f"Policies found: {actual_policies}")

    unexpected = sorted(set(actual_policies) - set(expected_policies))
    missing = sorted(set(expected_policies) - set(actual_policies))

    if unexpected:
        raise ValueError(
            f"Unexpected policy names: {unexpected}\n"
            f"Expected policy names: {EXPECTED_POLICIES}"
        )

    if missing:
        raise ValueError(
            f"Missing policies: {missing}\n"
            f"Expected all four policies: {EXPECTED_POLICIES}"
        )

    # Convert numeric fields where present.
    to_numeric_if_present(
        df,
        [
            "load",
            "server_count",
            "nodes_per_server",
            "total_nodes",
            "seed",
            "seed_id",
            "submitted_tasks",
            "allocated_tasks",
            "rejected_tasks",
            "allocation_success_ratio",
            "utility_mean",
            "response_time_mean",
            "throughput",
            "jain_fairness",
            "jains_fairness_index",
            "load_variance",
            "allocation_time_seconds",
            "decision_time_seconds",
            "mfg_convergence_time_seconds",
            "nash_gap",
            "stackelberg_gap",
        ],
    )

    return df


# ============================================================
# EXPERIMENT STRUCTURE VALIDATION
# ============================================================

def validate_experiments(df):
    print_section("EXPERIMENT STRUCTURE VALIDATION")

    required_columns = [
        "network_id",
        "load",
        "profile_id",
        "policy_variant",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}\n"
            f"Available columns: {list(df.columns)}"
        )

    print(f"Total result rows: {len(df)}")

    for column in [
        "network_id",
        "load",
        "profile_id",
        "policy_variant",
    ]:
        print(f"Unique {column}: {df[column].nunique()}")

    if "seed_id" in df.columns:
        seed_column = "seed_id"
    elif "seed" in df.columns:
        seed_column = "seed"
    else:
        seed_column = None

    if seed_column:
        print(f"Unique seeds: {df[seed_column].nunique()}")

    config_columns = [
        "network_id",
        "load",
        "profile_id",
    ]

    if seed_column:
        config_columns.append(seed_column)

    config_columns.append("policy_variant")

    duplicates = df.duplicated(subset=config_columns, keep=False)

    if duplicates.any():
        duplicate_rows = df.loc[duplicates, config_columns]
        save_csv(duplicate_rows, "duplicate_run_rows.csv")

        print(
            f"WARNING: Found {duplicates.sum()} rows participating "
            "in duplicate experiment configurations."
        )
        print("See analysis/duplicate_run_rows.csv.")
    else:
        print("No duplicate configuration/seed/policy rows detected.")

    expected_networks = 3
    expected_loads = 3
    expected_profiles = 3
    expected_seeds = 5
    expected_policies = 4

    expected_runs = (
        expected_networks
        * expected_loads
        * expected_profiles
        * expected_seeds
        * expected_policies
    )

    print(f"\nExpected runs for the planned design: {expected_runs}")
    print(f"Rows currently available: {len(df)}")

    if len(df) != expected_runs:
        print(
            "WARNING: The row count does not equal 540. "
            "The dataset may be incomplete, may contain extra rows, "
            "or may use a different experimental design."
        )
    else:
        print("Row count matches the planned 540-run design.")

    return df


# ============================================================
# POLICY PERFORMANCE SUMMARY
# ============================================================

def summarize_policies(df):
    print_section("POLICY PERFORMANCE SUMMARY")

    metrics = [
        "utility_mean",
        "response_time_mean",
        "throughput",
        "jain_fairness",
        "jains_fairness_index",
        "load_variance",
        "allocation_time_seconds",
        "decision_time_seconds",
        "mfg_convergence_time_seconds",
        "nash_gap",
        "stackelberg_gap",
        "allocation_success_ratio",
        "rejected_tasks",
    ]

    available_metrics = [
        metric for metric in metrics
        if metric in df.columns
        and pd.api.types.is_numeric_dtype(df[metric])
    ]

    if not available_metrics:
        print("No recognized numeric performance metrics were found.")
        return None

    summary = (
        df.groupby("policy_variant")[available_metrics]
        .agg(["mean", "std", "min", "max", "count"])
        .round(6)
    )

    print(summary.to_string())

    # Flatten multi-level column names for CSV output.
    summary.columns = [
        f"{metric}_{statistic}"
        for metric, statistic in summary.columns
    ]

    summary = summary.reset_index()
    save_csv(summary, "policy_performance_summary.csv")

    return summary


# ============================================================
# NETWORK-WISE PERFORMANCE
# ============================================================

def summarize_by_network(df):
    print_section("NETWORK-WISE POLICY PERFORMANCE")

    metric_candidates = [
        "utility_mean",
        "response_time_mean",
        "throughput",
        "jain_fairness",
        "jains_fairness_index",
        "load_variance",
        "allocation_time_seconds",
        "decision_time_seconds",
        "allocation_success_ratio",
        "rejected_tasks",
    ]

    metrics = [
        metric for metric in metric_candidates
        if metric in df.columns
        and pd.api.types.is_numeric_dtype(df[metric])
    ]

    if not metrics:
        print("No recognized metrics available for network comparison.")
        return None

    grouping = ["network_id", "policy_variant"]

    if "server_count" in df.columns:
        grouping.insert(1, "server_count")

    if "total_nodes" in df.columns:
        grouping.insert(2, "total_nodes")

    result = (
        df.groupby(grouping, dropna=False)[metrics]
        .mean()
        .reset_index()
        .round(6)
    )

    print(result.to_string(index=False))
    save_csv(result, "network_policy_summary.csv")

    return result


# ============================================================
# LOAD-WISE PERFORMANCE
# ============================================================

def summarize_by_load(df):
    print_section("LOAD-WISE POLICY PERFORMANCE")

    metric_candidates = [
        "utility_mean",
        "response_time_mean",
        "throughput",
        "jain_fairness",
        "jains_fairness_index",
        "load_variance",
        "allocation_success_ratio",
        "rejected_tasks",
    ]

    metrics = [
        metric for metric in metric_candidates
        if metric in df.columns
        and pd.api.types.is_numeric_dtype(df[metric])
    ]

    if not metrics:
        print("No recognized metrics available for load comparison.")
        return None

    result = (
        df.groupby(["load", "policy_variant"], dropna=False)[metrics]
        .mean()
        .reset_index()
        .round(6)
    )

    print(result.to_string(index=False))
    save_csv(result, "load_policy_summary.csv")

    return result


# ============================================================
# PRIORITY PROFILE PERFORMANCE
# ============================================================

def summarize_by_profile(df):
    print_section("PRIORITY PROFILE PERFORMANCE")

    metric_candidates = [
        "utility_mean",
        "response_time_mean",
        "throughput",
        "jain_fairness",
        "jains_fairness_index",
        "allocation_success_ratio",
        "rejected_tasks",
    ]

    metrics = [
        metric for metric in metric_candidates
        if metric in df.columns
        and pd.api.types.is_numeric_dtype(df[metric])
    ]

    if not metrics:
        print("No recognized metrics available for profile comparison.")
        return None

    grouping = ["profile_id", "policy_variant"]

    if "profile_name" in df.columns:
        grouping.insert(1, "profile_name")

    result = (
        df.groupby(grouping, dropna=False)[metrics]
        .mean()
        .reset_index()
        .round(6)
    )

    print(result.to_string(index=False))
    save_csv(result, "profile_policy_summary.csv")

    return result


# ============================================================
# TASK ACCOUNTING
# ============================================================

def analyze_task_accounting(df):
    print_section("TASK ACCOUNTING AND SUCCESS RATES")

    needed = [
        "submitted_tasks",
        "allocated_tasks",
        "rejected_tasks",
    ]

    available = [column for column in needed if column in df.columns]

    if len(available) < 2:
        print(
            "Task accounting columns are incomplete. "
            "Cannot reliably summarize submitted, allocated, and rejected tasks."
        )
        return None

    grouping = ["policy_variant"]

    if "network_id" in df.columns:
        grouping.insert(0, "network_id")

    result = (
        df.groupby(grouping, dropna=False)[available]
        .agg(["mean", "min", "max"])
    )

    result.columns = [
        f"{metric}_{statistic}"
        for metric, statistic in result.columns
    ]

    result = result.reset_index()

    print(result.to_string(index=False))
    save_csv(result, "task_accounting_summary.csv")

    # Recalculate success ratio from counts when possible.
    if {
        "submitted_tasks",
        "allocated_tasks",
    }.issubset(df.columns):
        df["calculated_success_ratio"] = (
            df["allocated_tasks"]
            / df["submitted_tasks"].replace(0, pd.NA)
        )

        success_summary = (
            df.groupby("policy_variant")["calculated_success_ratio"]
            .agg(["mean", "std", "min", "max", "count"])
            .reset_index()
            .round(6)
        )

        print("\nCalculated allocation success ratio:")
        print(success_summary.to_string(index=False))
        save_csv(success_summary, "calculated_success_ratio_summary.csv")

    return result


# ============================================================
# POLICY RANKING
# ============================================================

def create_rankings(df):
    print_section("POLICY RANKINGS")

    # Higher is better for these metrics.
    higher_is_better = [
        "utility_mean",
        "throughput",
        "jain_fairness",
        "jains_fairness_index",
        "allocation_success_ratio",
    ]

    # Lower is better for these metrics.
    lower_is_better = [
        "response_time_mean",
        "load_variance",
        "allocation_time_seconds",
        "decision_time_seconds",
        "mfg_convergence_time_seconds",
        "rejected_tasks",
    ]

    selected_metrics = [
        metric for metric in higher_is_better + lower_is_better
        if metric in df.columns
        and pd.api.types.is_numeric_dtype(df[metric])
    ]

    if not selected_metrics:
        print("No recognized metrics available for ranking.")
        return None

    # Aggregate run-level values first.
    averages = (
        df.groupby("policy_variant")[selected_metrics]
        .mean()
        .reset_index()
    )

    for metric in higher_is_better:
        if metric in averages.columns:
            averages[f"{metric}_rank"] = averages[metric].rank(
                ascending=False,
                method="min",
            )

    for metric in lower_is_better:
        if metric in averages.columns:
            averages[f"{metric}_rank"] = averages[metric].rank(
                ascending=True,
                method="min",
            )

    rank_columns = [
        column for column in averages.columns
        if column.endswith("_rank")
    ]

    if rank_columns:
        averages["average_rank"] = averages[rank_columns].mean(axis=1)
        averages = averages.sort_values("average_rank")

    averages = averages.round(6)

    print(
        "Rankings are descriptive averages across runs. "
        "They are not statistical significance tests."
    )
    print(averages.to_string(index=False))

    save_csv(averages, "policy_rankings.csv")

    return averages


# ============================================================
# MAIN
# ============================================================

def run_analysis():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    df = validate_experiments(df)

    # Save a normalized copy without overwriting the original data.
    normalized_path = OUTPUT_DIR / "normalized_policy_run_metrics.csv"
    df.to_csv(normalized_path, index=False)
    print(f"\nSaved normalized data: {normalized_path}")

    summarize_policies(df)
    summarize_by_network(df)
    summarize_by_load(df)
    summarize_by_profile(df)
    analyze_task_accounting(df)
    create_rankings(df)

    print_section("ANALYSIS COMPLETE")
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_DIR}")
    print("Original experiment CSV was not modified.")


if __name__ == "__main__":
    try:
        run_analysis()
    except Exception as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        sys.exit(1)
