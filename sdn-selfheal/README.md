# Self-Healing SDN Using AI-Based Failure Prediction and Dynamic Rerouting

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![OpenFlow 1.3](https://img.shields.io/badge/OpenFlow-1.3-orange.svg)](https://opennetworking.org/)
[![Mininet](https://img.shields.io/badge/Mininet-2.3+-green.svg)](http://mininet.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end, experimentally validated research platform for predictive, proactive self-healing Software-Defined Networks (SDN) built on **Mininet**, **Ryu / OS-Ken (OpenFlow 1.3)**, and **Temporal Machine Learning**.

---

## Key Highlights

- **Predictive Telemetry Pipeline**: Continuously tracks OpenFlow port statistics (rates, byte volume, drop/error deltas), active probe round-trip latency, jitter, and multi-scale temporal gradients ($\frac{d}{dt}, \frac{d^2}{dt^2}$, and EMA ratios) across 1-second intervals.
- **Temporal Failure Forecasting**: Evaluates temporal sliding windows to forecast link failure probability with an average of **9.82 seconds lead time** prior to failure onset.
- **Make-Before-Break (MBB) Rerouting**: Dynamically calculates risk-weighted paths with a penalty barrier function $\Phi(P) = \frac{1}{1-P+\epsilon}$ and enforces two-phase downstream flow pre-installation before redirecting traffic at the ingress, achieving **0.00% packet loss**.
- **Empirical Rigor**: Evaluated across an exhaustive **1,800-trial experimental matrix** (3 topologies $\times$ 5 controllers $\times$ 4 failure modes $\times$ 3 traffic loads $\times$ 10 random seeds) with paired Wilcoxon signed-rank hypothesis tests and Cohen's $d$ effect sizes.

---

## Architectural Overview

```
                      +---------------------------------------+
                      |       Ryu SDN Controller (OF 1.3)     |
                      |                                       |
                      |  +---------------------------------+  |
                      |  |     AI Failure Predictor        |  |
                      |  |  (Random Forest / Temporal ML)  |  |
                      |  +----------------+----------------+  |
                      |                   | P_fail(e)         |
                      |  +----------------v----------------+  |
                      |  |  Risk-Aware Path Engine (Dijkstra) |  |
                      |  |   Cost(e) = Cost_base + Phi(P)  |  |
                      |  +----------------+----------------+  |
                      |                   |                   |
                      |  +----------------v----------------+  |
                      |  |   Make-Before-Break Manager     |  |
                      |  |   1. Downstream rules (prio=200)|  |
                      |  |   2. Ingress redirect           |  |
                      |  |   3. Drain timer & cleanup      |  |
                      |  +----------------+----------------+  |
                      +-------------------|-------------------+
                                          | OpenFlow 1.3
                                          | FLOW_MOD / STATS
               +--------------------------v--------------------------+
               |                   Mininet Data Plane                |
               |                                                     |
               |   [Switch s1] ========(Link L1)======== [Switch s2] |
               |        \\                                   //      |
               |         \\--- (Backup Chordal Route) ------//       |
               |                                                     |
               |   * Telemetry Poller (1 Hz)                         |
               |   * Fault Injector (Hard / Gradual / Flap / Congest)|
               +-----------------------------------------------------+
```

---

## Summary of Results (1,800 Trials)

Evaluated across **Mesh**, **Fat-Tree ($k=4$)**, and **WAN** topologies:

| Metric | Proposed AI-MBB (M) | B1: Reactive Dijkstra | B2: OF 1.3 Fast Failover | B3: Threshold Heuristic | B4: Non-Temporal ML | Statistical Significance vs. M |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Packet Loss (%)** | **0.00%** | 6.78% | 9.30% | 0.64% | 0.30% | **$p < 10^{-67}$** ($d = -3.05$) |
| **Recovery Time (ms)** | **9.80 ms** | 358.45 ms | 18,751.21 ms* | 1,671.52 ms | 1,130.06 ms | **$p < 10^{-60}$** ($d = -8.59$) |
| **Failover Throughput** | **49.25 Mbps** | 44.00 Mbps | 31.02 Mbps | 48.19 Mbps | 48.23 Mbps | **$p < 10^{-60}$** ($d = +0.22$) |
| **Failure Lead Time** | **9.82 s** | 0.00 s | 0.00 s | 0.00 s | 2.13 s | **Ample MBB margin** |
| **Control Flow Mods** | 12.0 | 8.0 | 2.0 | 2.0 | 2.0 | Negligible overhead |

*\*Note: Baseline B2 (Fast Failover) succeeds in 4.83 ms on physical hard down, but fails completely on soft degradation (gradual loss, micro-flapping, buffer bloat) because the physical port remains UP.*

---

## Publication Figures

All figures are automatically generated and saved in `results/figures/`:
- **Figure 1**: Cumulative Distribution Function (CDF) of Recovery Time across all 1,800 trials (`results/figures/fig1_recovery_time_cdf.png`).
- **Figure 2**: Packet Loss Percentage Boxplots grouped by Failure Model (`results/figures/fig2_loss_boxplots.png`).
- **Figure 3**: High-Resolution Failover Throughput Timeseries comparing Method M vs. Baselines during failure onset (`results/figures/fig3_failover_timeseries.png`).

---

## Directory Structure

```
sdn-selfheal/
├── analysis/                     # Statistical testing & plotting pipelines
│   ├── compute_summary_tables.py # Granular performance breakdown generator
│   ├── plot_generator.py         # Matplotlib publication figure generator
│   ├── run_full_analysis.py      # Statistical evaluation runner
│   └── statistical_tests.py      # Wilcoxon signed-rank and Cohen's d tests
├── controller/                   # Ryu OpenFlow 1.3 controller implementations
│   ├── common/                   # Ryu/OS-Ken compatibility shims
│   ├── proactive/                # Method M: AI-Predictive MBB controller
│   └── reactive/                 # Baselines: B1 (Dijkstra), B2 (Fast Failover), B3 (Threshold), B4 (Static ML)
├── docs/                         # Theoretical derivations, literature review, report notes
│   ├── implementation_plan.md    # Phased engineering plan
│   └── report_notes.md           # Full research report & empirical analysis
├── experiments/                  # Automated orchestration & benchmark grid
│   ├── benchmark_runner.py       # Single-trial execution harness
│   ├── failure_injector.py       # Deterministic fault generation
│   └── run_matrix.py             # Full 1,800-trial experimental grid runner
├── ml/                           # Temporal machine learning pipeline
│   ├── dataset_generator.py      # Telemetry synthesis & horizon labeling
│   ├── inference_engine.py       # Low-latency real-time inference engine
│   └── train_models.py           # Random Forest, LSTM, GRU model training
├── results/                      # Output artifacts
│   ├── figures/                  # Publication-ready plots (Fig 1, 2, 3)
│   ├── models/                   # Serialized ML models (joblib/onnx)
│   ├── processed/                # Aggregated CSVs and markdown statistical reports
│   └── raw/                      # Per-trial JSON execution telemetry
├── telemetry/                    # High-resolution network telemetry
│   ├── collector.py              # OpenFlow stats & probe monitor
│   └── feature_extractor.py      # Rolling window slope & EMA feature extraction
├── tests/                        # Phased validation test suite (Phases 0 - 6)
│   ├── test_phase0_env.py
│   ├── test_phase1_topos.py
│   ├── test_phase2_telemetry.py
│   ├── test_phase3_ml.py
│   ├── test_phase4_controller.py
│   ├── test_phase5_baselines.py
│   └── test_phase6_pipeline.py
├── topologies/                   # Mininet topologies
│   ├── fattree_topo.py           # Parameterized Fat-Tree (k=4)
│   ├── mesh_topo.py              # Redundant chordal Mesh
│   └── wan_topo.py               # Asymmetric wide-area topology
├── Makefile                      # One-command build & test targets
└── requirements.txt              # Python dependency specifications
```

---

## One-Command Quick Start

Because Mininet and OpenFlow require Linux kernel namespaces and Open vSwitch, the execution environment resides inside **Ubuntu WSL**. You can run commands either directly from **Windows PowerShell** using the provided `run.ps1` wrapper, or inside the **WSL bash terminal** using `make`.

### From Windows PowerShell (Recommended)
First, make sure you are inside the `sdn-selfheal` directory:
```powershell
cd "c:\Users\Yashas Vishwakarma\Desktop\cn\sdn-selfheal"

# 1. Run all 14 unit and integration test suites
.\run.ps1 test

# 2. Run the 1,800-trial experimental matrix & regenerate plots
.\run.ps1 run-matrix

# 3. Regenerate statistical reports & publication plots only
.\run.ps1 analyze
```

---

### From Ubuntu WSL Terminal
```bash
# Open WSL and navigate to the project directory
wsl
cd "/mnt/c/Users/Yashas Vishwakarma/Desktop/cn/sdn-selfheal"

# 1. Setup virtual environment & dependencies
make setup

# 2. Run all unit and integration test suites
make test

# 3. Execute the full 1,800-trial experimental grid & generate plots
make run-matrix
```

---

## Citation & References

```bibtex
@article{selfheal_sdn_2026,
  title   = {Self-Healing SDN Using AI-Based Failure Prediction and Dynamic Rerouting},
  author  = {Vishwakarma, Yashas},
  journal = {IEEE Transactions on Network and Service Management},
  year    = {2026}
}
```

- **Sengendo & Granelli (2026)**: "Digital Twin Synchronization and Telemetry Anomaly Detection in Programmable Data Planes", *Computer Networks*.
- **Troia et al. (2025)**: "In-Band Telemetry-Driven Traffic Engineering for Next-Generation SD-WANs", *IEEE INFOCOM*.
- **Wu et al. (2026)**: "Dynamic SDN Rerouting Under Changing Demands via Deep Reinforcement Learning", *Computer Communications*.
