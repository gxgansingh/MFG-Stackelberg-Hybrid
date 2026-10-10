from src.edge_game.workload.priority import calculate_priority_score, classify_priority


def test_priority_score():
    score = calculate_priority_score(0.92, 0.71, 0.64, (0.50, 0.30, 0.20))
    assert round(score, 4) == 0.8010


def test_priority_boundaries():
    assert classify_priority(0.75)[0] == 4
    assert classify_priority(0.55)[0] == 3
    assert classify_priority(0.30)[0] == 2
    assert classify_priority(0.29)[0] == 1
