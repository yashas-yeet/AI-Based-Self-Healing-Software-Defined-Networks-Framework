#!/usr/bin/env python3
"""Compute breakdown tables across topologies, controllers, faults, and loads."""
import os
import sys
import pandas as pd

def main():
    csv_path = "results/processed/experiment_matrix_results.csv"
    df = pd.read_csv(csv_path)

    print("=== SUMMARY METRICS BY CONTROLLER ===")
    summary = df.groupby("controller")[["recovery_time_ms", "packet_loss_pct", "mean_throughput_failover_mbps", "lead_time_sec", "control_plane_flow_mods"]].agg(["mean", "std"])
    print(summary.to_string())

    print("\n=== RECOVERY TIME (ms) BY CONTROLLER & TOPOLOGY ===")
    piv_topo_rec = df.pivot_table(index="controller", columns="topology", values="recovery_time_ms", aggfunc="mean")
    print(piv_topo_rec.to_string())

    print("\n=== PACKET LOSS (%) BY CONTROLLER & TOPOLOGY ===")
    piv_topo_loss = df.pivot_table(index="controller", columns="topology", values="packet_loss_pct", aggfunc="mean")
    print(piv_topo_loss.to_string())

    print("\n=== RECOVERY TIME (ms) BY CONTROLLER & FAULT TYPE ===")
    piv_fault_rec = df.pivot_table(index="controller", columns="failure_type", values="recovery_time_ms", aggfunc="mean")
    print(piv_fault_rec.to_string())

    print("\n=== PACKET LOSS (%) BY CONTROLLER & FAULT TYPE ===")
    piv_fault_loss = df.pivot_table(index="controller", columns="failure_type", values="packet_loss_pct", aggfunc="mean")
    print(piv_fault_loss.to_string())

    print("\n=== FAILURE LEAD TIME (s) BY CONTROLLER ===")
    lead = df.groupby("controller")["lead_time_sec"].agg(["mean", "min", "max"])
    print(lead.to_string())

if __name__ == "__main__":
    main()
