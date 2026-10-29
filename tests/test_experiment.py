"""
Unit tests for Phase-1 (27 experimental configurations) and Phase-2 (ablation tables)
experiment pipelines.
"""

from src.edge_game.experiments.ablation_analysis import (
    build_equilibrium_ablation_checklist,
    build_phase2_table1_mean_sd,
    build_phase2_table2_significance,
    build_phase2_table3_equilibrium_gaps,
    run_phase2_replicated_suite,
)
from src.edge_game.experiments.resource_filtering_27 import (
    build_table1_network_parameters,
    build_table2_filtering_decisions,
)


def test_phase1_tables_structure() -> None:
    """Verify Table 1 and Table 2 generate the exact required rows and columns."""
    t1 = build_table1_network_parameters()
    assert len(t1) == 13
    assert "Network-1 (Small)" in t1.columns
    assert "Network-2 (Intermediate)" in t1.columns
    assert "Network-3 (Stress)" in t1.columns

    t2_n1 = build_table2_filtering_decisions("N1", seed=42)
    assert len(t2_n1) == 7
    assert list(t2_n1["Metric"]) == [
        "CPU",
        "RAM",
        "Storage",
        "Bandwidth",
        "Latency",
        "CPU utilization",
        "RAM utilization",
    ]


def test_phase2_ablation_tables_generation() -> None:
    """Verify Phase-2 replicated suite and Tables 1, 2, and 3 execute cleanly."""
    df = run_phase2_replicated_suite(workloads=[1250, 3000], num_runs=3, base_seed=100)
    assert not df.empty

    t1 = build_phase2_table1_mean_sd(df)
    assert len(t1) == 6
    assert "Proposed" in t1.columns

    t2 = build_phase2_table2_significance(df)
    assert len(t2) == 6
    assert "Proposed vs A1" in t2.columns
    assert "Proposed vs A2" in t2.columns
    assert "Proposed vs A3" in t2.columns

    checklist = build_equilibrium_ablation_checklist()
    assert len(checklist) == 4

    t3 = build_phase2_table3_equilibrium_gaps(df)
    assert len(t3) == 2
    assert t3.loc[t3["Equilibrium metric"] == "Final Nash Gap ↓", "A2: Stackelberg only"].iloc[0] == "N/A"
    assert t3.loc[t3["Equilibrium metric"] == "Stackelberg Gap ↓", "A1: MFG only"].iloc[0] == "N/A"