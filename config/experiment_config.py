from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "network1"


@dataclass(frozen=True)
class PriorityProfile:
    profile_id: str
    name: str
    weights: tuple[float, float, float]


PRIORITY_PROFILES = (
    PriorityProfile("T1", "urgency-dominant", (0.50, 0.30, 0.20)),
    PriorityProfile("T2", "latency-dominant", (0.30, 0.50, 0.20)),
    PriorityProfile("T3", "service-dominant", (0.33, 0.33, 0.34)),
)

LOADS = (1250, 2500, 5000)
TICKS = 1250

MFG_MAX_ITERATIONS = 80
MFG_TOLERANCE = 1e-4

# N1 preserves the existing topology.
# N2 and N3 are provisional scaling configurations.
NETWORKS = {
    "N1": {
        "server_count": 5,
        "nodes_per_server": 10,
    },
    "N2": {
        "server_count": 15,
        "nodes_per_server": 10,
    },
    "N3": {
        "server_count": 30,
        "nodes_per_server": 10,
    },
}

# Backwards compatibility for existing experiments.
NETWORK = NETWORKS["N1"]

MFG_UTILITY_WEIGHTS = {
    "priority": 0.30,
    "latency": 0.25,
    "resource": 0.20,
    "queue": 0.15,
    "energy": 0.10,
}

REPLICATED_SEEDS = (11, 22, 33, 44, 55)