#!/usr/bin/env python3
"""
Phase 6 Smoke Test: End-to-End Experimental Pipeline & Analysis Verification
Runs a mini-matrix of scenarios, verifies statistical report generation, and generates publication plots.
"""

import sys
import os
import glob
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from experiments.scenario_runner import ScenarioRunner
from analysis.statistical_tests import generate_statistical_report
from analysis.plot_generator import generate_all_plots

def test_pipeline_execution():
    print("[TEST] Running end-to-end mini-matrix (M vs B1 vs B2 across 3 seeds)...")
    results = []
    seeds = [42, 101, 2024]
    controllers = ["M", "B1", "B2", "B3", "B4"]

    for ctrl in controllers:
        for seed in seeds:
            runner = ScenarioRunner(
                topology_name="mesh",
                controller_type=ctrl,
                failure_type="gradual",
                traffic_load="medium",
                seed=seed,
                duration_sec=20.0,
                output_dir="results/raw"
            )
            res = runner.run_simulation()
            results.append(res)

    df = pd.DataFrame(results)
    csv_path = "results/processed/test_pipeline_results.csv"
    os.makedirs("results/processed", exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"[PASS] Mini-matrix generated {len(df)} trials saved to {csv_path}")

    # Validate data integrity
    assert not df.isnull().values.any(), "Result dataset must not contain null values"
    assert (df["packet_loss_pct"] >= 0.0).all(), "Packet loss percentage must be non-negative"

    # Verify statistical testing
    print("[TEST] Generating statistical significance report...")
    report = generate_statistical_report(csv_path, "results/processed/test_stat_report.md")
    assert os.path.exists("results/processed/test_stat_report.md"), "Statistical report file must exist"
    print("[PASS] Statistical significance report generated.")

    # Verify plot generation
    print("[TEST] Generating publication-quality figures...")
    generate_all_plots(csv_path)

    for fig in ["fig1_recovery_time_cdf.png", "fig2_loss_boxplots.png", "fig3_failover_timeseries.png"]:
        path = os.path.join("results/figures", fig)
        assert os.path.exists(path), f"Figure {fig} must exist"
        assert os.path.getsize(path) > 1000, f"Figure {fig} must not be empty"
        print(f"[PASS] Verified figure: {fig} ({os.path.getsize(path)} bytes)")

    return True

def main():
    print("=" * 60)
    print("PHASE 6 PIPELINE & ANALYSIS VERIFICATION")
    print("=" * 60)
    
    passed = test_pipeline_execution()
    if not passed:
        print("\n[RESULT] Phase 6 pipeline checks failed.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] PHASE 6 PIPELINE ACCEPTANCE CHECKS PASSED!")
    print("=" * 60)
    sys.exit(0)

if __name__ == "__main__":
    main()
