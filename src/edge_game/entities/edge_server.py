"""
EdgeServer entity representing a Stackelberg leader that coordinates
a cluster of EdgeNodes and sets resource pricing strategies.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class EdgeServer:
    """Represents an edge server acting as a leader in the Stackelberg game."""
    server_id: int
    node_ids: List[int] = field(default_factory=list)
    unit_price: float = 1.0
    min_price: float = 0.25
    max_price: float = 4.00
    congestion_penalty_weight: float = 0.20

    def set_price(self, new_price: float) -> None:
        """Update the resource price within admissible bounds."""
        self.unit_price = float(min(max(new_price, self.min_price), self.max_price))