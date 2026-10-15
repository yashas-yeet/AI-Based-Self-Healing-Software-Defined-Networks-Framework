"""
Automated Experimental Matrix Runner for Self-Healing SDN.
Executes multi-run factorial experiments across Topologies, Controllers, Failure Modes, and Loads.
Supports full scientific matrix (>= 10 seeds) and fast verification mode (--quick).
"""

import os
import sys
import argparse
import pandas as pd
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from experiments.scenario_runner import ScenarioRunner

SEEDS = [42, 101, 2024, 3051, 4096, 5112, 6001, 7234, 8888, 9999]

def execute_matrix(
    topologies: List[str],
    controllers: List[str],
    failures: List[str],
    loads: List[str],
    seeds: List[int],
    output_dir: str = "results/raw"
) -> pd.DataFrame:
    total_runs = len(topologies) * len(controllers) * len(failures) * len(loads) * len(seeds)
    print("=" * 70)
    print(f"[EXPERIMENT MATRIX] Initiating {total_runs} Experimental Trials")
    print(f"Topologies: {topologies}")
    print(f"Controllers: {controllers}")
    print(f"Failures: {failures}")
    print(f"Loads: {loads}")
    print(f"Seeds: {len(seeds)} trials per condition")
    print("=" * 70)

    results = []
    run_idx = 0

    for topo in topologies:
        for fault in failures:
            for load in loads:
                for ctrl in controllers:
                    for seed in seeds:
                        run_idx += 1
                        print(f"[{run_idx:03d}/{total_runs:03d}] Running: Topo={topo}, Ctrl={ctrl}, Fault={fault}, Load={load}, Seed={seed}")
                        runner = ScenarioRunner(
                            topology_name=topo,
                            controller_type=ctrl,
                            failure_type=fault,
                            traffic_load=load,
                            seed=seed,
                            duration_sec=30.0,
                            output_dir=output_dir
                        )
                        res = runner.run_simulation()
                        results.append(res)

    df = pd.DataFrame(results)
    summary_path = os.path.join("results/processed", "experiment_matrix_results.csv")
    os.makedirs("results/processed", exist_ok=True)
    df.to_csv(summary_path, index=False)
    print(f"\n[MATRIX COMPLETED] Aggregated results saved to {summary_path}")
    return df

def main():
    parser = argparse.ArgumentParser(description="SDN Self-Healing Experiment Matrix")
    parser.add_argument("--quick", action="store_true", help="Run fast verification subset")
    parser.add_argument("--seeds", type=int, default=10, help="Number of seeds to run")
    args = parser.parse_args()

    if args.quick:
        # Fast subset: 2 seeds, mesh & wan, all controllers, gradual & hard failures
        topos = ["mesh", "wan"]
        ctrls = ["M", "B1", "B2", "B3", "B4"]
        faults = ["gradual", "hard_down"]
        loads = ["medium"]
        seeds = SEEDS[:2]
    else:
        # Full scientific benchmark matrix
        topos = ["mesh", "fattree", "wan"]
        ctrls = ["M", "B1", "B2", "B3", "B4"]
        faults = ["gradual", "hard_down", "flapping", "congestion"]
        loads = ["light", "medium", "heavy"]
        seeds = SEEDS[:args.seeds]

    execute_matrix(topos, ctrls, faults, loads, seeds)

if __name__ == "__main__":
    main()
