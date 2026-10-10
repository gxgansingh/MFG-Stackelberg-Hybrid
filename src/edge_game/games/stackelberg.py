from dataclasses import dataclass


@dataclass(frozen=True)
class StackelbergDecision:
    server_id: str
    follower_node_id: str
    leader_cost: float
    follower_cost: float
    stackelberg_gap: float
    margin: float
    best_alternative_cost: float


class StackelbergGame:
    def __init__(self, server_penalty_weight: float = 0.35):
        self.server_penalty_weight = server_penalty_weight

    def leader_cost(self, server, mfg_decision) -> float:
        return (
            0.60 * server.aggregate_load()
            + 0.20 * (server.network_latency_ms / 100.0)
            + 0.20
            * self.server_penalty_weight
            * mfg_decision.cost
        )

    def choose_server(self, task, server_decisions):
        if not server_decisions:
            raise ValueError(
                "Stackelberg received no feasible server decisions."
            )

        ranked = []

        for (
            server_id,
            mfg_decision,
            nash_diag,
            server,
        ) in server_decisions:

            leader_cost = self.leader_cost(
                server,
                mfg_decision,
            )

            ranked.append(
                (
                    leader_cost,
                    server_id,
                    mfg_decision,
                    server,
                )
            )

        ranked.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        leader_cost, server_id, mfg_decision, _ = ranked[0]

        second_cost = (
            ranked[1][0]
            if len(ranked) > 1
            else leader_cost
        )

        margin = max(
            0.0,
            second_cost - leader_cost,
        )

        best_alternative_cost = (
            second_cost
            if len(ranked) > 1
            else leader_cost
        )

        stackelberg_gap = max(
            0.0,
            leader_cost - best_alternative_cost,
        )

        return StackelbergDecision(
            server_id=server_id,
            follower_node_id=mfg_decision.node_id,
            leader_cost=leader_cost,
            follower_cost=mfg_decision.cost,
            stackelberg_gap=stackelberg_gap,
            margin=margin,
            best_alternative_cost=best_alternative_cost,
        )