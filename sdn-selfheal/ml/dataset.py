"""
ML Dataset Pipeline for Network Failure Prediction.
Performs leak-free temporal splitting, sliding window sequencing, and feature scaling.
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "rtt_ms", "jitter_ms", "tx_bps", "rx_bps", "tx_pps", "rx_pps",
    "tx_drops_sec", "tx_errors_sec", "drop_ratio", "utilization",
    "ewma_rtt_ms", "ewma_drop_rate",
    "rtt_mean_w", "rtt_std_w", "rtt_slope_w",
    "drop_rate_mean_w", "drop_rate_std_w", "drop_rate_slope_w",
    "util_mean_w", "util_slope_w"
]

class TemporalDataset:
    def __init__(self, window_size: int = 5, feature_cols: Optional[List[str]] = None):
        self.window_size = window_size
        self.feature_cols = feature_cols or FEATURE_COLUMNS
        self.scaler = StandardScaler()

    def prepare_data(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Splits data chronologically to ensure zero lookahead data leakage.
        Returns (X_train, y_train, X_val, y_val, X_test, y_test).
        Shapes: X is (N, window_size, num_features), y is (N,) binary labels.
        """
        # Sort chronologically
        df = df.sort_values(by="timestamp").reset_index(drop=True)
        
        # Ensure all required features are present
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = 0.0
                
        df[self.feature_cols] = df[self.feature_cols].fillna(0.0)

        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        df_train = df.iloc[:train_end]
        df_val = df.iloc[train_end:val_end]
        df_test = df.iloc[val_end:]

        # Fit scaler strictly on training split
        self.scaler.fit(df_train[self.feature_cols].values)

        X_train, y_train = self._create_windows(df_train)
        X_val, y_val = self._create_windows(df_val)
        X_test, y_test = self._create_windows(df_test)

        return X_train, y_train, X_val, y_val, X_test, y_test

    def _create_windows(self, sub_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        scaled_features = self.scaler.transform(sub_df[self.feature_cols].values)
        labels = sub_df["label"].values

        X, y = [], []
        # Group by link if multiple links are present, or slide across contiguous series
        n_samples = len(sub_df)
        if n_samples < self.window_size:
            return np.empty((0, self.window_size, len(self.feature_cols))), np.empty((0,))

        for i in range(self.window_size, n_samples + 1):
            window = scaled_features[i - self.window_size : i]
            target = labels[i - 1]
            X.append(window)
            y.append(target)

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.int64)

    def flatten_for_trees(self, X: np.ndarray) -> np.ndarray:
        """Flattens 3D temporal sequence (N, W, F) to 2D tabular (N, W * F) for Random Forest / XGBoost."""
        if X.ndim == 3:
            N, W, F = X.shape
            return X.reshape(N, W * F)
        return X
