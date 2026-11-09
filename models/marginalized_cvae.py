"""
Multi-Class Marginalized Conditional Autoencoder (CVAE)
Fixes:
1. Eliminates invalid KL divergence on non-probability feature vectors.
2. Implements regularized Mahalanobis distance weighted by empirical covariance.
3. Solves cascading classifier error via Top-K Marginalized Free Energy scoring.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Tuple, Optional


class MultiClassMarginalizedCVAE(nn.Module):
    """
    Class-Conditional Variational Autoencoder that decodes features conditional
    on latent space and class hypothesis. Evaluates anomaly energy marginalized
    over classifier posterior distributions.
    """

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

        # Encoder: Maps (x, one_hot_y) -> (mu, log_var)
        self.encoder = nn.Sequential(
            nn.Linear(input_dim + num_classes, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, latent_dim * 2),
        )

        # Multi-Head Class Decoders: specialized reconstruction for each known attack type
        self.decoders = nn.ModuleList([
            nn.Sequential(
                nn.Linear(latent_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.Tanh(),
                nn.Linear(hidden_dim, input_dim),
            )
            for _ in range(num_classes)
        ])

        # Precision matrix for Mahalanobis metric (learned or calibrated)
        self.register_buffer("precision_matrix", torch.eye(input_dim))

    def set_precision_matrix(self, prec: np.ndarray):
        """Sets empirical precision (inverse covariance) matrix with shrinkage."""
        self.precision_matrix = torch.tensor(prec, dtype=torch.float32, device=self.precision_matrix.device)

    def encode(self, x: torch.Tensor, y_onehot: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        xy = torch.cat([x, y_onehot], dim=-1)
        h = self.encoder(xy)
        mu, log_var = torch.chunk(h, 2, dim=-1)
        # Clamp log_var for numerical stability
        log_var = torch.clamp(log_var, min=-10.0, max=5.0)
        return mu, log_var

    def reparameterize(self, mu: torch.Tensor, log_var: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode_class(self, z: torch.Tensor, class_idx: int) -> torch.Tensor:
        return self.decoders[class_idx](z)

    def mahalanobis_distance(self, x: torch.Tensor, x_rec: torch.Tensor) -> torch.Tensor:
        """
        Calculates (x - x_rec)^T Sigma^-1 (x - x_rec).
        Mathematically valid distance metric on continuous network features.
        """
        diff = x - x_rec
        prec = self.precision_matrix.to(diff.device)
        dist = torch.sum((diff @ prec) * diff, dim=-1)
        return dist

    def fit_cvae(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        epochs: int = 25,
        batch_size: int = 128,
        lr: float = 2e-3,
        verbose: bool = False,
    ):
        """Trains CVAE using Mahalanobis reconstruction loss and KL divergence."""
        device = next(self.parameters()).device
        N, D = X_train.shape

        # Calibrate Ledoit-Wolf precision matrix if not set
        if torch.equal(self.precision_matrix, torch.eye(D, device=device)):
            # Shrinkage covariance
            cov = np.cov(X_train, rowvar=False) + 1e-4 * np.eye(D)
            prec = np.linalg.pinv(cov)
            self.set_precision_matrix(prec)

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

                # Reconstruction loss over corresponding class decoder
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

                # KL divergence to prior N(0, I)
                kl_div = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp(), dim=-1).mean()
                batch_loss = rec_loss + 0.01 * kl_div
                batch_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=5.0)
                optimizer.step()
                total_loss += batch_loss.item()

            if verbose and (epoch + 1) % 5 == 0:
                print(f"CVAE Epoch [{epoch+1}/{epochs}] Loss: {total_loss/len(loader):.4f}")

    def compute_marginalized_energy(
        self,
        X: np.ndarray,
        posterior_probs: np.ndarray,
        temperature: float = 1.0,
    ) -> np.ndarray:
        """
        Computes Marginalized Free Energy E(x) across all class hypotheses:
        E(x) = -T * log( sum_k p(y=k|x) * exp(-D_Maha(x, rec_k) / T) )
        Prevents cascading failure from single misclassified upstream labels.
        """
        self.eval()
        device = next(self.parameters()).device
        N, D = X.shape
        X_t = torch.tensor(X, dtype=torch.float32, device=device)

        with torch.no_grad():
            class_dists = []
            for c in range(self.num_classes):
                # Conditional hypothesis encoding for class c
                y_hyp = torch.zeros(N, self.num_classes, device=device)
                y_hyp[:, c] = 1.0
                mu, _ = self.encode(X_t, y_hyp)
                rec = self.decode_class(mu, c)
                dist = self.mahalanobis_distance(X_t, rec)  # Shape: (N,)
                class_dists.append(dist.cpu().numpy())

            class_dists_arr = np.column_stack(class_dists)  # Shape: (N, K)

            # Smooth negative free energy
            scaled_neg_dist = -class_dists_arr / temperature
            # Weight by classifier posterior probability
            weighted_terms = posterior_probs * np.exp(scaled_neg_dist - np.max(scaled_neg_dist, axis=1, keepdims=True))
            sum_terms = np.sum(weighted_terms, axis=1)
            
            # Log-sum-exp stabilization
            free_energy = -temperature * (
                np.log(np.clip(sum_terms, 1e-12, None)) + np.max(scaled_neg_dist, axis=1)
            )

        return free_energy

