"""
Statistical Significance Testing for SDN Self-Healing Validation.
Performs paired t-tests, non-parametric Wilcoxon signed-rank tests,
and computes effect sizes (Cohen's d) and 95% Confidence Intervals.
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Tuple

def compute_summary_stats(series: np.ndarray) -> Dict[str, float]:
    """Computes mean, std, and 95% Confidence Interval."""
    n = len(series)
    mean = float(np.mean(series))
    std = float(np.std(series, ddof=1)) if n > 1 else 0.0
    se = std / np.sqrt(n) if n > 1 else 0.0
    ci95 = float(stats.t.ppf(0.975, df=max(1, n - 1)) * se) if n > 1 else 0.0

    return {
        "mean": mean,
        "std": std,
        "ci95": ci95,
        "min": float(np.min(series)),
        "max": float(np.max(series))
    }

def compare_methods(
    m_series: np.ndarray,
    baseline_series: np.ndarray
) -> Dict[str, Any]:
    """
    Computes statistical hypothesis tests comparing Method M vs Baseline:
    1. Paired Student's t-test
    2. Wilcoxon signed-rank test
    3. Cohen's d effect size
    """
    m_stats = compute_summary_stats(m_series)
    b_stats = compute_summary_stats(baseline_series)

    # Paired t-test
    t_stat, p_ttest = stats.ttest_rel(m_series, baseline_series)

    # Wilcoxon signed-rank test
    try:
        w_stat, p_wilcoxon = stats.wilcoxon(m_series, baseline_series)
    except Exception:
        w_stat, p_wilcoxon = 0.0, 1.0

    # Cohen's d: (mean_M - mean_B) / pooled_std
    n1, n2 = len(m_series), len(baseline_series)
    s1, s2 = m_stats["std"], b_stats["std"]
    pooled_std = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / max(1, n1 + n2 - 2))
    cohens_d = float((m_stats["mean"] - b_stats["mean"]) / max(1e-6, pooled_std))

    return {
        "method_M": m_stats,
        "baseline": b_stats,
        "t_stat": float(t_stat),
        "p_value_ttest": float(p_ttest),
        "wilcoxon_stat": float(w_stat),
        "p_value_wilcoxon": float(p_wilcoxon),
        "cohens_d": cohens_d,
        "statistically_significant_p05": bool(p_wilcoxon < 0.05)
    }

def generate_statistical_report(results_csv: str, output_path: str = "results/processed/statistical_report.md"):
    """Loads experimental results CSV and generates formatted Markdown report."""
    df = pd.read_csv(results_csv)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    metrics = ["packet_loss_pct", "recovery_time_ms", "mean_throughput_failover_mbps"]
    baselines = ["B1", "B2", "B3", "B4"]

    lines = ["# Statistical Significance & Comparative Benchmark Report\n"]
    lines.append("| Metric | Baseline | Mean (M) | Mean (Baseline) | Diff (%) | Wilcoxon p-value | Cohen's d | Significant (p < 0.05) |")
    lines.append("|:---|:---|:---|:---|:---|:---|:---|:---|")

    for metric in metrics:
        m_vals = df[df["controller"] == "M"][metric].values
        if len(m_vals) == 0:
            continue
        for b in baselines:
            b_vals = df[df["controller"] == b][metric].values
            if len(b_vals) == 0:
                continue
            comp = compare_methods(m_vals, b_vals)
            diff_pct = ((comp["method_M"]["mean"] - comp["baseline"]["mean"]) / max(1e-4, comp["baseline"]["mean"])) * 100.0
            sig = "YES (p < 0.05)" if comp["statistically_significant_p05"] else "NO"
            lines.append(
                f"| `{metric}` | **{b}** | {comp['method_M']['mean']:.2f} ± {comp['method_M']['ci95']:.2f} | "
                f"{comp['baseline']['mean']:.2f} ± {comp['baseline']['ci95']:.2f} | {diff_pct:+.1f}% | "
                f"{comp['p_value_wilcoxon']:.4e} | {comp['cohens_d']:.2f} | {sig} |"
            )

    report_content = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(report_content)
    print(f"[STATISTICS] Report successfully generated at {output_path}")
    return report_content
