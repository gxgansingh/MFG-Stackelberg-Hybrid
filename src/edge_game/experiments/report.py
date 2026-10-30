"""
Automated report generation module.
Compiles Phase-1 and Phase-2 experimental tables, detailed architectural and
mathematical explanations, condition-level breakdowns, paired statistical tests,
equilibrium diagnostics, and the 6 three-subplot performance figures into
publication-ready Markdown (report.md) and HTML (report.html) files.
"""

import os
from typing import Dict, List
import pandas as pd

from src.edge_game.experiments.ablation_analysis import (
    build_condition_breakdown_tables,
    build_load_wise_equilibrium_diagnostics,
    build_paired_statistical_comparisons,
)


def _df_to_markdown_table(df: pd.DataFrame) -> str:
    """Convert a pandas DataFrame into a GitHub-flavored Markdown table."""
    headers = [str(col) for col in df.columns]
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"

    body_lines: List[str] = []
    for _, row in df.iterrows():
        cells = [str(val) for val in row.values]
        body_lines.append("| " + " | ".join(cells) + " |")

    return "\n".join([header_line, separator_line] + body_lines)


def _consolidate_table2_filtering(
    phase1_table2_by_net: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Consolidate the per-network Table 2 filtering audits into a single compact
    table to eliminate redundant repetition while preserving all 7 rules.
    """
    if "N1" not in phase1_table2_by_net:
        first_key = next(iter(phase1_table2_by_net))
        return phase1_table2_by_net[first_key]

    base_df = phase1_table2_by_net["N1"][["Metric", "Eligibility rule"]].copy()
    for net_code, df_net in phase1_table2_by_net.items():
        base_df[f"{net_code} (1,250 / 3,000 / 5,000)"] = [
            f"{r['1,250 tasks'].replace('Apply ', '')} | "
            f"{r['3,000 tasks'].replace('Apply ', '')} | "
            f"{r['5,000 tasks'].replace('Apply ', '')}"
            for _, r in df_net.iterrows()
        ]
    return base_df


def generate_markdown_and_html_reports(
    phase1_table1: pd.DataFrame,
    phase1_table2_by_net: Dict[str, pd.DataFrame],
    phase1_27_df: pd.DataFrame,
    phase2_table1: pd.DataFrame,
    phase2_table2: pd.DataFrame,
    equilibrium_checklist: pd.DataFrame,
    phase2_table3: pd.DataFrame,
    figure_paths: List[str],
    md_output_path: str = "report.md",
    html_output_path: str = "report.html",
    raw_phase2_df: pd.DataFrame | None = None,
) -> None:
    """
    Generate restructured, self-explanatory `report.md` and `report.html` files.
    """
    consolidated_t2 = _consolidate_table2_filtering(phase1_table2_by_net)

    exp27_display_cols = [
        "Exp.",
        "Network",
        "Edge Nodes",
        "Servers",
        "Task Load",
        "Tasks/Node",
        "Task Profile",
        "Observed Priority Distribution (P1–P4)",
        "Mean Feasible Nodes",
    ]
    exp27_view = phase1_27_df[exp27_display_cols]

    if raw_phase2_df is not None and not raw_phase2_df.empty:
        cond_part1, cond_part2 = build_condition_breakdown_tables(raw_phase2_df)
        paired_stats_df = build_paired_statistical_comparisons(raw_phase2_df)
        nash_diag_df, stack_diag_df = build_load_wise_equilibrium_diagnostics(raw_phase2_df)
    else:
        cond_part1 = pd.DataFrame()
        cond_part2 = pd.DataFrame()
        paired_stats_df = pd.DataFrame()
        nash_diag_df = pd.DataFrame()
        stack_diag_df = pd.DataFrame()

    # -------------------- 1. BUILD MARKDOWN REPORT --------------------
    md_lines: List[str] = [
        "# Intra-Node Load Balancing for IoT Edge Computing Using Non-Cooperative Game Theory",
        "",
        "## 1. System Architecture & How the Framework Works",
        "",
        "This simulation framework models a hierarchical three-tier IoT Edge Computing environment consisting of **IoT Task Generators**, **Edge Nodes** (followers), and **Edge Servers** (leaders). Rather than relying on static heuristics or unverified equilibrium claims, the pipeline executes a five-stage mathematical workflow:",
        "",
        "1. **Heterogeneous Topology & Workload Generation (`generator.py`)**:",
        "   - Instantiates three network scales: **Network-1 (Small)** with 50 edge nodes and 5 servers, **Network-2 (Intermediate)** with 150 nodes and 15 servers, and **Network-3 (Stress)** with 300 nodes and 30 servers.",
        "   - Generates task workloads of **1,250**, **3,000**, and **5,000** tasks under three arrival profiles: **T1** (latency-sensitive telemetry), **T2** (balanced mixed IoT traffic), and **T3** (compute/bandwidth-intensive analytics).",
        "2. **Multi-Attribute Priority Classification (`priority.py`)**:",
        "   - Every individual task $i$ is evaluated using a composite priority score $S_i \\in [0, 1]$ combining deadline urgency ($45\\%$), application criticality ($35\\%$), and normalized resource intensity ($20\\%$):",
        "     $$S_i = 0.45 \\cdot U_i + 0.35 \\cdot C_i + 0.20 \\cdot I_i$$",
        "   - Tasks are dynamically classified into four priority tiers: **P1** ($S_i \\ge 0.70$, weight $1.60$), **P2** ($0.52 \\le S_i < 0.70$, weight $1.25$), **P3** ($0.35 \\le S_i < 0.52$, weight $1.00$), and **P4** ($S_i < 0.35$, weight $0.75$). Thus, each workload produces a realistic observed distribution of $P_1, P_2, P_3, P_4$ tasks rather than a single static label.",
        "3. **Seven-Rule Resource Feasibility Filtering (`resource_filter.py`)**:",
        "   - Before game-theoretic allocation, candidate edge nodes are filtered against seven strict hardware and QoS constraints: (i) Available CPU $\\ge$ task demand, (ii) Available RAM $\\ge$ task demand, (iii) Available Storage $\\ge$ task demand, (iv) Available Bandwidth $\\ge$ task demand, (v) Estimated transmission + queuing latency $\\le 50\\text{ ms}$, (vi) Projected CPU utilization $\\le 85\\%$, and (vii) Projected RAM utilization $\\le 90\\%$.",
        "4. **Hierarchical Game-Theoretic Coordination (`stackelberg.py`, `nash_mfg.py`, `hierarchical_game.py`)**:",
        "   - **Leader Stage (Stackelberg Pricing)**: Each Edge Server $s$ acts as a Stackelberg leader, optimizing its unit resource price $p_s \\in [p_{\\min}, p_{\\max}]$ to maximize server utility (revenue minus cluster congestion penalty) while anticipating the elastic demand response of follower nodes.",
        "   - **Follower Stage (Mean-Field Game Nash Equilibrium)**: Edge Nodes and tasks act as followers. First, damped fixed-point iterations compute the stationary mean-field flow distribution across nodes. Second, tasks are routed sequentially by minimizing a priority-weighted potential cost combining base propagation latency, real-time virtual queue backlog, quadratic utilization congestion, and server pricing.",
        "   - **Ablation Variants**:",
        "     - **A1: MFG only**: Solves the intra-node MFG Nash distribution without Stackelberg pricing feedback or priority ordering.",
        "     - **A2: Stackelberg only**: Optimizes server leader prices and routes tasks by price-proportional weights without intra-node MFG congestion balancing.",
        "     - **A3: MFG+Stackelberg**: Combines Stackelberg pricing and MFG Nash load balancing without task priority differentiation.",
        "     - **Proposed (Priority-Aware MFG + Stackelberg)**: Integrates 7-rule feasibility filtering, $P_1\\text{--}P_4$ priority-ordered scheduling, Stackelberg leader pricing, and priority-weighted MFG Nash routing.",
        "5. **Queue-Based Task Execution & Independent Equilibrium Verification (`edge_node.py`, `metrics.py`)**:",
        "   - Tasks are committed to their assigned nodes, advancing each node's `next_available_time_ms` queue clock based on instruction length (MI) and core processing speed (MIPS) to produce genuine turnaround response times and throughput.",
        "   - **Final Nash Gap ($\\downarrow$)** is verified independently post-allocation by auditing the maximum relative cost reduction any task could achieve by unilaterally migrating to the least-congested node.",
        "   - **Stackelberg Gap ($\\downarrow$)** is verified independently over a fine 60-point price audit grid by measuring the relative leader utility shortfall against the global best-response price.",
        "",
        "---",
        "",
        "## 2. Experimental Design & Phase-1 Resource Filtering (27 Configurations)",
        "",
        "- **Networks evaluated:** Network-1 (50 nodes, 5 servers), Network-2 (150 nodes, 15 servers), Network-3 (300 nodes, 30 servers).",
        "- **Task loads:** 1,250, 3,000, and 5,000 tasks.",
        "- **Task profiles:** T1 (Urgency-heavy), T2 (Balanced), T3 (Compute-heavy).",
        "- **Phase-1 scope:** 27 unique experimental configurations (`E1`–`E27`).",
        "- **Phase-2 scope:** 3 networks $\\times$ 3 workloads $\\times$ 4 ablation policies $\\times$ 9 replications = **324 matched simulation runs** (81 paired conditions across the 4 methods).",
        "",
        "### Table 1. Network Configuration and Resource Parameters",
        "",
        _df_to_markdown_table(phase1_table1),
        "",
        "### Table 2. Consolidated Seven-Rule Resource Filtering Viability Across Networks and Workloads",
        "",
        _df_to_markdown_table(consolidated_t2),
        "",
        "### Table 3. Phase-1 Experimental Configurations (E1–E27) with Observed P1–P4 Priority Distributions",
        "",
        _df_to_markdown_table(exp27_view),
        "",
        "---",
        "",
        "## 3. Phase-2 Overall Ablation Results & Statistical Significance",
        "",
        "Values in Table 4 represent Mean $\\pm$ Sample Standard Deviation across all replicated runs. Table 5 reports two-sample Welch $t$-test and four-group one-way ANOVA $p$-values.",
        "",
        "### Table 4. Overall Performance Comparison Across Six Metrics (Mean ± SD)",
        "",
        _df_to_markdown_table(phase2_table1),
        "",
        "### Table 5. Statistical Significance Summary (Welch t-test & ANOVA p-values)",
        "",
        _df_to_markdown_table(phase2_table2),
        "",
    ]

    if not paired_stats_df.empty:
        md_lines.extend(
            [
                "### Table 6. Paired Statistical Comparisons (Proposed Minus Baseline with 95% CI & Holm Correction)",
                "",
                "Reported differences represent `Proposed` minus each baseline across matched conditions (paired by network, workload, task profile, and random seed). Two-sided paired $t$-tests with step-down Holm-Bonferroni correction ($\\alpha = 0.05$).",
                "",
                _df_to_markdown_table(paired_stats_df),
                "",
            ]
        )

    if not cond_part1.empty and not cond_part2.empty:
        md_lines.extend(
            [
                "---",
                "",
                "## 4. Condition-Level Results by Workload and Task Profile",
                "",
                "### Part 1: Utility, Jain's Fairness & Load Variance",
                "",
                _df_to_markdown_table(cond_part1),
                "",
                "### Part 2: Convergence Time, System Throughput & Response Time",
                "",
                _df_to_markdown_table(cond_part2),
                "",
            ]
        )

    md_lines.extend(
        [
            "---",
            "",
            "## 5. Equilibrium Ablation & Load-Wise Diagnostics",
            "",
            "Because **A1 (MFG only)** does not employ a Stackelberg pricing leader and **A2 (Stackelberg only)** does not employ an MFG follower solver, their respective equilibrium metrics are distinguished explicitly rather than conflated.",
            "",
            "### Table 7. Nash and Stackelberg Equilibrium Applicability Structure",
            "",
            _df_to_markdown_table(equilibrium_checklist),
            "",
            "### Table 8. Overall Equilibrium Gap Comparison (Mean ± SD)",
            "",
            _df_to_markdown_table(phase2_table3),
            "",
        ]
    )

    if not nash_diag_df.empty and not stack_diag_df.empty:
        md_lines.extend(
            [
                "### Table 9. Load-Wise Nash Equilibrium Diagnostics",
                "",
                _df_to_markdown_table(nash_diag_df),
                "",
                "### Table 10. Load-Wise Stackelberg Equilibrium Diagnostics",
                "",
                _df_to_markdown_table(stack_diag_df),
                "",
            ]
        )

    md_lines.extend(
        [
            "---",
            "",
            "## 6. Multi-Network Performance Figures (Fig. 1 – Fig. 6)",
            "",
            "Each figure presents three side-by-side subplots corresponding to **(a) Network-1 (50 Nodes, 5 Servers)**, **(b) Network-2 (150 Nodes, 15 Servers)**, and **(c) Network-3 (300 Nodes, 30 Servers)**.",
            "",
        ]
    )

    figure_titles = [
        "Fig. 1: Utility Value vs. Workload",
        "Fig. 2: Jain's Fairness Index vs. Workload",
        "Fig. 3: Load Variance vs. Workload",
        "Fig. 4: Convergence Time vs. Workload",
        "Fig. 5: Throughput vs. Workload",
        "Fig. 6: Response Time vs. Workload",
    ]

    for title, fpath in zip(figure_titles, figure_paths):
        rel_path = fpath.replace("\\", "/")
        md_lines.extend(
            [
                f"### {title}",
                f"![{title}]({rel_path})",
                "",
            ]
        )

    md_lines.extend(
        [
            "---",
            "",
            "## 7. Methodological Notes & Interpretation Cautions",
            "",
            "- **Pooled vs. Condition-Specific Means**: Overall summary tables aggregate across three network scales (`N1`, `N2`, `N3`), three workload intensities (`1,250`, `3,000`, `5,000`), and three priority profiles (`T1`, `T2`, `T3`). Condition-level breakdown tables should be consulted alongside pooled averages when evaluating scale-specific behavior.",
            "- **Paired Experimental Control**: Within every replication, all four policy variants (`A1`, `A2`, `A3`, `Proposed`) receive the exact same generated task batch and initial node resource state initialized from a shared seed, ensuring that observed differences arise strictly from the coordination mechanism.",
            "- **Jain's Fairness & Load Variance**: Both metrics are evaluated over post-allocation composite node resource utilization ($65\\%$ CPU utilization $+ 35\\%$ RAM utilization), reflecting actual hardware balance rather than raw task counts.",
            "- **Independent Equilibrium Auditing**: The reported **Final Nash Gap ($\\downarrow$)** and **Stackelberg Gap ($\\downarrow$)** are computed by independent post-allocation perturbation verifiers rather than solver internal stopping residuals.",
        ]
    )

    with open(md_output_path, "w", encoding="utf-8") as md_file:
        md_file.write("\n".join(md_lines))

    # -------------------- 2. BUILD HTML REPORT --------------------
    css_style = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 36px auto;
            max-width: 1320px;
            line-height: 1.65;
            color: #1f2937;
            background-color: #f8fafc;
            padding: 0 24px;
        }
        h1, h2, h3 {
            color: #0f172a;
        }
        h1 {
            border-bottom: 3px solid #1d4ed8;
            padding-bottom: 12px;
        }
        h2 {
            margin-top: 40px;
            border-bottom: 2px solid #cbd5e1;
            padding-bottom: 6px;
        }
        .card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px 24px;
            margin: 18px 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 14px 0 26px 0;
            background: #ffffff;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
            font-size: 13.5px;
        }
        th, td {
            border: 1px solid #cbd5e1;
            padding: 9px 11px;
            text-align: left;
        }
        th {
            background-color: #1e3a8a;
            color: #ffffff;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background-color: #f1f5f9;
        }
        .figure-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 26px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .figure-box img {
            max-width: 100%;
            height: auto;
        }
    </style>
    """

    html_parts: List[str] = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<title>IoT Edge Game Theory – Restructured Experimental Report</title>",
        css_style,
        "</head>",
        "<body>",
        "<h1>Intra-Node Load Balancing for IoT Edge Computing Using Non-Cooperative Game Theory</h1>",
        "<h2>1. System Architecture &amp; How the Framework Works</h2>",
        "<div class='card'>",
        "<p>This framework models a three-tier IoT Edge Computing architecture (IoT Task Generators, Follower Edge Nodes, and Leader Edge Servers) through five sequential stages:</p>",
        "<ol>",
        "<li><strong>Topology &amp; Workload Generation (<code>generator.py</code>)</strong>: Instantiates <strong>Network-1</strong> (50 nodes, 5 servers), <strong>Network-2</strong> (150 nodes, 15 servers), and <strong>Network-3</strong> (300 nodes, 30 servers) under workloads of <strong>1,250</strong>, <strong>3,000</strong>, and <strong>5,000</strong> tasks across arrival profiles <strong>T1</strong> (urgent telemetry), <strong>T2</strong> (balanced mixed), and <strong>T3</strong> (compute-heavy).</li>",
        "<li><strong>Multi-Attribute Priority Scoring (<code>priority.py</code>)</strong>: Computes a composite priority score <em>S<sub>i</sub> = 0.45&middot;Urgency + 0.35&middot;Criticality + 0.20&middot;ResourceIntensity</em> for every task and classifies each into <strong>P1</strong> (weight 1.60), <strong>P2</strong> (1.25), <strong>P3</strong> (1.00), or <strong>P4</strong> (0.75), yielding an empirical <em>P<sub>1</sub>&ndash;P<sub>4</sub></em> distribution per experiment.</li>",
        "<li><strong>Seven-Rule Resource Filtering (<code>resource_filter.py</code>)</strong>: Enforces Available CPU, RAM, Storage, and Bandwidth sufficiency alongside Estimated Latency &le; 50 ms, Projected CPU Utilization &le; 85%, and Projected RAM Utilization &le; 90%.</li>",
        "<li><strong>Hierarchical Game Coordination (<code>stackelberg.py</code>, <code>nash_mfg.py</code>, <code>hierarchical_game.py</code>)</strong>: Edge servers optimize Stackelberg unit prices while follower nodes compute damped fixed-point Mean-Field Game (MFG) stationary distributions and route tasks via priority-weighted congestion potentials across four policy variants: <strong>A1: MFG only</strong>, <strong>A2: Stackelberg only</strong>, <strong>A3: MFG+Stackelberg</strong>, and <strong>Proposed</strong>.</li>",
        "<li><strong>Queue Execution &amp; Independent Equilibrium Auditing (<code>edge_node.py</code>, <code>metrics.py</code>)</strong>: Tasks execute against real node queue clocks (<code>next_available_time_ms</code>), and post-allocation perturbation verifiers independently compute the <strong>Final Nash Gap (&darr;)</strong> and <strong>Stackelberg Gap (&darr;)</strong>.</li>",
        "</ol>",
        "</div>",
        "<h2>2. Experimental Design &amp; Phase-1 Resource Filtering (27 Configurations)</h2>",
        "<h3>Table 1. Network Configuration and Resource Parameters</h3>",
        phase1_table1.to_html(index=False, border=0),
        "<h3>Table 2. Consolidated Seven-Rule Resource Filtering Viability Across Networks</h3>",
        consolidated_t2.to_html(index=False, border=0),
        "<h3>Table 3. Phase-1 Experimental Configurations (E1–E27) with Observed P1–P4 Distributions</h3>",
        exp27_view.to_html(index=False, border=0),
        "<h2>3. Phase-2 Overall Ablation Results &amp; Statistical Significance</h2>",
        "<h3>Table 4. Overall Performance Comparison Across Six Metrics (Mean &plusmn; SD)</h3>",
        phase2_table1.to_html(index=False, border=0),
        "<h3>Table 5. Statistical Significance Summary (Welch t-test &amp; ANOVA p-values)</h3>",
        phase2_table2.to_html(index=False, border=0),
    ]

    if not paired_stats_df.empty:
        html_parts.extend(
            [
                "<h3>Table 6. Paired Statistical Comparisons (Proposed Minus Baseline with 95% CI &amp; Holm Correction)</h3>",
                paired_stats_df.to_html(index=False, border=0),
            ]
        )

    if not cond_part1.empty and not cond_part2.empty:
        html_parts.extend(
            [
                "<h2>4. Condition-Level Results by Workload and Task Profile</h2>",
                "<h3>Part 1: Utility, Jain's Fairness &amp; Load Variance</h3>",
                cond_part1.to_html(index=False, border=0),
                "<h3>Part 2: Convergence Time, System Throughput &amp; Response Time</h3>",
                cond_part2.to_html(index=False, border=0),
            ]
        )

    html_parts.extend(
        [
            "<h2>5. Equilibrium Ablation &amp; Load-Wise Diagnostics</h2>",
            "<h3>Table 7. Nash and Stackelberg Equilibrium Applicability Structure</h3>",
            equilibrium_checklist.to_html(index=False, border=0),
            "<h3>Table 8. Overall Equilibrium Gap Comparison (Mean &plusmn; SD)</h3>",
            phase2_table3.to_html(index=False, border=0),
        ]
    )

    if not nash_diag_df.empty and not stack_diag_df.empty:
        html_parts.extend(
            [
                "<h3>Table 9. Load-Wise Nash Equilibrium Diagnostics</h3>",
                nash_diag_df.to_html(index=False, border=0),
                "<h3>Table 10. Load-Wise Stackelberg Equilibrium Diagnostics</h3>",
                stack_diag_df.to_html(index=False, border=0),
            ]
        )

    html_parts.append(
        "<h2>6. Multi-Network Performance Figures (Subplots: (a) Network-1, (b) Network-2, (c) Network-3)</h2>"
    )

    for title, fpath in zip(figure_titles, figure_paths):
        rel_path = os.path.relpath(
            fpath, start=os.path.dirname(os.path.abspath(html_output_path))
        ).replace("\\", "/")
        html_parts.extend(
            [
                "<div class='figure-box'>",
                f"<h3>{title}</h3>",
                f"<img src='{rel_path}' alt='{title}'>",
                "</div>",
            ]
        )

    html_parts.extend(
        [
            "<h2>7. Methodological Notes &amp; Interpretation Cautions</h2>",
            "<div class='card'>",
            "<ul>",
            "<li><strong>Pooled vs. Condition-Specific Means</strong>: Overall summary tables combine three network sizes, three load levels, and three priority profiles. Condition-level tables should be interpreted alongside pooled results.</li>",
            "<li><strong>Matched Environmental Seeds</strong>: Within each replication, all four policy variants observe the exact same task batch and initial node capacities.</li>",
            "<li><strong>Utilization-Based Fairness</strong>: Jain's Fairness and Load Variance measure composite post-allocation hardware utilization (65% CPU + 35% RAM) across edge nodes.</li>",
            "<li><strong>Independent Equilibrium Verification</strong>: Final Nash Gap and Stackelberg Gap are evaluated by post-allocation perturbation audits, leaving inapplicable solver components as <code>N/A</code>.</li>",
            "</ul>",
            "</div>",
            "</body>",
            "</html>",
        ]
    )

    with open(html_output_path, "w", encoding="utf-8") as html_file:
        html_file.write("\n".join(html_parts))