"""
Sequential PyTorch Models for Network Failure Prediction.
Compact, CPU-friendly LSTM and GRU architectures designed for real-time inference.
"""

import torch
import torch.nn as nn
from typing import Tuple

class FailureLSTM(nn.Module):
    """
    Two-layer LSTM with dropout and sigmoid activation for binary failure probability forecasting.
    """
    def __init__(self, input_dim: int = 20, hidden_dim: int = 32, num_layers: int = 2, dropout: float = 0.2):
        super(FailureLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]  # Take final temporal state
        logits = self.fc(last_step).squeeze(-1)
        return torch.sigmoid(logits)

class FailureGRU(nn.Module):
    """
    Two-layer GRU for low-latency failure prediction.
    """
    def __init__(self, input_dim: int = 20, hidden_dim: int = 32, num_layers: int = 2, dropout: float = 0.2):
        super(FailureGRU, self).__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gru_out, _ = self.gru(x)
        last_step = gru_out[:, -1, :]
        logits = self.fc(last_step).squeeze(-1)
        return torch.sigmoid(logits)

class FocalLoss(nn.Module):
    """
    Focal Loss to address severe class imbalance between steady-state and rare failure events.
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    """
    def __init__(self, alpha: float = 0.75, gamma: float = 2.0, reduction: str = "mean"):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        eps = 1e-7
        preds = torch.clamp(preds, eps, 1.0 - eps)
        pt = torch.where(targets == 1, preds, 1 - preds)
        w = torch.where(targets == 1, self.alpha, 1 - self.alpha)
        loss = -w * ((1 - pt) ** self.gamma) * torch.log(pt)

        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss
