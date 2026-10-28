"""
Runner script for Phase-2:
Executes the 9-run statistical replication study across all networks, workloads,
task profiles, and 4 ablation methods (A1, A2, A3, Proposed), computes Phase-2
Tables 1, 2, and 3, and generates the 6 three-subplot performance figures.
"""

import os
from src.edge_game.experiments.ablation_analysis import (
    build_equilibrium_ablation_checklist,
    build_phase2_table1_mean_sd,
    build_phase2_table2_significance,
    build_phase2_table3_equilibrium_gaps,
    run_phase2_replicated_suite,
)
from src.edge_game.experiments.visualization import generate_six_performance_figures


def main() -> None:
    output_dir = "results"
    figures_dir = os.path.join(output_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    print("=" * 88)
    print("PHASE-2: STATISTICAL ANALYSIS, EQUILIBRIUM ABLATION & PERFORMANCE VISUALIZATION")
    print("=" * 88)

    # 1. Run replicated Phase-2 experiment suite (3 networks x 3 workloads x 4 methods x 9 runs)
    raw_df = run_phase2_replicated_suite()
    raw_csv_path = os.path.join(output_dir, "phase2_replicated_runs.csv")
    raw_df.to_csv(raw_csv_path, index=False)

    # 2. Phase-2 Table-1: Mean +/- SD comparison across the 6 metrics
    table1_df = build_phase2_table1_mean_sd(raw_df)
    table1_df.to_csv(os.path.join(output_dir, "phase2_table1_mean_sd.csv"), index=False)
    print("\n[Phase-2 Table-1] Performance Comparison (Mean ± SD):")
    print(table1_df.to_string(index=False))

    # 3. Phase-2 Table-2: Statistical Significance (p-values)
    table2_df = build_phase2_table2_significance(raw_df)
    table2_df.to_csv(os.path.join(output_dir, "phase2_table2_significance.csv"), index=False)
    print("\n[Phase-2 Table-2] Statistical Significance (Welch t-test & ANOVA p-values):")
    print(table2_df.to_string(index=False))

    # 4. Equilibrium Ablation Applicability Checklist
    checklist_df = build_equilibrium_ablation_checklist()
    checklist_df.to_csv(
        os.path.join(output_dir, "phase2_equilibrium_ablation_checklist.csv"), index=False
    )
    print("\n[Nash and Stackelberg Equilibrium Ablation Structure]:")
    print(checklist_df.to_string(index=False))

    # 5. Phase-2 Table-3: Final Nash Gap & Stackelberg Gap (Mean +/- SD)
    table3_df = build_phase2_table3_equilibrium_gaps(raw_df)
    table3_df.to_csv(os.path.join(output_dir, "phase2_table3_equilibrium_gaps.csv"), index=False)
    print("\n[Phase-2 Table-3] Equilibrium Gap Ablation (Mean ± SD):")
    print(table3_df.to_string(index=False))

    # 6. Generate the 6 Three-Subplot Performance Figures
    figure_paths = generate_six_performance_figures(raw_df, output_dir=figures_dir)
    print("\n[Generated 6 Three-Subplot Performance Figures]:")
    for path in figure_paths:
        print(f"  - {path}")


if __name__ == "__main__":
    main()