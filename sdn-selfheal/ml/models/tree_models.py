"""
Tree-Based Ensemble Models for Network Failure Prediction.
Includes Random Forest and XGBoost with automated class weighting.
"""

from sklearn.ensemble import RandomForestClassifier
import numpy as np
from typing import Optional

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

class RandomForestFailurePredictor:
    def __init__(self, n_estimators: int = 100, max_depth: int = 8, random_state: int = 42):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=1
        )

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        probs = self.model.predict_proba(X)
        if probs.shape[1] == 2:
            return probs[:, 1]
        elif probs.shape[1] == 1:
            return np.zeros(len(X))
        return probs

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)

class XGBoostFailurePredictor:
    def __init__(self, n_estimators: int = 100, max_depth: int = 6, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        if not HAS_XGB:
            raise ImportError("xgboost package is not installed.")
        neg_count = max(1, np.sum(y == 0))
        pos_count = max(1, np.sum(y == 1))
        scale_pos_weight = neg_count / pos_count

        self.model = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            scale_pos_weight=scale_pos_weight,
            random_state=self.random_state,
            eval_metric="logloss"
        )
        self.model.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model is not fitted yet.")
        probs = self.model.predict_proba(X)
        if probs.shape[1] == 2:
            return probs[:, 1]
        return probs

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)
