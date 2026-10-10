# Edge Game Network-1

Fresh implementation of the Network-1 hierarchical edge resource-allocation experiment.

## Pipeline

```text
IoT Task -> Resource Feasibility Filtering -> Feasible Nodes
         -> MFG/Nash -> Stackelberg -> Final Allocation
         -> Metrics -> Equilibrium Diagnostics -> Statistics -> Figures -> Report
```

## Network-1

- 5 edge servers
- 10 nodes per server
- 50 nodes total
- Loads: 1250, 2500, 5000 tasks
- T1: urgency-dominant, W3 = (0.50, 0.30, 0.20)
- T2: latency-dominant, W4 = (0.30, 0.50, 0.20)
- T3: service-dominant, W1 = (0.33, 0.33, 0.34)
- 1250-tick horizon

## Priority score

`S = wU*U + wL*L + wI*I`

- P1 Critical: 0.75 <= S <= 1.00
- P2 High: 0.55 <= S < 0.75
- P3 Medium: 0.30 <= S < 0.55
- P4 Low: 0.00 <= S < 0.30

Internal class values are 1=P4, 2=P3, 3=P2, 4=P1.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
python -m src.edge_game.main
```

Results are written under `outputs/network1/`.

Mean and SD at a fixed load summarize variation across T1/T2/T3. They are not independent stochastic replications.
