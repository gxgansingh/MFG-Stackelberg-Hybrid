from src.edge_game.entities.edge_node import EdgeNode
from src.edge_game.filtering.resource_filter import ResourceFilter
from src.edge_game.workload.generator import generate_tasks


def test_filtering_rejects_insufficient_cpu():
    task = generate_tasks(1, "T1", 10, 10)[0]
    node = EdgeNode("S1-N1", "S1", 0.1, 16, 100, 10, 30, 20)
    result = ResourceFilter().evaluate(task, node)
    assert not result.feasible
    assert not result.cpu_ok
