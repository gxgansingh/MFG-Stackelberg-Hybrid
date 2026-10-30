"""
Automated report generation module.
Compiles Phase-1 and Phase-2 experimental tables and embeds the 6 three-subplot
performance figures into publication-ready Markdown (report.md) and HTML (report.html) files.
"""

import os
from typing import Dict, List
import pandas as pd


def _df_to_markdown_table(df: pd.DataFrame) -> str:
    """Convert a pandas DataFrame into a GitHub-flavored Markdown table without extra dependencies."""
    headers = [str(col) for col in df.columns]
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"

    body_lines: List[str] = []
    for _, row in df.iterrows():
        cells = [str(val) for val in row.values]
        body_lines.append("| " + " | ".join(cells) + " |")

    return "\n".join([header_line, separator_line] + body_lines)


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
) -> None:
    """
    Generate both `report.md` and `report.html` containing all Phase-1 and Phase-2
    tables and the 6 performance figures.
    """
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

    # -------------------- 1. BUILD MARKDOWN REPORT --------------------
    md_lines: List[str] = [
        "# Experimental Report",
        "",
        "## Phase-1: Network Configuration, Resource Filtering & 27 Experimental Configurations",
        "",
        "### Table 1. Network Configuration and Resource Parameters",
        "",
        _df_to_markdown_table(phase1_table1),
        "",
        "### Table 2. Filtering Decisions Across Workloads (1,250, 3,000, and 5,000 Tasks)",
        "",
    ]

    for net_code, t2_df in phase1_table2_by_net.items():
        md_lines.extend(
            [
                f"#### Network {net_code}",
                "",
                _df_to_markdown_table(t2_df),
                "",
            ]
        )

    md_lines.extend(
        [
            "### Proposed Experimental Configuration – 27 Experiments (Observed P1–P4 Distributions)",
            "",
            _df_to_markdown_table(exp27_view),
            "",
            "---",
            "",
            "## Phase-2: Statistical Analysis, Equilibrium Ablation & Performance Visualization",
            "",
            "### Phase-2 Table-1: Performance Comparison Across Six Metrics (Mean ± SD)",
            "",
            _df_to_markdown_table(phase2_table1),
            "",
            "### Phase-2 Table-2: Statistical Significance (Welch Two-Sample t-test & One-Way ANOVA p-values)",
            "",
            _df_to_markdown_table(phase2_table2),
            "",
            "### Nash and Stackelberg Equilibrium Ablation Applicability",
            "",
            _df_to_markdown_table(equilibrium_checklist),
            "",
            "### Phase-2 Table-3: Final Nash Gap and Stackelberg Gap (Mean ± SD)",
            "",
            _df_to_markdown_table(phase2_table3),
            "",
            "---",
            "",
            "## Performance Figures (3 Networks × Workloads × 4 Methods × 9 Runs)",
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

    with open(md_output_path, "w", encoding="utf-8") as md_file:
        md_file.write("\n".join(md_lines))

    # -------------------- 2. BUILD HTML REPORT --------------------
    css_style = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px auto;
            max-width: 1280px;
            line-height: 1.6;
            color: #1f2937;
            background-color: #f9fafb;
            padding: 0 20px;
        }
        h1, h2, h3, h4 {
            color: #111827;
        }
        h1 {
            border-bottom: 3px solid #2563eb;
            padding-bottom: 10px;
        }
        h2 {
            margin-top: 36px;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 6px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0 28px 0;
            background: #ffffff;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            font-size: 14px;
        }
        th, td {
            border: 1px solid #d1d5db;
            padding: 10px 12px;
            text-align: left;
        }
        th {
            background-color: #1e3a8a;
            color: #ffffff;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background-color: #f3f4f6;
        }
        .figure-box {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 28px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
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
        "<title>IoT Edge Game Theory Experimental Report</title>",
        css_style,
        "</head>",
        "<body>",
        "<h1>Experimental Report: Intra-Node Load Balancing for IoT Edge Computing Using Non-Cooperative Game Theory</h1>",
        "<h2>Phase-1: Network Configuration, Resource Filtering &amp; 27 Experimental Configurations</h2>",
        "<h3>Table 1. Network Configuration and Resource Parameters</h3>",
        phase1_table1.to_html(index=False, border=0),
        "<h3>Table 2. Filtering Decisions Across Workloads (1,250, 3,000, and 5,000 Tasks)</h3>",
    ]

    for net_code, t2_df in phase1_table2_by_net.items():
        html_parts.append(f"<h4>Network {net_code}</h4>")
        html_parts.append(t2_df.to_html(index=False, border=0))

    html_parts.extend(
        [
            "<h3>Proposed Experimental Configuration – 27 Experiments (Observed P1–P4 Distributions)</h3>",
            exp27_view.to_html(index=False, border=0),
            "<h2>Phase-2: Statistical Analysis, Equilibrium Ablation &amp; Performance Visualization</h2>",
            "<h3>Phase-2 Table-1: Performance Comparison Across Six Metrics (Mean &plusmn; SD)</h3>",
            phase2_table1.to_html(index=False, border=0),
            "<h3>Phase-2 Table-2: Statistical Significance (Welch Two-Sample t-test &amp; One-Way ANOVA p-values)</h3>",
            phase2_table2.to_html(index=False, border=0),
            "<h3>Nash and Stackelberg Equilibrium Ablation Applicability</h3>",
            equilibrium_checklist.to_html(index=False, border=0),
            "<h3>Phase-2 Table-3: Final Nash Gap and Stackelberg Gap (Mean &plusmn; SD)</h3>",
            phase2_table3.to_html(index=False, border=0),
            "<h2>Performance Figures (Subplots: (a) Network-1, (b) Network-2, (c) Network-3)</h2>",
        ]
    )

    for title, fpath in zip(figure_titles, figure_paths):
        rel_path = os.path.relpath(fpath, start=os.path.dirname(os.path.abspath(html_output_path))).replace("\\", "/")
        html_parts.extend(
            [
                "<div class='figure-box'>",
                f"<h3>{title}</h3>",
                f"<img src='{rel_path}' alt='{title}'>",
                "</div>",
            ]
        )

    html_parts.extend(["</body>", "</html>"])

    with open(html_output_path, "w", encoding="utf-8") as html_file:
        html_file.write("\n".join(html_parts))