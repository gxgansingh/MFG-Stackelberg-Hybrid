"""
Visualization module for generating the 6 multi-subplot performance figures
(Fig. 1 to Fig. 6), each with 3 network subplots:
  (a) Network-1       (b) Network-2       (c) Network-3
"""

import os
from typing import List
import matplotlib.pyplot as plt
import pandas as pd

from config.experiment_config import ABLATION_METHODS
from src.edge_game.experiments.ablation_analysis import METRICS_SPEC


def generate_six_performance_figures(
    df: pd.DataFrame,
    output_dir: str = "results/figures",
) -> List[str]:
    """
    Generate and save the 6 performance figures specified in Phase-2:
      - Fig. 1: Utility Value (Workload vs Mean Utility)
      - Fig. 2: Jain's Fairness Index (Workload vs Mean Fairness)
      - Fig. 3: Load Variance (Workload vs Mean Load Variance)
      - Fig. 4: Convergence Time (Workload vs Mean Convergence Time)
      - Fig. 5: Throughput (Workload vs Mean Throughput)
      - Fig. 6: Response Time (Workload vs Mean Response Time)
    Each figure contains 3 subplots: (a) Network-1, (b) Network-2, (c) Network-3.
    """
    os.makedirs(output_dir, exist_ok=True)

    subplot_specs = [
        ("N1", "(a) Network-1 (50 Nodes, 5 Servers)"),
        ("N2", "(b) Network-2 (150 Nodes, 15 Servers)"),
        ("N3", "(c) Network-3 (300 Nodes, 30 Servers)"),
    ]

    method_styles = {
        "A1: MFG only": {"marker": "o", "linestyle": "--", "color": "#1f77b4"},
        "A2: Stackelberg only": {"marker": "s", "linestyle": "-.", "color": "#ff7f0e"},
        "A3: MFG+Stackelberg": {"marker": "^", "linestyle": ":", "color": "#2ca02c"},
        "Proposed": {"marker": "D", "linestyle": "-", "color": "#d62728"},
    }

    workloads_sorted = sorted(df["workload"].unique())
    saved_paths: List[str] = []

    for fig_num, (col_key, metric_title, y_axis_label) in enumerate(METRICS_SPEC, start=1):
        fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=False)
        fig.suptitle(
            f"Fig. {fig_num}: {metric_title} vs. Workload",
            fontsize=14,
            fontweight="bold",
        )

        for ax, (net_code, panel_title) in zip(axes, subplot_specs):
            df_net = df[df["network"] == net_code]

            for method in ABLATION_METHODS:
                df_method = df_net[df_net["method"] == method]
                means = []
                stds = []
                for w in workloads_sorted:
                    vals = df_method.loc[df_method["workload"] == w, col_key].dropna().astype(float)
                    means.append(float(vals.mean()) if not vals.empty else 0.0)
                    stds.append(float(vals.std(ddof=1)) if len(vals) > 1 else 0.0)

                style = method_styles[method]
                ax.errorbar(
                    workloads_sorted,
                    means,
                    yerr=stds,
                    label=method,
                    marker=style["marker"],
                    linestyle=style["linestyle"],
                    color=style["color"],
                    linewidth=2.0,
                    capsize=3,
                )

            ax.set_title(panel_title, fontsize=11, fontweight="semibold")
            ax.set_xlabel("Workload (Tasks)", fontsize=10)
            ax.set_ylabel(y_axis_label, fontsize=10)
            ax.set_xticks(workloads_sorted)
            ax.grid(True, linestyle="--", alpha=0.4)

        axes[-1].legend(loc="best", fontsize=9, frameon=True)
        fig.tight_layout(rect=[0.0, 0.02, 1.0, 0.93])

        file_path = os.path.join(output_dir, f"fig{fig_num}_{col_key}.png")
        fig.savefig(file_path, dpi=300)
        plt.close(fig)
        saved_paths.append(file_path)

    return saved_paths