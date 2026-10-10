from src.edge_game.simulation.environment import Network1Environment
from src.edge_game.simulation.engine import SimulationEngine
from src.edge_game.workload.generator import generate_tasks


def test_small_simulation_runs():
    tasks = generate_tasks(20, "T2", 30, 20)
    metrics, records, filtering = SimulationEngine(Network1Environment.create(30)).run(tasks, 20)
    assert metrics["completed_tasks"] == len(records)
    assert len(filtering) == 20 * 50
