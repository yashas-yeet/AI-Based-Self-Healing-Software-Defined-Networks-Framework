"""
Training Pipeline for Failure Prediction Models.
Supports Random Forest, XGBoost, and PyTorch LSTM/GRU with class weighting and focal loss.
"""

import os
import argparse
import numpy as np
import pandas as pd
import joblib
from typing import Dict, Any

from ml.dataset import TemporalDataset
from ml.models.temporal_models import FailureLSTM, FailureGRU, FocalLoss
from ml.models.tree_models import RandomForestFailurePredictor, XGBoostFailurePredictor

try:
    import torch
    import torch.optim as optim
    from torch.utils.data import TensorDataset, DataLoader
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def train_tree_model(
    model_type: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray
):
    print(f"[ML-TRAIN] Training {model_type} model on {len(X_train)} samples...")
    if model_type == "rf":
        model = RandomForestFailurePredictor(n_estimators=100, max_depth=8)
    elif model_type == "xgb":
        model = XGBoostFailurePredictor(n_estimators=100, max_depth=6)
    else:
        raise ValueError(f"Unknown tree model: {model_type}")

    model.fit(X_train, y_train)
    val_probs = model.predict_proba(X_val)

    from sklearn.metrics import roc_auc_score, average_precision_score
    roc = roc_auc_score(y_val, val_probs) if len(np.unique(y_val)) > 1 else 0.5
    pr = average_precision_score(y_val, val_probs) if len(np.unique(y_val)) > 1 else 0.0

    print(f"[ML-TRAIN] {model_type.upper()} Validation ROC-AUC: {roc:.4f}, PR-AUC: {pr:.4f}")
    return model

def train_lstm_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 25,
    batch_size: int = 32,
    lr: float = 1e-3
):
    if not HAS_TORCH:
        raise ImportError("PyTorch not installed.")

    print(f"[ML-TRAIN] Training PyTorch LSTM on {len(X_train)} sequential samples (epochs={epochs})...")
    input_dim = X_train.shape[2]
    model = FailureLSTM(input_dim=input_dim, hidden_dim=32, num_layers=2, dropout=0.2)
    criterion = FocalLoss(alpha=0.75, gamma=2.0)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    train_ds = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.float32))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for bx, by in train_loader:
            optimizer.zero_grad()
            preds = model(bx)
            loss = criterion(preds, by)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(bx)

        if epoch % 5 == 0 or epoch == epochs:
            model.eval()
            with torch.no_grad():
                val_preds = model(torch.tensor(X_val, dtype=torch.float32)).numpy()
                from sklearn.metrics import roc_auc_score, average_precision_score
                roc = roc_auc_score(y_val, val_preds) if len(np.unique(y_val)) > 1 else 0.5
                pr = average_precision_score(y_val, val_preds) if len(np.unique(y_val)) > 1 else 0.0
                print(f"Epoch {epoch:02d}/{epochs}: Train Loss={total_loss/len(X_train):.4f}, Val ROC={roc:.4f}, PR={pr:.4f}")

    return model

def main():
    parser = argparse.ArgumentParser(description="Train failure prediction models")
    parser.add_argument("--data", type=str, required=True, help="Path to telemetry CSV")
    parser.add_argument("--model", type=str, default="rf", choices=["rf", "xgb", "lstm", "gru"])
    parser.add_argument("--out", type=str, default="results/models", help="Output model directory")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    df = pd.read_csv(args.data)

    dataset = TemporalDataset(window_size=5)
    X_train, y_train, X_val, y_val, X_test, y_test = dataset.prepare_data(df)

    if args.model in ["rf", "xgb"]:
        X_tr = dataset.flatten_for_trees(X_train)
        X_v = dataset.flatten_for_trees(X_val)
        model = train_tree_model(args.model, X_tr, y_train, X_v, y_val)
        model_path = os.path.join(args.out, f"{args.model}_model.joblib")
        joblib.dump({"model": model, "scaler": dataset.scaler}, model_path)
        print(f"[ML-TRAIN] Model saved to: {model_path}")
    elif args.model == "lstm":
        model = train_lstm_model(X_train, y_train, X_val, y_val)
        model_path = os.path.join(args.out, "lstm_model.pth")
        torch.save({"model_state": model.state_dict(), "scaler": dataset.scaler}, model_path)
        print(f"[ML-TRAIN] LSTM model saved to: {model_path}")

if __name__ == "__main__":
    main()
