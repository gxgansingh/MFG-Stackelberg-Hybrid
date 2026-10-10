from config.experiment_config import OUTPUT_ROOT
from .experiments.network1_experiment import run_network1
from .experiments.report import generate_report
from .experiments.statistical_analysis import run_statistics
from .experiments.visualization import generate_figures, generate_filtering_figure


def main():
    frames = run_network1()
    statistics_dir = OUTPUT_ROOT / "statistics"
    figures_dir = OUTPUT_ROOT / "figures"
    report_dir = OUTPUT_ROOT / "report"
    tables = run_statistics(frames["runs"], statistics_dir)
    generate_figures(frames["runs"], figures_dir)
    generate_filtering_figure(frames["filtering"], figures_dir)
    generate_report(
        frames["runs"],
        tables["mean_sd_by_load"],
        tables["equilibrium_statistics"],
        frames["filtering"],
        report_dir / "network1_results.md",
    )
    print(f"Network-1 experiment completed. Results: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
