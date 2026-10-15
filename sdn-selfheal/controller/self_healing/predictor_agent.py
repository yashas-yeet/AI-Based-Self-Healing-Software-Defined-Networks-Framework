"""
Real-time AI Inference Agent for Failure Prediction.
Maintains sliding temporal telemetry buffers, invokes trained ML models,
and executes hysteresis and hold-down timers to avoid route flapping.
"""

import time
import numpy as np
from typing import Dict, Tuple, Optional, Any, List
from telemetry.feature_pipeline import TelemetryFeaturePipeline

class PredictorAgent:
    """
    Manages online model inference and cooldown damping.
    """
    def __init__(
        self,
        model=None,
        scaler=None,
        alarm_threshold: float = 0.70,
        cooldown_sec: float = 15.0,
        window_size: int = 5
    ):
        self.model = model
        self.scaler = scaler
        self.alarm_threshold = alarm_threshold
        self.cooldown_sec = cooldown_sec
        self.window_size = window_size

        self.pipeline = TelemetryFeaturePipeline(window_size=window_size)
        # (u, v) -> latest failure probability P_fail in [0, 1]
        self.latest_predictions: Dict[Tuple[int, int], float] = {}
        # (u, v) -> timestamp of last alarm trigger (for hysteresis)
        self.last_alarm_time: Dict[Tuple[int, int], float] = {}

    def update_telemetry(self, u: int, v: int, raw_metrics: Dict[str, float]) -> Tuple[float, bool]:
        """
        Processes new 1-second telemetry for link (u, v).
        Returns: (p_fail, should_trigger_alarm)
        """
        features = self.pipeline.process_link_observation(u, v, raw_metrics)
        now = raw_metrics.get("timestamp", time.time())
        key = (u, v)

        # Predict failure probability
        p_fail = self._run_inference(key, features)
        self.latest_predictions[key] = p_fail

        # Hysteresis & cooldown check
        last_alarm = self.last_alarm_time.get(key, 0.0)
        in_cooldown = (now - last_alarm) < self.cooldown_sec

        should_trigger = False
        if p_fail >= self.alarm_threshold:
            if not in_cooldown:
                self.last_alarm_time[key] = now
                should_trigger = True

        return p_fail, should_trigger

    def _run_inference(self, link_key: Tuple[int, int], latest_features: Dict[str, float]) -> float:
        """Runs model inference if model exists, or evaluates rule-based trend heuristic fallback."""
        if self.model is not None:
            try:
                # If PyTorch model or Scikit-Learn model
                buf = self.pipeline.buffers.get(link_key)
                if not buf or len(buf.history) < self.window_size:
                    return 0.0

                from ml.dataset import FEATURE_COLUMNS
                seq = []
                for rec in buf.history:
                    f_vec = [rec.get(c, 0.0) for c in FEATURE_COLUMNS]
                    seq.append(f_vec)
                seq_np = np.array(seq, dtype=np.float32)

                if self.scaler is not None:
                    seq_np = self.scaler.transform(seq_np)

                # Sequential inference
                if hasattr(self.model, "predict_proba"):
                    # Tabular model: flatten
                    flat = seq_np.flatten().reshape(1, -1)
                    return float(self.model.predict_proba(flat)[0])
                else:
                    # PyTorch tensor
                    import torch
                    with torch.no_grad():
                        t_in = torch.tensor(seq_np).unsqueeze(0)
                        out = self.model(t_in)
                        return float(out.item())
            except Exception as e:
                pass

        # Robust heuristic fallback: evaluates rapid growth in drop slope and RTT slope
        drop_slope = latest_features.get("drop_rate_slope_w", 0.0)
        rtt_slope = latest_features.get("rtt_slope_w", 0.0)
        drop_ratio = latest_features.get("drop_ratio", 0.0)

        # Escalating degradation pattern
        score = 0.0
        if drop_slope > 2.0 or drop_ratio > 0.02:
            score += 0.5
        if rtt_slope > 1.5:
            score += 0.4
        if latest_features.get("rtt_ms", 1.0) > 20.0:
            score += 0.2

        return min(1.0, max(0.0, score))

    def get_prediction(self, u: int, v: int) -> float:
        return self.latest_predictions.get((u, v), 0.0)
