"""
Evaluation Pipeline for Network Failure Predictors.
Evaluates Precision, Recall, F1, ROC-AUC, PR-AUC, False Alarm Rate,
and the operational Prediction Lead Time distribution (T_lead = T_actual - T_alarm).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)

def evaluate_predictions(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    threshold: float = 0.5
) -> Dict[str, float]:
    """Computes comprehensive classification metrics."""
    y_pred = (y_probs >= threshold).astype(int)

    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    # ROC and PR AUC
    has_both_classes = len(np.unique(y_true)) > 1
    roc = roc_auc_score(y_true, y_probs) if has_both_classes else 0.5
    pr_auc = average_precision_score(y_true, y_probs) if has_both_classes else 0.0

    # False Alarm Rate = FP / (FP + TN)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    far = fp / max(1, fp + tn)

    return {
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "roc_auc": float(roc),
        "pr_auc": float(pr_auc),
        "false_alarm_rate": float(far),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn)
    }

def compute_lead_times(
    timestamps: np.ndarray,
    y_true: np.ndarray,
    y_probs: np.ndarray,
    failure_timestamp: float,
    threshold: float = 0.5
) -> Dict[str, float]:
    """
    Computes early warning lead time:
    T_lead = T_actual_failure - T_first_alarm (in seconds).
    """
    alarm_mask = (y_probs >= threshold) & (timestamps <= failure_timestamp)
    if not np.any(alarm_mask):
        return {
            "lead_time_sec": 0.0,
            "detected_early": False,
            "first_alarm_time": None
        }

    first_alarm_t = float(timestamps[alarm_mask][0])
    lead_time = max(0.0, failure_timestamp - first_alarm_t)

    return {
        "lead_time_sec": lead_time,
        "detected_early": True,
        "first_alarm_time": first_alarm_t
    }
