from src.edge_game.experiments.network1_experiment import run_network1


def test_network1_has_nine_runs():
    frames = run_network1()
    assert len(frames["runs"]) == 9
    assert set(frames["runs"]["profile_id"]) == {"T1", "T2", "T3"}
    assert set(frames["runs"]["load"]) == {1250, 2500, 5000}
