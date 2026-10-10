from pathlib import Path
import matplotlib.pyplot as plt

from .statistical_analysis import METRICS


LABELS = {
    "utility_mean": "Utility Mean",
    "jain_fairness": "Jain Fairness Index",
    "load_variance": "Load Variance",
    "convergence_time_seconds": "Convergence Time (s)",
    "throughput": "Throughput",
    "response_time_mean": "Response Time Mean (ms)",
}


def generate_figures(runs, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    for metric in METRICS:
        fig, ax = plt.subplots(figsize=(8, 5))
        for profile_id, group in runs.groupby("profile_id"):
            group = group.sort_values("load")
            ax.plot(group["load"], group[metric], marker="o", label=profile_id)
        ax.set_xlabel("Task Load")
        ax.set_ylabel(LABELS[metric])
        ax.set_title(f"{LABELS[metric]} vs Load")
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(output_dir / f"{metric}_vs_load.png", dpi=180)
        plt.close(fig)


def generate_filtering_figure(filtering, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = filtering.groupby(["load", "profile_id"])["feasible"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    for profile_id, group in summary.groupby("profile_id"):
        group = group.sort_values("load")
        ax.plot(group["load"], group["feasible"], marker="o", label=profile_id)
    ax.set_xlabel("Task Load")
    ax.set_ylabel("Feasibility Ratio")
    ax.set_title("Resource Filtering Feasibility Ratio")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "resource_filtering_audit.png", dpi=180)
    plt.close(fig)
