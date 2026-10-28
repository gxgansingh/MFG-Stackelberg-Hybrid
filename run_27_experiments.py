"""
Runner script for Phase-1:
Generates Table 1 (Network Configuration), Table 2 (Resource Filtering Decisions
for N1, N2, and N3), and the 27 Experimental Configurations (E1-E27) with
observed P1-P4 task distributions.
"""

import os
from src.edge_game.experiments.resource_filtering_27 import (
    build_table1_network_parameters,
    build_table2_filtering_decisions,
    run_27_experimental_configurations,
)


def main() -> None:
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 88)
    print("PHASE-1: NETWORK PARAMETERS, RESOURCE FILTERING & 27 EXPERIMENTAL CONFIGURATIONS")
    print("=" * 88)

    # 1. Table 1: Network Configuration and Resource Parameters
    table1_df = build_table1_network_parameters()
    table1_path = os.path.join(output_dir, "phase1_table1_network_parameters.csv")
    table1_df.to_csv(table1_path, index=False)
    print("\n[Table 1] Network Configuration and Resource Parameters:")
    print(table1_df.to_string(index=False))

    # 2. Table 2: Filtering Decisions at Each Workload (for N1, N2, N3)
    for net_code in ["N1", "N2", "N3"]:
        table2_df = build_table2_filtering_decisions(net_code)
        table2_path = os.path.join(output_dir, f"phase1_table2_filtering_{net_code}.csv")
        table2_df.to_csv(table2_path, index=False)
        print(f"\n[Table 2 - {net_code}] Filtering Decisions at Each Workload:")
        print(table2_df.to_string(index=False))

    # 3. 27 Experimental Configurations (E1 - E27)
    exp27_df = run_27_experimental_configurations()
    exp27_path = os.path.join(output_dir, "phase1_27_experimental_configurations.csv")
    exp27_df.to_csv(exp27_path, index=False)

    summary_cols = [
        "Exp.",
        "Network",
        "Edge Nodes",
        "Servers",
        "Task Load",
        "Task Profile",
        "Observed Priority Distribution (P1–P4)",
        "Mean Feasible Nodes",
    ]
    print("\n[27 Experimental Configurations (E1–E27) with Observed P1–P4 Distributions]:")
    print(exp27_df[summary_cols].to_string(index=False))
    print(f"\nPhase-1 CSV artifacts saved to '{output_dir}/'.")


if __name__ == "__main__":
    main()