"""
End-to-end integration tests for SimulationEngine across all 4 ablation methods
(A1, A2, A3, and Proposed).
"""

import math
from config.experiment_config import ABLATION_METHODS, NETWORKS
from src.edge_game.simulation.engine import SimulationEngine


def test_ablation_methods_distinguish_nash_and_stackelberg_gaps() -> None:
    """
    Verify Table-3 equilibrium applicability rules:
      - A1: MFG only -> finite Nash Gap, NaN Stackelberg Gap
      - A2: Stackelberg only -> NaN Nash Gap, finite Stackelberg Gap
      - A3 & Proposed -> finite Nash Gap and finite Stackelberg Gap
    """
    engine = SimulationEngine(NETWORKS["N1"])
    results = {
        method: engine.run_trial(workload_size=200, task_profile="T2", method=method, seed=99)
        for method in ABLATION_METHODS
    }

    # Check A1: MFG only
    a1_metrics = results["A1: MFG only"].metrics
    assert not math.isnan(a1_metrics.nash_gap)
    assert math.isnan(a1_metrics.stackelberg_gap)

    # Check A2: Stackelberg only
    a2_metrics = results["A2: Stackelberg only"].metrics
    assert math.isnan(a2_metrics.nash_gap)
    assert not math.isnan(a2_metrics.stackelberg_gap)

    # Check A3 and Proposed
    a3_metrics = results["A3: MFG+Stackelberg"].metrics
    prop_metrics = results["Proposed"].metrics
    assert not math.isnan(a3_metrics.nash_gap) and not math.isnan(a3_metrics.stackelberg_gap)
    assert not math.isnan(prop_metrics.nash_gap) and not math.isnan(prop_metrics.stackelberg_gap)

    # Proposed priority-aware method should achieve lower equilibrium gaps and higher utility
    assert prop_metrics.nash_gap < a1_metrics.nash_gap
    assert prop_metrics.stackelberg_gap < a2_metrics.stackelberg_gap
    assert prop_metrics.utility > a1_metrics.utility
    assert prop_metrics.utility > a2_metrics.utility