"""
Runner script for Phase-2 and Full Restructured Report Generation:
Executes the 9-run statistical replication study across all networks, workloads,
task profiles, and 4 ablation methods (A1, A2, A3, Proposed), computes all
summary, condition-level, paired statistical, and equilibrium diagnostic tables,
generates the 6 three-subplot performance figures, and compiles `report.md` and `report.html`.
"""

import os
from src.edge_game.experiments.ablation_analysis import (
    build_condition_breakdown_tables,
    build_equilibrium_ablation_checklist,
    build_load_wise_equilibrium_diagnostics,
    build_paired_statistical_comparisons,
    build_phase2_table1_mean_sd,
    build_phase2_table2_significance,
    build_phase2_table3_equilibrium_gaps,
    run_phase2_replicated_suite,
)
from src.edge_game.experiments.report import generate_markdown_and_html_reports
from src.edge_game.experiments.resource_filtering_27 import (
    build_table1_network_parameters,
    build_table2_filtering_decisions,
    run_27_experimental_configurations,
)
from src.edge_game.experiments.visualization import generate_six_performance_figures


def main() -> None:
    output_dir = "results"
    figures_dir = os.path.join(output_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    print("=" * 88)
    print("PHASE-2: STATISTICAL ANALYSIS, EQUILIBRIUM ABLATION & RESTRUCTURED REPORT")
    print("=" * 88)

    # 1. Prepare Phase-1 tables for unified report compilation
    p1_table1 = build_table1_network_parameters()
    p1_table2_map = {
        net_code: build_table2_filtering_decisions(net_code)
        for net_code in ["N1", "N2", "N3"]
    }
    p1_exp27 = run_27_experimental_configurations()

    # 2. Run replicated Phase-2 experiment suite (3 networks x 3 workloads x 4 methods x 9 runs)
    raw_df = run_phase2_replicated_suite()
    raw_csv_path = os.path.join(output_dir, "phase2_replicated_runs.csv")
    raw_df.to_csv(raw_csv_path, index=False)

    # 3. Phase-2 Table-1: Overall Mean +/- SD comparison across the 6 metrics
    table1_df = build_phase2_table1_mean_sd(raw_df)
    table1_df.to_csv(os.path.join(output_dir, "phase2_table1_mean_sd.csv"), index=False)
    print("\n[Table 4] Overall Performance Comparison (Mean ± SD):")
    print(table1_df.to_string(index=False))

    # 4. Phase-2 Table-2: Statistical Significance (Welch t-test & ANOVA p-values)
    table2_df = build_phase2_table2_significance(raw_df)
    table2_df.to_csv(os.path.join(output_dir, "phase2_table2_significance.csv"), index=False)
    print("\n[Table 5] Statistical Significance Summary (Welch t-test & ANOVA p-values):")
    print(table2_df.to_string(index=False))

    # 5. Paired Statistical Comparisons (Mean Diff, 95% CI, Holm p)
    paired_df = build_paired_statistical_comparisons(raw_df)
    paired_df.to_csv(os.path.join(output_dir, "phase2_paired_comparisons.csv"), index=False)
    print("\n[Table 6] Paired Statistical Comparisons (95% CI & Holm Correction):")
    print(paired_df.to_string(index=False))

    # 6. Condition-Level Breakdown Tables (Part 1 & Part 2)
    cond_p1, cond_p2 = build_condition_breakdown_tables(raw_df)
    cond_p1.to_csv(os.path.join(output_dir, "phase2_condition_part1.csv"), index=False)
    cond_p2.to_csv(os.path.join(output_dir, "phase2_condition_part2.csv"), index=False)

    # 7. Equilibrium Ablation Checklist & Overall Gaps
    checklist_df = build_equilibrium_ablation_checklist()
    checklist_df.to_csv(
        os.path.join(output_dir, "phase2_equilibrium_ablation_checklist.csv"), index=False
    )
    table3_df = build_phase2_table3_equilibrium_gaps(raw_df)
    table3_df.to_csv(os.path.join(output_dir, "phase2_table3_equilibrium_gaps.csv"), index=False)
    print("\n[Table 8] Overall Equilibrium Gap Ablation (Mean ± SD):")
    print(table3_df.to_string(index=False))

    # 8. Load-Wise Nash and Stackelberg Equilibrium Diagnostics
    nash_diag, stack_diag = build_load_wise_equilibrium_diagnostics(raw_df)
    nash_diag.to_csv(os.path.join(output_dir, "phase2_nash_diagnostics.csv"), index=False)
    stack_diag.to_csv(os.path.join(output_dir, "phase2_stackelberg_diagnostics.csv"), index=False)
    print("\n[Table 9] Load-Wise Nash Equilibrium Diagnostics:")
    print(nash_diag.to_string(index=False))
    print("\n[Table 10] Load-Wise Stackelberg Equilibrium Diagnostics:")
    print(stack_diag.to_string(index=False))

    # 9. Generate the 6 Three-Subplot Performance Figures
    figure_paths = generate_six_performance_figures(raw_df, output_dir=figures_dir)
    print("\n[Generated 6 Three-Subplot Performance Figures]:")
    for path in figure_paths:
        print(f"  - {path}")

    # 10. Compile Restructured Markdown and HTML Reports
    generate_markdown_and_html_reports(
        phase1_table1=p1_table1,
        phase1_table2_by_net=p1_table2_map,
        phase1_27_df=p1_exp27,
        phase2_table1=table1_df,
        phase2_table2=table2_df,
        equilibrium_checklist=checklist_df,
        phase2_table3=table3_df,
        figure_paths=figure_paths,
        md_output_path="report.md",
        html_output_path="report.html",
        raw_phase2_df=raw_df,
    )
    print("\n[Compiled Restructured Reports]:")
    print("  - report.md")
    print("  - report.html")


if __name__ == "__main__":
    main()