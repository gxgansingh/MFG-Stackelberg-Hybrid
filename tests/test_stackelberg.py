from src.edge_game.entities.edge_server import EdgeServer
from src.edge_game.games.nash_mfg import MFGDecision, NashDiagnostics
from src.edge_game.games.stackelberg import StackelbergGame


def test_stackelberg_selects_best_leader_cost():
    servers = [EdgeServer("S1", [], 5), EdgeServer("S2", [], 20)]
    decisions = [
        ("S1", MFGDecision("S1-N1", "S1", 0.2, 0.8, 0.2, 0.1, 1, 1), NashDiagnostics(True, 1, 0, 0, 0), servers[0]),
        ("S2", MFGDecision("S2-N1", "S2", 0.2, 0.8, 0.2, 0.1, 1, 1), NashDiagnostics(True, 1, 0, 0, 0), servers[1]),
    ]
    decision = StackelbergGame().choose_server(None, decisions)
    assert decision.server_id == "S1"
