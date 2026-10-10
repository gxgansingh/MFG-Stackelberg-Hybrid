from dataclasses import dataclass, field

from .edge_node import EdgeNode


@dataclass
class EdgeServer:
    server_id: str
    nodes: list[EdgeNode] = field(default_factory=list)
    network_latency_ms: float = 5.0

    def aggregate_load(self) -> float:
        if not self.nodes:
            return 0.0
        return sum(node.utilization_state() for node in self.nodes) / len(self.nodes)
