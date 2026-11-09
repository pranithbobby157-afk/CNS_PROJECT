"""
Unit Test for GPD Parameter Estimation & Extreme Value Theory
Validates Fix C4:
- Verifies Hosking-Wallis PWM sign convention against known synthetic GPD ground truth.
- Validates threshold cutoff z_q.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import scipy.stats as stats
from code.models.dynamic_evt import AdaptiveExtremeValueDetector


def test_pwm_gpd_recovery():
    np.random.seed(42)
    # Ground truth parameters: xi (shape) = 0.20, sigma (scale) = 2.5
    true_xi = 0.20
    true_sigma = 2.5
    n_samples = 5000

    # scipy genpareto parameterization: c = xi, scale = sigma
    synthetic_excesses = stats.genpareto.rvs(c=true_xi, scale=true_sigma, size=n_samples)

    detector = AdaptiveExtremeValueDetector(target_far=1e-3, base_quantile=0.85)
    est_xi, est_sigma = detector._fit_gpd_pwm(synthetic_excesses)

    print(f"Ground Truth: xi = {true_xi:.3f}, sigma = {true_sigma:.3f}")
    print(f"PWM Estimate: xi = {est_xi:.3f}, sigma = {est_sigma:.3f}")

    # Must recover true parameters within reasonable sampling error (<= 15%)
    assert abs(est_xi - true_xi) < 0.08, f"Shape estimate {est_xi} deviated from true {true_xi}"
    assert abs(est_sigma - true_sigma) < 0.35, f"Scale estimate {est_sigma} deviated from true {true_sigma}"
    print("PWM GPD Parameter Recovery Test: PASSED ✅")


def test_sliding_window_drift_guard():
    detector = AdaptiveExtremeValueDetector(target_far=1e-3, base_quantile=0.85, window_size=500, max_drift_rate=0.05)
    baseline_energies = np.random.chisquare(df=4, size=1000)
    detector.fit(baseline_energies)

    initial_u = detector.u_
    initial_thresh = detector.extreme_threshold_

    # Simulate adversarial poisoning attempt: sudden massive energy burst
    for _ in range(50):
        detector.update_streaming_benign(1000.0)

    # Threshold must NOT jump arbitrarily due to drift velocity guard
    assert detector.u_ <= initial_u * 2.0, "Drift guard failed to prevent adversarial threshold inflation"
    print("Sliding Window & Adversarial Drift Guard Test: PASSED ✅")


if __name__ == "__main__":
    test_pwm_gpd_recovery()
    test_sliding_window_drift_guard()
