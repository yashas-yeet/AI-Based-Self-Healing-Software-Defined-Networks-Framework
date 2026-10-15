# Research Project Report: Self-Healing SDN

This directory contains the complete publication-ready **LaTeX manuscript**, **BibTeX bibliography**, and **high-resolution vector/raster figures** for our research paper:

> **"Self-Healing Software-Defined Networks Using AI-Based Failure Prediction and Dynamic Make-Before-Break Rerouting"**  
> *Target Publication*: IEEE Transactions on Network and Service Management / IEEE INFOCOM

---

## Directory Layout

```
project report/
├── main.pdf                    # Master 25-Page VIT Research Project Report (Compliant with VIT SCOPE sample)
├── main.tex                    # LaTeX source for the 25-Page VIT Research Project Report
├── main_ieee_transactions.pdf  # IEEE Transactions 2-column manuscript PDF (~869 KB)
├── main_ieee_transactions.tex  # LaTeX source for the IEEE Transactions manuscript
├── main_article.tex            # Universal article class fallback
├── references.bib              # Complete BibTeX citations (2025-2026 SDN literature)
├── compile.ps1                 # One-click Windows PowerShell automated compiler
├── figures/                    # High-resolution experimental figures
│   ├── fig0_architecture_loop.png     # System Architecture & Observe-Decide-Act Telemetry Loop
│   ├── fig1_recovery_time_cdf.png     # Recovery Time CDF across 1,800 trials
│   ├── fig2_loss_boxplots.png         # Packet loss breakdown across fault models
│   └── fig3_failover_timeseries.png   # High-resolution failover throughput timeline
└── README.md                   # Compilation guide & instructions
```

---

## Compilation Instructions

### Option 1: Overleaf (Zero-Install, Recommended)
1. Select all files in this `project report/` folder (`main.tex`, `references.bib`, and the `figures/` subfolder).
2. Compress into a `.zip` file.
3. Open [Overleaf](https://www.overleaf.com), click **New Project** $\to$ **Upload Project**, and upload the `.zip`.
4. Overleaf natively includes `IEEEtran` and compiles `main.tex` into a publication-ready PDF with one click.

---

### Option 2: Local Compilation with TeX Live or MiKTeX
From a terminal or command prompt inside this folder:

```bash
# 1. Compile IEEEtran format:
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Or using latexmk (automated multi-pass):
latexmk -pdf main.tex
```

If your local LaTeX distribution lacks the `IEEEtran` class package, compile the universal fallback:
```bash
pdflatex main_article.tex
bibtex main_article
pdflatex main_article.tex
pdflatex main_article.tex
```

---

## Paper Sections & Content Mapping

- **Section I: Introduction**  
  Derivation of the reactive convergence delay $T_{\text{conv}} = T_{\text{detect}} + T_{\text{notify}} + T_{\text{calc}} + T_{\text{install}}$ and discovery of the OpenFlow 1.3 Fast Failover soft-failure blind spot.
- **Section II: Related Work**  
  Comprehensive review citing Sengendo & Granelli (2026), Troia et al. (2025), and Wu et al. (2026).
- **Section III: System Architecture & Theoretical Framework**  
  Formulation of rolling-window telemetry slope extraction ($\frac{d}{dt}, \frac{d^2}{dt^2}$), the Random Forest sequence predictor, the asymptotic barrier penalty routing cost function $\Phi(P) = (1 - P + \epsilon)^{-1}$, and the two-phase Make-Before-Break (MBB) flow installation invariant.
- **Section IV: Experimental Methodology**  
  Topological models (Mesh, Fat-Tree $k=4$, WAN), failure injection taxonomy (Hard Down, Flapping, Gradual, Congestion), and the 1,800-trial benchmark grid.
- **Section V: Experimental Results & Statistical Analysis**  
  Full empirical tables:
  - **Table I**: Macro-level performance comparison across all 1,800 trials.
  - **Table II**: Paired Wilcoxon signed-rank tests ($p < 10^{-60}$) and Cohen's $d$ effect sizes ($d = -8.59$).
  - **Tables III & IV**: Granular recovery time and packet loss breakdown by failure model.
- **Section VI: Discussion & Engineering Insights**  
  Analysis of the zero packet loss invariant ($T_{\text{lead}} = 9.82\text{ s} \gg T_{\text{MBB}} = 9.80\text{ ms}$), the control-plane overhead trade-off ($12$ vs.\ $2$ flow mods), and the sub-5ms real-time inference latency budget ($3.77$~ms).
- **Section VII: Threats to Validity**  
  Evaluation of internal, external, and construct validity constraints.
- **Section VIII: Conclusion & Future Work**  
  Summary and roadmap for P4 programmable data plane integration.
