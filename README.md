# AI-Based Self-Healing Software-Defined Networks Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![OpenFlow 1.3](https://img.shields.io/badge/OpenFlow-1.3-orange.svg)](https://opennetworking.org/)
[![Mininet](https://img.shields.io/badge/Mininet-2.3+-green.svg)](http://mininet.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end, experimentally validated research framework for proactive, predictive self-healing in Software-Defined Networks (SDN) combining high-resolution streaming telemetry, temporal machine learning failure forecasting, barrier-penalized path optimization, and zero-loss Make-Before-Break (MBB) flow migration.

---

## 👤 Author

- **Yashas Vishwakarma** ([@yashas-yeet](https://github.com/yashas-yeet))

---

## 📂 Repository Layout

```
.
└── sdn-selfheal/                    # Mininet & Ryu SDN Self-Healing Implementation
    ├── controller/                  # Ryu/OS-Ken OpenFlow 1.3 Controller modules
    │   ├── base_controller.py       # Base OpenFlow 1.3 switch & ARP handling
    │   ├── reactive_controller.py   # Baseline 1: Reactive Dijkstra rerouting
    │   ├── fast_failover_ctrl.py    # Baseline 2: OpenFlow 1.3 Fast Failover groups
    │   ├── threshold_controller.py  # Baseline 3: Dynamic threshold heuristics
    │   ├── static_ml_ctrl.py        # Baseline 4: Non-temporal ML classifier
    │   └── proactive_controller.py  # Proposed: Temporal ML + Risk Barrier + MBB
    ├── ml/                          # Feature extraction & temporal failure prediction
    ├── telemetry/                   # In-band & port stats collector
    ├── topologies/                  # Mesh, Fat-Tree k=4, and WAN B4 topologies
    ├── experiments/                 # Benchmark runners & failure injectors
    ├── analysis/                    # Statistical validation & publication plotting
    ├── Makefile                     # Linux / WSL automated execution targets
    ├── run.ps1 / run.bat            # Windows WSL runners
    └── requirements.txt             # Python dependencies
```

---

## 🔬 Core Innovations & Key Results

1. **Temporal Gradient Failure Forecasting**: Multi-scale feature engineering ($\frac{d}{dt}, \frac{d^2}{dt^2}$, and EMA ratios) predicting soft and hard link failures with an average advance lead time of **9.82 seconds**.
2. **Make-Before-Break (MBB) Zero-Loss Migration**: A dynamic non-linear barrier cost function $\Phi(P) = (1 - P + \epsilon)^{-1}$ steering traffic onto pre-warmed backup paths through atomic downstream rule installation before modifying ingress flows, achieving **0.00% packet loss**.
3. **97.3% Reduction in Failover Latency**: Cuts failover recovery time from $358.45$~ms (Reactive Dijkstra) to **$9.80$~ms** while sustaining line-rate throughput ($49.25$~Mbps).
4. **Exhaustive Empirical Benchmarking**: Validated across a 1,800-trial experimental grid with non-parametric Wilcoxon signed-rank tests ($p < 10^{-60}$) and very large effect sizes (Cohen's $d = -8.59$).

---

## 🚀 Quick Start

Inside Ubuntu / WSL:

```bash
cd sdn-selfheal

# 1. Environment Setup
make setup

# 2. Run Test Suite
make test

# 3. Execute Single Interactive Trial
make run-single

# 4. Run Full Experimental Benchmark Grid
make run-all

# 5. Generate Statistical Analysis & Figures
make analyze
```

---

## 📖 Citation

```bibtex
@article{selfheal_sdn_2026,
  title   = {Self-Healing Software-Defined Networks Using AI-Based Failure Prediction and Dynamic Make-Before-Break Rerouting},
  author  = {Vishwakarma, Yashas},
  journal = {IEEE Transactions on Network and Service Management},
  year    = {2026}
}
```
