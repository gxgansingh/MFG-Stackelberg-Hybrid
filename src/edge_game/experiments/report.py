from pathlib import Path


def generate_report(runs, mean_sd, equilibrium, filtering, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtering_summary = filtering.groupby(["load", "profile_id"])["feasible"].mean().reset_index()
    lines = [
        "# Network-1 Experiment Report",
        "",
        "## Experimental Design",
        "",
        "- Network-1: 5 edge servers and 50 edge nodes",
        "- Loads: 1250, 2500, and 5000 tasks",
        "- Profiles: T1, T2, and T3",
        "- Horizon: 1250 ticks",
        "- Allocation order: filtering -> MFG/Nash -> Stackelberg -> final allocation",
        "",
        "## Priority Profiles",
        "",
        "| Profile | Description | Weights |",
        "|---|---|---|",
        "| T1 | Urgency-dominant | (0.50, 0.30, 0.20) |",
        "| T2 | Latency-dominant | (0.30, 0.50, 0.20) |",
        "| T3 | Service-dominant | (0.33, 0.33, 0.34) |",
        "",
        "## Run-Level Results",
        "",
        runs.to_string(index=False),
        "",
        "## Mean ± SD by Load",
        "",
        mean_sd.to_string(index=False),
        "",
        "## Equilibrium Diagnostics",
        "",
        equilibrium.to_string(index=False),
        "",
        "## Resource Filtering",
        "",
        filtering_summary.to_string(index=False),
        "",
        "## Statistical Interpretation",
        "",
        "Mean ± SD at a fixed load summarizes variation across the three priority profiles. "
        "It is not independent stochastic replication. Repeated-seed analysis should be added "
        "when repeatability or significance testing across stochastic runs is required.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
