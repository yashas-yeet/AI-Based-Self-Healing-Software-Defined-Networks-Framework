# AI-Based Self-Healing Software-Defined Networks Framework

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![OpenFlow 1.3](https://img.shields.io/badge/OpenFlow-1.3-orange.svg)](https://opennetworking.org/)
[![Mininet](https://img.shields.io/badge/Mininet-2.3+-green.svg)](http://mininet.org/)
[![LaTeX: Compiled](https://img.shields.io/badge/LaTeX-PDF%20Ready-brightgreen.svg)](project%20report/main.pdf)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end, experimentally validated research framework for proactive, predictive self-healing in Software-Defined Networks (SDN) combining high-resolution streaming telemetry, temporal machine learning failure forecasting, barrier-penalized path optimization, and zero-loss Make-Before-Break (MBB) flow migration.

---

## 👥 Student Research Project Team

- **Yashas Anand Kumar Vishwakarma** (25BCE2133)
- **Aabha Manishkumar Parikh** (25BDS0307)
- **Mohamed Yusouf Eijaaz M** (25BCE0755)

*School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology (VIT), Vellore, Tamil Nadu, India.*

---

## 📂 Repository Structure

```
.
├── project report/                  # Complete LaTeX manuscripts & compiled publication PDFs
│   ├── main.pdf                     # 25-Page Formal VIT Research Project Report
│   ├── main.tex                     # LaTeX source (VIT SCOPE compliant)
│   ├── main_ieee_transactions.pdf   # IEEE Transactions 2-column manuscript PDF
│   ├── main_ieee_transactions.tex   # LaTeX source for IEEE Transactions
│   ├── main_article.pdf             # Universal article class PDF
│   ├── main_article.tex             # LaTeX source for universal article class
│   ├── references.bib               # Comprehensive 2025-2026 SDN citations
│   ├── compile.ps1                  # One-click Windows PowerShell automated compiler
│   └── figures/                     # Publication-ready vector & raster figures
│       ├── fig0_architecture_loop.png
│       ├── fig1_recovery_time_cdf.png
│       ├── fig2_loss_boxplots.png
│       └── fig3_failover_timeseries.png
│
└── sdn-selfheal/                    # Mininet & Ryu SDN Self-Healing Implementation
    ├── controller/                  # Ryu/OS-Ken OpenFlow 1.3 Controller modules
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

### 1. Research Project Report
To compile the LaTeX reports and manuscripts on Windows:
```powershell
cd "project report"
.\compile.ps1
```

### 2. SDN Self-Healing Framework
Inside Ubuntu / WSL:
```bash
cd sdn-selfheal
make setup
make run-single
```

---

## 📖 Citation

```bibtex
@article{selfheal_sdn_2026,
  title   = {Self-Healing Software-Defined Networks Using AI-Based Failure Prediction and Dynamic Make-Before-Break Rerouting},
  author  = {Vishwakarma, Yashas Anand Kumar and Parikh, Aabha Manishkumar and Eijaaz M, Mohamed Yusouf},
  journal = {IEEE Transactions on Network and Service Management},
  year    = {2026}
}
```
