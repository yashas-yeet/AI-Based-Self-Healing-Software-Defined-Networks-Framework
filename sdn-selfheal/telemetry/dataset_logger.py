"""
Telemetry Dataset Logger for AI Model Training.
Aligns real-time streaming link telemetry with injected failure events and tags data
with forward-looking binary failure labels (failure within next H seconds).
"""

import os
import time
import pandas as pd
from typing import Dict, List, Optional, Tuple

class DatasetLogger:
    """
    Logs labeled telemetry samples to CSV for offline training and evaluation.
    """
    def __init__(self, output_dir: str = "results/raw", horizon_sec: float = 10.0):
        self.output_dir = output_dir
        self.horizon_sec = horizon_sec
        os.makedirs(output_dir, exist_ok=True)
        self.records: List[Dict[str, Any]] = []
        # (src_dpid, dst_dpid) -> list of future failure timestamps
        self.scheduled_failures: Dict[Tuple[int, int], List[float]] = {}

    def register_future_failure(self, src_dpid: int, dst_dpid: int, failure_time: float):
        """Notifies the logger of an impending ground-truth failure timestamp for labeling."""
        key = (src_dpid, dst_dpid)
        if key not in self.scheduled_failures:
            self.scheduled_failures[key] = []
        self.scheduled_failures[key].append(failure_time)

    def log_sample(self, src_dpid: int, dst_dpid: int, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Tags sample with label_H = 1 if a failure occurs within (t, t + horizon_sec], else 0.
        """
        now = features.get("timestamp", time.time())
        key = (src_dpid, dst_dpid)
        future_times = self.scheduled_failures.get(key, [])

        # Check if any failure occurs within [now, now + horizon_sec]
        label = 0
        time_to_fail = -1.0
        for f_time in future_times:
            if 0 <= (f_time - now) <= self.horizon_sec:
                label = 1
                time_to_fail = f_time - now
                break

        row = dict(features)
        row["src_dpid"] = src_dpid
        row["dst_dpid"] = dst_dpid
        row["label"] = label
        row["time_to_fail"] = time_to_fail
        row["horizon_sec"] = self.horizon_sec

        self.records.append(row)
        return row

    def save_to_csv(self, filename: Optional[str] = None) -> str:
        """Saves accumulated samples to CSV file and returns path."""
        if not filename:
            filename = f"telemetry_run_{int(time.time())}.csv"
        path = os.path.join(self.output_dir, filename)
        df = pd.DataFrame(self.records)
        df.to_csv(path, index=False)
        print(f"[DATASET-LOGGER] Saved {len(df)} samples ({df['label'].sum()} positive labels) to {path}")
        return path

    def clear(self):
        self.records.clear()
        self.scheduled_failures.clear()
