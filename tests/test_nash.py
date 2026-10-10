from src.edge_game.entities.edge_node import EdgeNode
from src.edge_game.games.nash_mfg import MeanFieldGame
from src.edge_game.workload.generator import generate_tasks


def test_mfg_selects_from_feasible_nodes():
    task = generate_tasks(1, "T1", 20, 10)[0]
    nodes = [
        EdgeNode("S1-N1", "S1", 12, 16, 200, 10, 30, 30),
        EdgeNode("S1-N2", "S1", 14, 18, 220, 12, 35, 30),
    ]
    decision, diagnostics = MeanFieldGame().solve(task, nodes)
    assert decision.node_id in {"S1-N1", "S1-N2"}
    assert diagnostics.nash_gap >= 0
