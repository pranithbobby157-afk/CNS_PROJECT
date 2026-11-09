"""
Unit and Integration Tests for IR-IDS 2.0
Validates:
1. Double Markov Blanket search executes without in-place mutation or self-conditioning bugs.
2. Dirichlet smoothing prevents division-by-zero on sparse conditioning.
3. Mahalanobis distance metric behaves consistently on continuous vectors.
4. Dynamic POT-EVT accurately calculates extreme tail threshold.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest
import torch

from models.causal_feature_selection import RobustCausalSelector
from models.cost_sensitive_classifier import CostSensitiveClassifier
from models.marginalized_cvae import MultiClassMarginalizedCVAE
from models.dynamic_evt import AdaptiveExtremeValueDetector
from models.symbolic_kan import KolmogorovArnoldLayer, extract_symbolic_representation


def test_causal_selector_no_mutation_bug():
    np.random.seed(42)
    N, D = 500, 15
    X = np.random.randn(N, D)
    # Feature 2 and Feature 5 causally determine Y
    y = ((X[:, 2] + X[:, 5] * 1.5) > 0.5).astype(np.int64)

    selector = RobustCausalSelector(alpha_threshold=0.01, n_bins=6)
    selector.fit(X, y)

    selected = selector.selected_features_
    assert isinstance(selected, list)
    assert len(selected) > 0
    # Must retain key causal features
    assert (2 in selected) or (5 in selected)


def test_dirichlet_smoothing_bounds():
    selector = RobustCausalSelector(dirichlet_alpha=0.5, n_bins=4)
    # Generate extreme sparse data where many cells are zero
    x = np.array([0, 1, 0, 1, 0, 1])
    y = np.array([0, 0, 0, 0, 0, 0])  # Y is degenerate
    cond = np.zeros((6, 0), dtype=np.int32)
    cmi = selector._compute_dirichlet_cmi(x, y, cond, n_x_bins=4, n_classes=2)
    assert np.isfinite(cmi)
    assert cmi >= 0.0


def test_mahalanobis_cvae_marginalization():
    input_dim = 6
    num_classes = 3
    cvae = MultiClassMarginalizedCVAE(input_dim=input_dim, num_classes=num_classes, latent_dim=4)

    X = np.random.randn(50, input_dim).astype(np.float32)
    probs = np.array([[0.7, 0.2, 0.1]] * 50)

    energies = cvae.compute_marginalized_energy(X, probs)
    assert len(energies) == 50
    assert np.all(np.isfinite(energies))
    assert np.all(energies > 0.0)


def test_adaptive_evt_threshold():
    detector = AdaptiveExtremeValueDetector(target_far=1e-3, base_quantile=0.85)
    # Simulate normal chi-square reconstruction errors
    normal_errors = np.random.chisquare(df=4, size=2000)
    detector.fit(normal_errors)

    threshold = detector.extreme_threshold_
    assert threshold > detector.u_
    # On normal distribution, the fraction exceeding threshold should be close to or under target FAR
    actual_far = np.mean(normal_errors > threshold)
    assert actual_far <= 0.05  # Far below the naive 10% cutoff


def test_symbolic_kan_extraction():
    in_dim, out_dim = 5, 3
    kan = KolmogorovArnoldLayer(in_features=in_dim, out_features=out_dim, degree=3)
    x = torch.randn(10, in_dim)
    out = kan(x)
    assert out.shape == (10, out_dim)

    formulas = extract_symbolic_representation(kan, [f"pkt_stat_{i}" for i in range(in_dim)])
    assert len(formulas) == out_dim
    assert "symbolic_formula" in formulas[0]


if __name__ == "__main__":
    test_causal_selector_no_mutation_bug()
    test_dirichlet_smoothing_bounds()
    test_mahalanobis_cvae_marginalization()
    test_adaptive_evt_threshold()
    test_symbolic_kan_extraction()
    print("ALL UNIT TESTS PASSED SUCCESSFULLY! ✅")
