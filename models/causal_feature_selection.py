"""
Robust Causal Feature Selection Module (IR-IDS 2.0)
Fixes the mathematical, algorithmic, and statistical loopholes in IR-IDS:
1. Replaces inverted propensity score and combinatorial grid conditioning with Dirichlet-smoothed CMI.
2. Fixes Algorithm 1 self-conditioning bug (tests X ⊥ Y | CMB \\ {X}, not CMB).
3. Fixes in-place list mutation bug during iteration.
4. Eliminates division-by-zero via Bayesian categorical smoothing.
"""

import numpy as np
from typing import List, Optional, Tuple, Dict


class RobustCausalSelector:
    """
    Identifies the minimal and sufficient causal feature subset (Markov Boundary)
    for target Y using adaptive Dirichlet-smoothed Conditional Mutual Information (CMI).
    """

    def __init__(
        self,
        alpha_threshold: float = 0.015,
        n_bins: int = 8,
        dirichlet_alpha: float = 0.5,
        max_conditioning_size: int = 4,
    ):
        """
        Args:
            alpha_threshold: Minimum CMI required to retain feature in candidate set.
            n_bins: Number of quantile bins for continuous feature discretization.
            dirichlet_alpha: Prior parameter for Laplace/Dirichlet smoothing (Jeffreys prior=0.5).
            max_conditioning_size: Maximum conditioning set size to preserve statistical power.
        """
        self.alpha_threshold = alpha_threshold
        self.n_bins = n_bins
        self.dirichlet_alpha = dirichlet_alpha
        self.max_conditioning_size = max_conditioning_size
        self.selected_features_: List[int] = []
        self.feature_scores_: Dict[int, float] = {}

    def _discretize_feature(self, column: np.ndarray) -> np.ndarray:
        """Quantile-based equal-depth binning prevents empty sparse cells."""
        # Handle constant or near-constant features
        if np.all(column == column[0]):
            return np.zeros(len(column), dtype=np.int32)
            
        quantiles = np.linspace(0, 100, self.n_bins + 1)
        bins = np.percentile(column, quantiles)
        # Deduplicate identical bin edges
        unique_bins = np.unique(bins)
        if len(unique_bins) <= 1:
            return np.zeros(len(column), dtype=np.int32)
            
        unique_bins[0] -= 1e-6
        unique_bins[-1] += 1e-6
        discrete = np.digitize(column, unique_bins) - 1
        return np.clip(discrete, 0, len(unique_bins) - 2).astype(np.int32)

    def _compute_dirichlet_cmi(
        self,
        x: np.ndarray,
        y: np.ndarray,
        cond_data: np.ndarray,
        n_x_bins: int,
        n_classes: int,
    ) -> float:
        """
        Computes I(X; Y | Z) with Bayesian Dirichlet smoothing:
        P(x, y, z) = (N(x, y, z) + alpha) / (N + alpha * |X| * |Y| * |Z|)
        Guarantees zero-probability avoidance and mathematical boundedness.
        """
        N = len(x)
        if cond_data.shape[1] == 0:
            # Unconditional Mutual Information I(X; Y)
            joint_counts = np.zeros((n_x_bins, n_classes), dtype=np.float64)
            np.add.at(joint_counts, (x, y), 1.0)
            
            # Smooth joint distribution
            p_xy = (joint_counts + self.dirichlet_alpha) / (
                N + self.dirichlet_alpha * n_x_bins * n_classes
            )
            p_x = p_xy.sum(axis=1, keepdims=True)
            p_y = p_xy.sum(axis=0, keepdims=True)
            
            mi = np.sum(p_xy * np.log(p_xy / (p_x @ p_y)))
            return float(max(0.0, mi))

        # Discretize conditioning set to compact 1D state
        # Limit conditioning size to avoid sample degradation
        cond_to_use = cond_data[:, :self.max_conditioning_size]
        base = n_x_bins
        cond_state = np.zeros(N, dtype=np.int64)
        mult = 1
        for col in range(cond_to_use.shape[1]):
            cond_state += cond_to_use[:, col] * mult
            mult *= base

        unique_states, state_indices = np.unique(cond_state, return_inverse=True)
        cmi = 0.0

        for s_idx, state_val in enumerate(unique_states):
            mask = (state_indices == s_idx)
            n_s = np.sum(mask)
            if n_s < 2:
                continue

            x_s = x[mask]
            y_s = y[mask]

            joint = np.zeros((n_x_bins, n_classes), dtype=np.float64)
            np.add.at(joint, (x_s, y_s), 1.0)

            # Dirichlet smoothing within conditioning stratum
            p_xy_s = (joint + self.dirichlet_alpha) / (
                n_s + self.dirichlet_alpha * n_x_bins * n_classes
            )
            p_x_s = p_xy_s.sum(axis=1, keepdims=True)
            p_y_s = p_xy_s.sum(axis=0, keepdims=True)

            mi_s = np.sum(p_xy_s * np.log(p_xy_s / (p_x_s @ p_y_s)))
            cmi += (n_s / N) * float(max(0.0, mi_s))

        return cmi

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RobustCausalSelector":
        """
        Executes the corrected Double Markov Blanket search.
        """
        N, D = X.shape
        # Discretize continuous features
        X_disc = np.zeros((N, D), dtype=np.int32)
        for d in range(D):
            X_disc[:, d] = self._discretize_feature(X[:, d])

        # Map targets to integers 0..K-1
        classes, y_encoded = np.unique(y, return_inverse=True)
        n_classes = len(classes)

        # -------------------------------------------------------------
        # PHASE 1: GROWTH (Forward search for candidate Markov Blanket)
        # -------------------------------------------------------------
        CMB_growth: List[int] = []
        candidate_pool = list(range(D))

        # First sort candidates by unconditional MI for faster convergence
        marginal_scores = []
        for feat in candidate_pool:
            score = self._compute_dirichlet_cmi(
                X_disc[:, feat], y_encoded, np.empty((N, 0), dtype=np.int32), self.n_bins, n_classes
            )
            marginal_scores.append((feat, score))
            self.feature_scores_[feat] = score

        marginal_scores.sort(key=lambda item: item[1], reverse=True)
        sorted_candidates = [f for f, s in marginal_scores if s > 1e-4]

        for feat in sorted_candidates:
            cond_data = X_disc[:, CMB_growth] if len(CMB_growth) > 0 else np.empty((N, 0), dtype=np.int32)
            cmi = self._compute_dirichlet_cmi(
                X_disc[:, feat], y_encoded, cond_data, self.n_bins, n_classes
            )
            if cmi > self.alpha_threshold:
                CMB_growth.append(feat)

        # -------------------------------------------------------------
        # PHASE 2: SHRINK (Prune features rendered conditionally independent)
        # BUG FIX: Test X ⊥ Y | CMB \ {X}.
        # BUG FIX: Do NOT mutate CMB in-place during the loop.
        # -------------------------------------------------------------
        CMB_shrink = list(CMB_growth)
        converged = False
        iteration = 0
        max_iters = 10

        while not converged and iteration < max_iters:
            iteration += 1
            to_remove = []

            for feat in CMB_shrink:
                # Conditioning set explicitly excludes feature under test
                other_features = [f for f in CMB_shrink if f != feat]
                cond_data = X_disc[:, other_features] if len(other_features) > 0 else np.empty((N, 0), dtype=np.int32)
                
                cmi = self._compute_dirichlet_cmi(
                    X_disc[:, feat], y_encoded, cond_data, self.n_bins, n_classes
                )
                if cmi <= self.alpha_threshold:
                    to_remove.append(feat)

            if len(to_remove) == 0:
                converged = True
            else:
                for r in to_remove:
                    if r in CMB_shrink:
                        CMB_shrink.remove(r)

        # If aggressive pruning emptied the set, retain top marginal features
        if len(CMB_shrink) == 0:
            top_k = min(5, D)
            CMB_shrink = [f for f, _ in marginal_scores[:top_k]]

        self.selected_features_ = sorted(CMB_shrink)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if len(self.selected_features_) == 0:
            raise RuntimeError("Selector must be fitted before transforming.")
        return X[:, self.selected_features_]

    def fit_transform(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        return self.fit(X, y).transform(X)


def evaluate_causal_invariance(
    X_sub: np.ndarray, y: np.ndarray, env_ids: np.ndarray
) -> float:
    """
    Quantifies the invariance of the chosen feature representation across
    distinct network capture environments (subnets, capture days).
    Returns an Invariance Violation Ratio (lower is better, 0 = perfectly invariant).
    """
    unique_envs = np.unique(env_ids)
    if len(unique_envs) < 2:
        return 0.0

    env_means = []
    for env in unique_envs:
        mask = (env_ids == env)
        if np.sum(mask) > 10:
            env_means.append(np.mean(X_sub[mask], axis=0))

    if len(env_means) < 2:
        return 0.0

    env_means_arr = np.array(env_means)
    variance_across_envs = np.var(env_means_arr, axis=0)
    invariance_score = float(np.mean(variance_across_envs))
    return invariance_score

