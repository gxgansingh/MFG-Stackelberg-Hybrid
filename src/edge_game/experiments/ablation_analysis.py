import numpy as np
import pandas as pd
from scipy import stats

from config.experiment_config import OUTPUT_ROOT


METRICS = (
    "utility_mean",
    "jain_fairness",
    "load_variance",
    "allocation_time_seconds",
    "throughput",
    "response_time_mean",
)

BASELINES = (
    "A1_MFG_ONLY",
    "A2_STACKELBERG_ONLY",
    "A3_MFG_STACKELBERG",
)

PAIR_KEYS = ["load", "profile_id", "seed_id"]


def _mean_sd(values):
    values = pd.to_numeric(values, errors="coerce").dropna()

    if len(values) == 0:
        return float("nan"), float("nan")

    mean = float(values.mean())
    sd = float(values.std(ddof=1)) if len(values) > 1 else float("nan")
    return mean, sd


def _holm_adjust(p_values):
    """Apply Holm's step-down correction to a family of p-values."""
    values = np.asarray(p_values, dtype=float)
    adjusted = np.full(len(values), np.nan)

    valid_indices = [
        index
        for index, value in enumerate(values)
        if np.isfinite(value)
    ]

    ordered = sorted(valid_indices, key=lambda index: values[index])
    running_max = 0.0
    total = len(ordered)

    for rank, index in enumerate(ordered):
        candidate = min(1.0, (total - rank) * values[index])
        running_max = max(running_max, candidate)
        adjusted[index] = running_max

    return adjusted.tolist()


def build_ablation_summary(runs):
    required = {
        "policy_variant",
        "load",
        "profile_id",
        "seed_id",
        *METRICS,
    }
    missing = sorted(required.difference(runs.columns))

    if missing:
        raise ValueError(
            f"Ablation results are missing required columns: {missing}"
        )

    duplicate_keys = [
        "load",
        "profile_id",
        "seed_id",
        "policy_variant",
    ]

    if runs.duplicated(duplicate_keys).any():
        raise ValueError(
            "Duplicate load/profile/seed/policy combinations detected."
        )

    rows = []

    for (load, profile_id, variant), group in runs.groupby(
        ["load", "profile_id", "policy_variant"],
        sort=True,
    ):
        row = {
            "load": load,
            "profile_id": profile_id,
            "policy_variant": variant,
            "replication_count": int(group["seed_id"].nunique()),
        }

        for metric in METRICS:
            mean, sd = _mean_sd(group[metric])
            row[f"{metric}_mean"] = mean
            row[f"{metric}_sd"] = sd

        rows.append(row)

    return pd.DataFrame(rows)


def build_paired_comparisons(runs):
    rows = []

    for baseline in BASELINES:
        for metric in METRICS:
            subset = runs[
                runs["policy_variant"].isin([baseline, "PROPOSED"])
            ]

            paired = subset.pivot(
                index=PAIR_KEYS,
                columns="policy_variant",
                values=metric,
            )

            if baseline not in paired.columns or "PROPOSED" not in paired.columns:
                continue

            paired = paired[[baseline, "PROPOSED"]].dropna()

            differences = (
                paired["PROPOSED"] - paired[baseline]
            ).to_numpy(dtype=float)

            n = len(differences)
            mean_difference = (
                float(np.mean(differences)) if n else float("nan")
            )
            sd_difference = (
                float(np.std(differences, ddof=1))
                if n > 1
                else float("nan")
            )

            if n >= 2 and sd_difference > 0:
                standard_error = sd_difference / np.sqrt(n)
                t_statistic = mean_difference / standard_error

                p_value = float(
                    2.0 * stats.t.sf(abs(t_statistic), df=n - 1)
                )

                critical = float(stats.t.ppf(0.975, df=n - 1))
                ci_low = mean_difference - critical * standard_error
                ci_high = mean_difference + critical * standard_error
                effect_size_dz = mean_difference / sd_difference

            elif n >= 2 and mean_difference == 0:
                t_statistic = 0.0
                p_value = 1.0
                ci_low = 0.0
                ci_high = 0.0
                effect_size_dz = 0.0

            elif n >= 2:
                # All paired differences are identical and nonzero.
                t_statistic = float("inf")
                p_value = 0.0
                ci_low = mean_difference
                ci_high = mean_difference
                effect_size_dz = float("inf")

            else:
                t_statistic = float("nan")
                p_value = float("nan")
                ci_low = float("nan")
                ci_high = float("nan")
                effect_size_dz = float("nan")

            rows.append(
                {
                    "metric": metric,
                    "comparison": f"PROPOSED_vs_{baseline}",
                    "baseline": baseline,
                    "paired_conditions": n,
                    "proposed_mean": (
                        float(paired["PROPOSED"].mean())
                        if n
                        else float("nan")
                    ),
                    "baseline_mean": (
                        float(paired[baseline].mean())
                        if n
                        else float("nan")
                    ),
                    "mean_difference_proposed_minus_baseline": (
                        mean_difference
                    ),
                    "difference_sd": sd_difference,
                    "t_statistic": t_statistic,
                    "p_value": p_value,
                    "ci_95_low": ci_low,
                    "ci_95_high": ci_high,
                    "cohens_dz": effect_size_dz,
                }
            )

    result = pd.DataFrame(rows)

    if not result.empty:
        result["p_value_holm"] = _holm_adjust(
            result["p_value"].tolist()
        )
        result["significant_holm_0_05"] = (
            result["p_value_holm"] < 0.05
        )

    return result


def build_equilibrium_summary(runs):
    columns = [
        "nash_gap",
        "nash_deviation_margin",
        "stackelberg_gap",
        "stackelberg_margin",
        "stackelberg_deviation_margin",
    ]

    available = [column for column in columns if column in runs.columns]
    rows = []

    for (load, variant), group in runs.groupby(
        ["load", "policy_variant"],
        sort=True,
    ):
        row = {
            "load": load,
            "policy_variant": variant,
            "run_count": len(group),
        }

        for metric in available:
            mean, sd = _mean_sd(group[metric])
            row[f"{metric}_mean"] = mean
            row[f"{metric}_sd"] = sd
            row[f"{metric}_n"] = int(
                pd.to_numeric(
                    group[metric],
                    errors="coerce",
                ).notna().sum()
            )

        rows.append(row)

    return pd.DataFrame(rows)


def _markdown_table(frame, columns):
    selected = frame[columns]

    if selected.empty:
        return "_No rows available._"

    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]

    for _, row in selected.iterrows():
        values = []

        for value in row:
            if pd.isna(value):
                values.append("N/A")
            elif isinstance(value, (float, np.floating)):
                values.append(f"{value:.5f}")
            else:
                values.append(str(value))

        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def generate_ablation_report(
    runs,
    summary,
    paired,
    equilibrium,
    report_path,
):
    overall_rows = []

    for variant, group in runs.groupby("policy_variant", sort=False):
        row = {"policy_variant": variant}

        for metric in METRICS:
            mean, sd = _mean_sd(group[metric])
            row[f"{metric}_mean"] = mean
            row[f"{metric}_sd"] = sd

        overall_rows.append(row)

    overall = pd.DataFrame(overall_rows)

    summary_display = summary[
        [
            "load",
            "profile_id",
            "policy_variant",
            "replication_count",
        ]
    ].copy()

    for metric in METRICS:
        summary_display[metric] = summary.apply(
            lambda row: (
                f"{row[f'{metric}_mean']:.5f} ± "
                f"{row[f'{metric}_sd']:.5f}"
                if pd.notna(row[f"{metric}_sd"])
                else f"{row[f'{metric}_mean']:.5f} ± N/A"
            ),
            axis=1,
        )

    overall_columns = ["policy_variant"] + [
        column
        for metric in METRICS
        for column in (f"{metric}_mean", f"{metric}_sd")
    ]

    paired_columns = [
        "metric",
        "comparison",
        "paired_conditions",
        "mean_difference_proposed_minus_baseline",
        "ci_95_low",
        "ci_95_high",
        "p_value",
        "p_value_holm",
        "significant_holm_0_05",
    ]

    equilibrium_columns = list(equilibrium.columns)

    report = f"""# Network-1 Ablation Study

## Experimental design

- Allocation methods: A1 MFG only, A2 Stackelberg only,
  A3 MFG + Stackelberg, and Proposed priority-aware MFG + Stackelberg.
- Load levels: {", ".join(map(str, sorted(runs["load"].unique())))}.
- Priority profiles: {", ".join(sorted(runs["profile_id"].unique()))}.
- Replication labels: {", ".join(map(str, sorted(runs["seed_id"].unique())))}.
- Total runs: {len(runs)}.
- Matched conditions: load, priority profile, and replication seed.
- Each method uses the same generated workload and a fresh environment
  initialized with the same seed within each matched condition.
- Resource feasibility filtering is shared across all methods.

## Overall results

Values are means and sample standard deviations across the experiment runs.
These overall figures are descriptive and combine different loads and profiles.

{_markdown_table(overall, overall_columns)}

## Results by load and priority profile

Values are mean ± sample standard deviation across replications.

{_markdown_table(summary_display, [
    "load",
    "profile_id",
    "policy_variant",
    "replication_count",
    *METRICS,
])}

## Paired statistical comparisons

Each comparison uses paired observations for the same load/profile/seed
conditions. The reported difference is Proposed minus the named baseline.
Positive differences are not universally better: interpretation depends on
the metric.

Two-sided paired t-tests are used, with Holm correction across the family
of 18 tests (six metrics and three baselines). Confidence intervals are
95% intervals for the mean paired difference.

{_markdown_table(paired, paired_columns)}

## Equilibrium diagnostics

{_markdown_table(equilibrium, equilibrium_columns)}

A2 does not use an MFG follower, and A1 does not use a Stackelberg leader.
Their corresponding equilibrium metrics are not applicable. The gap and
margin values from the current game implementations are candidate-ranking
diagnostics; zero gaps alone do not establish a full Nash or Stackelberg
equilibrium.

## Interpretation cautions

- Overall means combine multiple load levels and priority profiles and are
  descriptive, not a substitute for condition-specific results.
- A statistically significant difference does not by itself establish
  practical importance or universal superiority.
- Paired tests assume the matched differences are sufficiently well behaved
  for a t-test. The 45 matched conditions include repeated profiles and loads,
  so the pooled test should be interpreted alongside condition-level results.
- Jain fairness measures fairness of task allocation counts across nodes,
  not fairness of completed work, resource consumption, or task outcomes.
- Throughput is completed tasks divided by the configured duration in ticks.
- Allocation computation time is measured around the complete policy decision.
  It is not the same as MFG convergence time.

"""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")


def run_ablation_analysis(runs=None):
    output_dir = OUTPUT_ROOT / "ablation"
    raw_dir = output_dir / "raw"
    statistics_dir = output_dir / "statistics"
    report_dir = output_dir / "report"

    statistics_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    if runs is None:
        runs = pd.read_csv(
            raw_dir / "ablation_run_results.csv"
        )

    summary = build_ablation_summary(runs)
    paired = build_paired_comparisons(runs)
    equilibrium = build_equilibrium_summary(runs)

    summary.to_csv(
        statistics_dir / "ablation_mean_sd.csv",
        index=False,
    )
    paired.to_csv(
        statistics_dir / "paired_comparisons.csv",
        index=False,
    )
    equilibrium.to_csv(
        statistics_dir / "equilibrium_comparison.csv",
        index=False,
    )

    generate_ablation_report(
        runs,
        summary,
        paired,
        equilibrium,
        report_dir / "ablation_results.md",
    )

    print(f"Summary statistics: {statistics_dir}")
    print(f"Report: {report_dir / 'ablation_results.md'}")

    if not paired.empty:
        print("\nPaired comparisons (Proposed minus baseline):")
        print(
            paired[
                [
                    "metric",
                    "comparison",
                    "paired_conditions",
                    "mean_difference_proposed_minus_baseline",
                    "p_value",
                    "p_value_holm",
                    "significant_holm_0_05",
                ]
            ].to_string(index=False)
        )

    return {
        "summary": summary,
        "paired_comparisons": paired,
        "equilibrium": equilibrium,
    }
