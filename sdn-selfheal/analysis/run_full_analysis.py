import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from analysis.statistical_tests import generate_statistical_report
from analysis.plot_generator import generate_all_plots

def main():
    csv_path = "results/processed/experiment_matrix_results.csv"
    report_path = "results/processed/statistical_report.md"

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} trials from {csv_path}.")
    print("Generating comprehensive statistical report...")
    generate_statistical_report(csv_path, report_path)
    print(f"Report saved to {report_path}.")

    print("Generating publication figures...")
    generate_all_plots(csv_path)
    print("All plots generated in results/figures/.")

if __name__ == "__main__":
    main()
