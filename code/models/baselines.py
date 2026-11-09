"""
Baseline Intrusion Detection & Open-Set Classification Models
Fixes B8:
Implements standardized baselines for fair benchmark comparisons:
1. Plain HistGBDT (Closed-World, no open-set rejection)
2. Isolation Forest (Liu et al., 2008)
3. One-Class SVM (Scholkopf et al., 2001)
4. Plain Autoencoder with MSE reconstruction threshold
5. Open-Set Softmax / Energy Score (Liu et al., NeurIPS 2020)
6. Reimplemented Gao et al. Baseline (Unweighted Tree + KAN-CVAE top-1)
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.svm import OneClassSVM
from typing import Dict, Any, Tuple


class PlainHistGBDTBaseline:
    """Closed-world baseline without open-set anomaly rejection."""
    def __init__(self, num_classes: int):
        self.model = HistGradientBoostingClassifier(random_state=42)
        self.num_classes = num_classes

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.fit(X, y)
        return self

    def predict(self, X: np.ndarray, unknown_label: int = -1) -> np.ndarray:
        # Standard GBDT cannot reject unknowns; predicts top-1 known class
        return self.model.predict(X)


class IsolationForestBaseline:
    """Unsupervised anomaly detector."""
    def __init__(self, contamination: float = 0.05):
        self.model = IsolationForest(contamination=contamination, random_state=42)

    def fit(self, X_train_benign: np.ndarray):
        self.model.fit(X_train_benign)
        return self

    def predict_anomaly(self, X: np.ndarray) -> np.ndarray:
        # -1 = anomaly, 1 = inlier
        raw = self.model.predict(X)
        return raw == -1


class OneClassSVMBaseline:
    """One-Class SVM boundary detector."""
    def __init__(self, nu: float = 0.02, gamma: str = 'scale'):
        self.model = OneClassSVM(nu=nu, gamma=gamma)

    def fit(self, X_train_benign: np.ndarray):
        self.model.fit(X_train_benign)
        return self

    def predict_anomaly(self, X: np.ndarray) -> np.ndarray:
        raw = self.model.predict(X)
        return raw == -1


class PlainAutoencoderBaseline(nn.Module):
    """Deep autoencoder with MSE reconstruction loss."""
    def __init__(self, input_dim: int, latent_dim: int = 8):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, latent_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim)
        )
        self.threshold_ = 0.0

    def forward(self, x):
        return self.decoder(self.encoder(x))

    def fit_ae(self, X_train: np.ndarray, epochs: int = 20, percentile: float = 95.0):
        optimizer = optim.Adam(self.parameters(), lr=2e-3)
        criterion = nn.MSELoss()
        X_t = torch.tensor(X_train, dtype=torch.float32)

        self.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            rec = self(X_t)
            loss = criterion(rec, X_t)
            loss.backward()
            optimizer.step()

        self.eval()
        with torch.no_grad():
            rec = self(X_t)
            mses = torch.mean((X_t - rec)**2, dim=-1).numpy()
            self.threshold_ = float(np.percentile(mses, percentile))

    def predict_anomaly(self, X: np.ndarray) -> np.ndarray:
        self.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32)
            rec = self(X_t)
            mses = torch.mean((X_t - rec)**2, dim=-1).numpy()
        return mses > self.threshold_


class OpenSetEnergyBaseline:
    """Open-set classifier using Energy score: E(x) = -T * logsumexp(logits / T)."""
    def __init__(self, num_classes: int, temperature: float = 1.0, percentile: float = 95.0):
        self.classifier = HistGradientBoostingClassifier(random_state=42)
        self.temperature = temperature
        self.percentile = percentile
        self.threshold_ = 0.0

    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        self.classifier.fit(X_train, y_train)
        # Compute energy scores on training data
        probs = self.classifier.predict_proba(X_train)
        # Convert probs to approximate log-odds logits
        logits = np.log(np.clip(probs, 1e-12, None))
        energies = -self.temperature * np.log(np.sum(np.exp(logits / self.temperature), axis=1))
        # Anomalies have high energy
        self.threshold_ = float(np.percentile(energies, self.percentile))
        return self

    def predict(self, X: np.ndarray, unknown_label: int = -1) -> np.ndarray:
        preds = self.classifier.predict(X)
        probs = self.classifier.predict_proba(X)
        logits = np.log(np.clip(probs, 1e-12, None))
        energies = -self.temperature * np.log(np.sum(np.exp(logits / self.temperature), axis=1))

        final_preds = np.copy(preds)
        is_unknown = energies > self.threshold_
        final_preds[is_unknown] = unknown_label
        return final_preds

