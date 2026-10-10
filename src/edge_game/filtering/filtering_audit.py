import pandas as pd


def build_filtering_record(task, node, result) -> dict:
    return {
        "task_id": task.task_id,
        "priority_profile": task.priority_profile,
        "priority_class": task.priority_label,
        "priority_score": task.priority_score,
        "server_id": node.server_id,
        "node_id": node.node_id,
        "cpu_ok": result.cpu_ok,
        "memory_ok": result.memory_ok,
        "bandwidth_ok": result.bandwidth_ok,
        "latency_ok": result.latency_ok,
        "energy_ok": result.energy_ok,
        "queue_ok": result.queue_ok,
        "feasible": result.feasible,
        "failed_constraints": ",".join(result.failed_constraints),
    }


def summarize_filtering(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    return frame.groupby("priority_profile").agg(
        candidates=("node_id", "count"),
        feasible=("feasible", "sum"),
        feasibility_ratio=("feasible", "mean"),
    ).reset_index()
