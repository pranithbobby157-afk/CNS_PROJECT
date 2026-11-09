"""
Dirichlet-Smoothed Conditional Mutual Information (DS-CMI) & Corrected Double Markov Blanket
Fixes C1, C2:
1. Bounds conditioning set size |Z| <= max_cond_size (default: 3) to prevent sample degradation.
2. Implements stratum pooling for sparse conditioning states (pools states with N_z < min_samples_stratum).
3. Corrects Shrink Phase: Eliminates features greedily ONE AT A TIME (lowest CMI first) to avoid dropping co-dependent features simultaneously.
4. Corrects Self-Conditioning: Evaluates independence on CMB \\ {X}.
5. Eliminates in-place list mutation.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional


class RobustCausalSelector:
    """
    Discovers the Markov Blanket using Dirichlet-Smoothed CMI with:
    - Equal-depth quantile discretization
    - Stratum pooling for sparse conditioning cells
    - Greedy sequential backward elimination in the Shrink phase
    """

    def __init__(
        self,
        alpha_threshold: float = 0.015,
        n_bins: int = 8,
        dirichlet_alpha: float = 0.5,
        max_cond_size: int = 3,
        min_stratum_samples: int = 4,
    ):
        self.alpha_threshold = alpha_threshold
        self.n_bins = n_bins
        self.dirichlet_alpha = dirichlet_alpha
        self.max_cond_size = max_cond_size
        self.min_stratum_samples = min_stratum_samples

        self.selected_features_: List[int] = []
        self.marginal_scores_: Dict[int, float] = {}

    def _discretize_column(self, col: np.ndarray) -> np.ndarray:
        """Equal-depth quantile binning to ensure uniform support."""
        if np.all(col == col[0]):
            return np.zeros(len(col), dtype=np.int32)
        quantiles = np.linspace(0, 100, self.n_bins + 1)
        bins = np.percentile(col, quantiles)
        unique_bins = np.unique(bins)
        if len(unique_bins) <= 1:
            return np.zeros(len(col), dtype=np.int32)
        unique_bins[0] -= 1e-6
        unique_bins[-1] += 1e-6
        disc = np.digitize(col, unique_bins) - 1
        return np.clip(disc, 0, len(unique_bins) - 2).astype(np.int32)

    def _compute_ds_cmi(
        self,
        x_disc: np.ndarray,
        y: np.ndarray,
        cond_data: np.ndarray,
        n_classes: int,
    ) -> float:
        """
        Computes I(X; Y | Z) with Dirichlet smoothing and sparse stratum pooling.
        """
        N = len(x_disc)
        n_x = self.n_bins

        # Unconditional Mutual Information
        if cond_data.shape[1] == 0:
            counts = np.zeros((n_x, n_classes), dtype=np.float64)
            np.add.at(counts, (x_disc, y), 1.0)
            p_xy = (counts + self.dirichlet_alpha) / (N + self.dirichlet_alpha * n_x * n_classes)
            p_x = p_xy.sum(axis=1, keepdims=True)
            p_y = p_xy.sum(axis=0, keepdims=True)
            mi = np.sum(p_xy * np.log2((p_xy + 1e-12) / (p_x @ p_y + 1e-12)))
            return float(max(0.0, mi))

        # Cap conditioning set to prevent combinatorial collapse
        cond_subset = cond_data[:, :self.max_cond_size]
        base = n_x
        state_id = np.zeros(N, dtype=np.int64)
        mult = 1
        for col_idx in range(cond_subset.shape[1]):
            state_id += cond_subset[:, col_idx] * mult
            mult *= base

        unique_states, state_indices, state_counts = np.unique(
            state_id, return_inverse=True, return_counts=True
        )

        cmi = 0.0
        # Stratum pooling: Pool states with fewer than min_stratum_samples
        sparse_mask = np.isin(state_indices, np.where(state_counts < self.min_stratum_samples)[0])
        has_pooled = np.sum(sparse_mask) > 0

        for s_idx, count in enumerate(state_counts):
            if count < self.min_stratum_samples:
                continue
            mask = (state_indices == s_idx)
            x_s = x_disc[mask]
            y_s = y[mask]

            counts = np.zeros((n_x, n_classes), dtype=np.float64)
            np.add.at(counts, (x_s, y_s), 1.0)

            # Dirichlet smoothing within stratum
            p_xy_s = (counts + self.dirichlet_alpha) / (count + self.dirichlet_alpha * n_x * n_classes)
            p_x_s = p_xy_s.sum(axis=1, keepdims=True)
            p_y_s = p_xy_s.sum(axis=0, keepdims=True)

            mi_s = np.sum(p_xy_s * np.log2((p_xy_s + 1e-12) / (p_x_s @ p_y_s + 1e-12)))
            cmi += (count / N) * float(max(0.0, mi_s))

        # Compute pooled tail stratum if applicable
        if has_pooled:
            n_pooled = np.sum(sparse_mask)
            x_p = x_disc[sparse_mask]
            y_p = y[sparse_mask]
            counts_p = np.zeros((n_x, n_classes), dtype=np.float64)
            np.add.at(counts_p, (x_p, y_p), 1.0)
            p_xy_p = (counts_p + self.dirichlet_alpha) / (n_pooled + self.dirichlet_alpha * n_x * n_classes)
            p_x_p = p_xy_p.sum(axis=1, keepdims=True)
            p_y_p = p_xy_p.sum(axis=0, keepdims=True)
            mi_p = np.sum(p_xy_p * np.log2((p_xy_p + 1e-12) / (p_x_p @ p_y_p + 1e-12)))
            cmi += (n_pooled / N) * float(max(0.0, mi_p))

        return float(max(0.0, cmi))

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RobustCausalSelector":
        N, D = X.shape
        X_disc = np.zeros((N, D), dtype=np.int32)
        for d in range(D):
            X_disc[:, d] = self._discretize_column(X[:, d])

        classes, y_enc = np.unique(y, return_inverse=True)
        n_classes = len(classes)

        # -------------------------------------------------------------
        # Phase 1: Forward Growth
        # -------------------------------------------------------------
        self.marginal_scores_ = {}
        for d in range(D):
            score = self._compute_ds_cmi(X_disc[:, d], y_enc, np.empty((N, 0)), n_classes)
            self.marginal_scores_[d] = score

        # Sort candidate features by marginal mutual information
        sorted_candidates = sorted(range(D), key=lambda d: self.marginal_scores_[d], reverse=True)

        CMB_growth = []
        for feat in sorted_candidates:
            cond_data = X_disc[:, CMB_growth] if len(CMB_growth) > 0 else np.empty((N, 0))
            score = self._compute_ds_cmi(X_disc[:, feat], y_enc, cond_data, n_classes)
            if score > self.alpha_threshold:
                CMB_growth.append(feat)

        # -------------------------------------------------------------
        # Phase 2: Sequential Greedy Backward Elimination (Fixes C2)
        # Condition on CMB \ {X}.
        # Remove ONE feature with lowest CMI <= alpha per pass.
        # -------------------------------------------------------------
        CMB_shrink = list(CMB_growth)
        while True:
            candidate_removals = []
            for feat in CMB_shrink:
                cond_set = [f for f in CMB_shrink if f != feat]
                cond_data = X_disc[:, cond_set] if len(cond_set) > 0 else np.empty((N, 0))
                cmi_val = self._compute_ds_cmi(X_disc[:, feat], y_enc, cond_data, n_classes)
                if cmi_val <= self.alpha_threshold:
                    candidate_removals.append((feat, cmi_val))

            if not candidate_removals:
                break

            # Greedy elimination: drop the feature with the lowest conditional dependency
            candidate_removals.sort(key=lambda item: item[1])
            worst_feat = candidate_removals[0][0]
            CMB_shrink.remove(worst_feat)

        if len(CMB_shrink) == 0:
            # Fallback to top 5 marginal features if threshold was too aggressive
            CMB_shrink = sorted_candidates[:min(5, D)]

        self.selected_features_ = sorted(CMB_shrink)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        return X[:, self.selected_features_]

    def fit_transform(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        return self.fit(X, y).transform(X)


def test_cmi_sensitivity(X: np.ndarray, y: np.ndarray, alphas=[0.1, 0.5, 1.0], bin_sizes=[4, 8, 16]) -> Dict[str, Any]:
    """Evaluates stability of selected feature counts across hyperparameter grids."""
    results = {}
    for a in alphas:
        for b in bin_sizes:
            sel = RobustCausalSelector(alpha_threshold=0.015, n_bins=b, dirichlet_alpha=a)
            sel.fit(X, y)
            results[f"alpha_{a}_bins_{b}"] = {
                "num_selected": len(sel.selected_features_),
                "features": sel.selected_features_
            }
    return results

