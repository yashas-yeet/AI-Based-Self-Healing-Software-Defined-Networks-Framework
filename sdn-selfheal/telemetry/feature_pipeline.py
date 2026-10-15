"""
Feature Pipeline for Network Telemetry.
Maintains temporal sliding windows per link to extract rolling statistical features,
exponentially weighted moving averages (EWMA), and degradation trend slopes.
"""

import numpy as np
from collections import deque
from typing import Dict, List, Optional, Tuple

class LinkFeatureBuffer:
    """
    Sliding window telemetry buffer for a single directional link (src_dpid, dst_dpid).
    """
    def __init__(self, window_size: int = 10, capacity_bps: float = 100e6):
        self.window_size = window_size
        self.capacity_bps = capacity_bps
        self.history = deque(maxlen=window_size)
        self.ewma_rtt: Optional[float] = None
        self.ewma_drop_rate: Optional[float] = None
        self.alpha = 0.3  # EWMA smoothing factor

    def push(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Pushes a new 1-second telemetry observation and returns the augmented feature vector.
        """
        now = metrics.get("timestamp", 0.0)
        rtt = metrics.get("rtt_ms", 1.0)
        tx_bps = metrics.get("tx_bps", 0.0)
        rx_bps = metrics.get("rx_bps", 0.0)
        tx_pps = metrics.get("tx_pps", 0.0)
        rx_pps = metrics.get("rx_pps", 0.0)
        drops_sec = metrics.get("tx_drops_sec", 0.0)
        errors_sec = metrics.get("tx_errors_sec", 0.0)
        drop_ratio = metrics.get("drop_ratio", 0.0)
        utilization = min(1.0, max(0.0, tx_bps / self.capacity_bps))

        # Update EWMA
        if self.ewma_rtt is None:
            self.ewma_rtt = rtt
            self.ewma_drop_rate = drops_sec
            jitter = 0.0
        else:
            jitter = abs(rtt - self.history[-1]["rtt_ms"])
            self.ewma_rtt = self.alpha * rtt + (1 - self.alpha) * self.ewma_rtt
            self.ewma_drop_rate = self.alpha * drops_sec + (1 - self.alpha) * self.ewma_drop_rate

        record = {
            "timestamp": now,
            "rtt_ms": rtt,
            "jitter_ms": jitter,
            "tx_bps": tx_bps,
            "rx_bps": rx_bps,
            "tx_pps": tx_pps,
            "rx_pps": rx_pps,
            "tx_drops_sec": drops_sec,
            "tx_errors_sec": errors_sec,
            "drop_ratio": drop_ratio,
            "utilization": utilization
        }
        self.history.append(record)

        # Compute rolling window features
        return self._extract_rolling_features(record)

    def _extract_rolling_features(self, current: Dict[str, float]) -> Dict[str, float]:
        features = dict(current)
        features["ewma_rtt_ms"] = self.ewma_rtt or 1.0
        features["ewma_drop_rate"] = self.ewma_drop_rate or 0.0

        n = len(self.history)
        if n < 2:
            features["rtt_mean_w"] = current["rtt_ms"]
            features["rtt_std_w"] = 0.0
            features["rtt_slope_w"] = 0.0
            features["drop_rate_mean_w"] = current["tx_drops_sec"]
            features["drop_rate_std_w"] = 0.0
            features["drop_rate_slope_w"] = 0.0
            features["util_mean_w"] = current["utilization"]
            features["util_slope_w"] = 0.0
            return features

        rtts = [h["rtt_ms"] for h in self.history]
        drops = [h["tx_drops_sec"] for h in self.history]
        utils = [h["utilization"] for h in self.history]

        features["rtt_mean_w"] = float(np.mean(rtts))
        features["rtt_std_w"] = float(np.std(rtts))
        features["drop_rate_mean_w"] = float(np.mean(drops))
        features["drop_rate_std_w"] = float(np.std(drops))
        features["util_mean_w"] = float(np.mean(utils))

        # Linear trend slopes over window: slope = Cov(t, y) / Var(t)
        t = np.arange(n)
        features["rtt_slope_w"] = float(np.polyfit(t, rtts, 1)[0])
        features["drop_rate_slope_w"] = float(np.polyfit(t, drops, 1)[0])
        features["util_slope_w"] = float(np.polyfit(t, utils, 1)[0])

        return features

class TelemetryFeaturePipeline:
    """
    Manages per-link feature buffers for the entire network.
    """
    def __init__(self, window_size: int = 10, default_capacity_bps: float = 100e6):
        self.window_size = window_size
        self.default_capacity_bps = default_capacity_bps
        # (src_dpid, dst_dpid) -> LinkFeatureBuffer
        self.buffers: Dict[Tuple[int, int], LinkFeatureBuffer] = {}

    def process_link_observation(self, src_dpid: int, dst_dpid: int, metrics: Dict[str, float]) -> Dict[str, float]:
        key = (src_dpid, dst_dpid)
        if key not in self.buffers:
            self.buffers[key] = LinkFeatureBuffer(self.window_size, self.default_capacity_bps)
        return self.buffers[key].push(metrics)
