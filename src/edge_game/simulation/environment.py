from dataclasses import dataclass

from config.experiment_config import NETWORK
from ..entities.edge_node import EdgeNode
from ..entities.edge_server import EdgeServer


@dataclass
class Network1Environment:
    servers: list[EdgeServer]

    @classmethod
    def create(cls, seed: int = 42):
        servers = []
        for server_index in range(NETWORK["server_count"]):
            server_id = f"S{server_index + 1}"
            nodes = []
            for node_index in range(NETWORK["nodes_per_server"]):
                nodes.append(
                    EdgeNode(
                        node_id=f"{server_id}-N{node_index + 1}",
                        server_id=server_id,
                        cpu_capacity_gcps=12.0 + (node_index % 4),
                        memory_capacity_gb=16.0 + (node_index % 3) * 2,
                        bandwidth_capacity_mbps=150.0 + (node_index % 5) * 20.0,
                        latency_ms=8.0 + node_index * 1.2 + server_index * 1.5,
                        energy_per_task_j=30.0 + node_index * 3.0 + server_index * 2.0,
                        queue_capacity=25 + (node_index % 4) * 5,
                    )
                )
            servers.append(
                EdgeServer(
                    server_id=server_id,
                    nodes=nodes,
                    network_latency_ms=4.0 + server_index * 2.0,
                )
            )
        return cls(servers)

    def apply_allocation(self, task, server_id: str, node_id: str) -> None:
        server = next(s for s in self.servers if s.server_id == server_id)
        node = next(n for n in server.nodes if n.node_id == node_id)
        node.reserve(task)
        if task.arrival_tick % 5 == 4:
            node.release_fraction(0.82)
