"""
Multi-Class Marginalized Conditional Autoencoder (CVAE)
Implements:
1. Multi-head class decoders (one specialized decoder head per known class).
2. Ledoit-Wolf shrinkage covariance for regularized Mahalanobis distance.
3. Top-K Marginalized Free Energy scoring over classifier posterior distribution.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Tuple, Optional


class MultiClassMarginalizedCVAE(nn.Module):
    def __init__(
        self,
        input_dim: int,
        num_classes: int,
        latent_dim: int = 8,
        hidden_dim: int = 32,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.num_classes = num_classes
        self.latent_dim = latent_dim

        # Encoder: x + onehot(y) -> (mu, log_var)
        self.encoder = nn.Sequential(
            nn.Linear(input_dim + num_classes, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, latent_dim * 2),
        )

        # Multi-Head Class Decoders
        self.decoders = nn.ModuleList([
            nn.Sequential(
                nn.Linear(latent_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.Tanh(),
                nn.Linear(hidden_dim, input_dim),
            )
            for _ in range(num_classes)
        ])

        self.register_buffer("precision_matrix", torch.eye(input_dim))

    def set_precision_matrix(self, prec: np.ndarray):
        self.precision_matrix = torch.tensor(prec, dtype=torch.float32, device=self.precision_matrix.device)

    def encode(self, x: torch.Tensor, y_onehot: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        xy = torch.cat([x, y_onehot], dim=-1)
        h = self.encoder(xy)
        mu, log_var = torch.chunk(h, 2, dim=-1)
        log_var = torch.clamp(log_var, min=-10.0, max=5.0)
        return mu, log_var

    def reparameterize(self, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode_class(self, z: torch.Tensor, class_idx: int) -> torch.Tensor:
        return self.decoders[class_idx](z)

    def mahalanobis_distance(self, x: torch.Tensor, x_rec: torch.Tensor) -> torch.Tensor:
        diff = x - x_rec
        prec = self.precision_matrix.to(diff.device)
        dist = torch.sum((diff @ prec) * diff, dim=-1)
        return dist

    def fit_cvae(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        epochs: int = 20,
        batch_size: int = 128,
        lr: float = 2e-3,
        verbose: bool = False,
    ):
        device = next(self.parameters()).device
        N, D = X_train.shape

        optimizer = optim.AdamW(self.parameters(), lr=lr, weight_decay=1e-4)

        X_t = torch.tensor(X_train, dtype=torch.float32)
        y_oh = torch.zeros(N, self.num_classes).scatter_(
            1, torch.tensor(y_train, dtype=torch.int64).unsqueeze(1), 1.0
        )
        dataset = torch.utils.data.TensorDataset(X_t, y_oh, torch.tensor(y_train, dtype=torch.int64))
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.train()
        for epoch in range(epochs):
            total_loss = 0.0
            for bx, by_oh, by_cls in loader:
                bx, by_oh, by_cls = bx.to(device), by_oh.to(device), by_cls.to(device)
                optimizer.zero_grad()

                mu, log_var = self.encode(bx, by_oh)
                z = self.reparameterize(mu, log_var)

                rec_loss = torch.tensor(0.0, device=device)
                for c in range(self.num_classes):
                    c_mask = (by_cls == c)
                    if torch.sum(c_mask) == 0:
                        continue
                    x_c = bx[c_mask]
                    z_c = z[c_mask]
                    x_rec_c = self.decode_class(z_c, c)
                    rec_dist = self.mahalanobis_distance(x_c, x_rec_c)
                    rec_loss = rec_loss + torch.mean(rec_dist)

                kl_div = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp(), dim=-1).mean()
                batch_loss = rec_loss + 0.01 * kl_div
                batch_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=5.0)
                optimizer.step()
                total_loss += batch_loss.item()

    def compute_marginalized_energy(
        self,
        X: np.ndarray,
        posterior_probs: np.ndarray,
        temperature: float = 1.0,
    ) -> np.ndarray:
        self.eval()
        device = next(self.parameters()).device
        N, D = X.shape
        X_t = torch.tensor(X, dtype=torch.float32, device=device)

        with torch.no_grad():
            class_dists = []
            for c in range(self.num_classes):
                y_hyp = torch.zeros(N, self.num_classes, device=device)
                y_hyp[:, c] = 1.0
                mu, _ = self.encode(X_t, y_hyp)
                rec = self.decode_class(mu, c)
                dist = self.mahalanobis_distance(X_t, rec)
                class_dists.append(dist.cpu().numpy())

            class_dists_arr = np.column_stack(class_dists)
            scaled_neg_dist = -0.5 * class_dists_arr / temperature
            max_val = np.max(scaled_neg_dist, axis=1, keepdims=True)
            weighted_terms = posterior_probs * np.exp(scaled_neg_dist - max_val)
            sum_terms = np.sum(weighted_terms, axis=1)
            free_energy = -temperature * (np.log(np.clip(sum_terms, 1e-12, None)) + max_val.squeeze())

        return free_energy

    def compute_conditional_free_energy(
        self,
        X: np.ndarray,
        predicted_classes: np.ndarray,
    ) -> np.ndarray:
        """Top-1 conditioned free energy (reconstruction error under predicted class)."""
        self.eval()
        device = next(self.parameters()).device
        N, D = X.shape
        X_t = torch.tensor(X, dtype=torch.float32, device=device)

        with torch.no_grad():
            energies = np.zeros(N, dtype=np.float32)
            for c in range(self.num_classes):
                c_mask = (predicted_classes == c)
                if not np.any(c_mask):
                    continue
                x_sub = X_t[c_mask]
                y_hyp = torch.zeros(len(x_sub), self.num_classes, device=device)
                y_hyp[:, c] = 1.0
                mu, _ = self.encode(x_sub, y_hyp)
                rec = self.decode_class(mu, c)
                dist = self.mahalanobis_distance(x_sub, rec)
                energies[c_mask] = (0.5 * dist).cpu().numpy()

        return energies
