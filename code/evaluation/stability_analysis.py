"""
Feature Selection Stability and Runtime Analysis (Fixes C3)
Compares:
1. DS-CMI (Proposed Dirichlet-smoothed Causal Selection with sequential shrink)
2. Standard Mutual Information (MI, Kraskov / Sklearn)
3. G-Test / Chi-Squared feature selector
4. BAMB Baseline (Backward Elimination without stratum pooling)

Computes average pairwise Jaccard index across 5 seeds:
Jaccard(S_i, S_j) = |S_i \cap S_j| / |S_i \cup S_j|
and execution runtime.
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd
from typing import List, Set
from sklearn.feature_selection import mutual_info_classif, SelectKBest, chi2
from sklearn.preprocessing import KBinsDiscretizer

from code.data.dataset_loader import generate_synthetic_benchmark_dataset
from code.data.preprocessor import FlowDataPreprocessor
from code.models.causal_feature_selection import RobustCausalSelector


def compute_pairwise_jaccard(sets: List[Set[int]]) -> Tuple[float, float]:
    """Computes mean and std of pairwise Jaccard similarities."""
    jaccards = []
    n = len(sets)
    for i in range(n):
        for j in range(i + 1, n):
            s1, s2 = sets[i], sets[j]
            if len(s1 | s2) == 0:
                jaccards.append(1.0)
            else:
                jaccards.append(len(s1 & s2) / len(s1 | s2))
    return float(np.mean(jaccards)), float(np.std(jaccards))


def run_stability_benchmark(seeds: List[int] = [42, 101, 202, 303, 404], target_k: int = 15):
    os.makedirs("results", exist_ok=True)
    methods = {
        "DS-CMI (Proposed)": [],
        "Standard Mutual Info": [],
        "G-Test (Chi-Squared)": [],
        "BAMB Baseline": []
    }

    runtimes = {m: [] for m in methods}

    for seed in seeds:
        split = generate_synthetic_benchmark_dataset(seed=seed)
        prep = FlowDataPreprocessor().fit(split.X_train)
        X = prep.transform(split.X_train)
        y = split.y_train

        # 1. DS-CMI (Proposed)
        t0 = time.time()
        cfs = RobustCausalSelector(alpha_threshold=0.015, dirichlet_alpha=0.5, max_cond_size=3)
        cfs.fit(X, y)
        runtimes["DS-CMI (Proposed)"].append(time.time() - t0)
        methods["DS-CMI (Proposed)"].append(set(cfs.selected_features_))

        # 2. Standard Mutual Information
        t0 = time.time()
        mi_scores = mutual_info_classif(X[:2500], y[:2500], random_state=seed)
        top_mi = set(np.argsort(mi_scores)[-target_k:])
        runtimes["Standard Mutual Info"].append(time.time() - t0)
        methods["Standard Mutual Info"].append(top_mi)

        # 3. G-Test / Chi2 (discretized non-negative bins)
        t0 = time.time()
        disc = KBinsDiscretizer(n_bins=5, encode="ordinal", strategy="uniform")
        X_binned = disc.fit_transform(X[:2500] - np.min(X[:2500]))
        ch2_selector = SelectKBest(chi2, k=min(target_k, X.shape[1]))
        ch2_selector.fit(X_binned, y[:2500])
        top_chi2 = set(ch2_selector.get_support(indices=True))
        runtimes["G-Test (Chi-Squared)"].append(time.time() - t0)
        methods["G-Test (Chi-Squared)"].append(top_chi2)

        # 4. BAMB Baseline (Backward elimination without stratum pooling or conditioning cap)
        t0 = time.time()
        bamb_selector = RobustCausalSelector(alpha_threshold=0.015, dirichlet_alpha=0.0, max_cond_size=10, min_stratum_samples=0)
        bamb_selector.fit(X[:1500], y[:1500])
        runtimes["BAMB Baseline"].append(time.time() - t0)
        methods["BAMB Baseline"].append(set(bamb_selector.selected_features_))

    # Compile results
    rows = []
    for m in methods:
        mean_jaccard, std_jaccard = compute_pairwise_jaccard(methods[m])
        avg_runtime = float(np.mean(runtimes[m]))
        avg_num_feats = float(np.mean([len(s) for s in methods[m]]))
        rows.append({
            "Method": m,
            "Mean_Jaccard_Stability": round(mean_jaccard, 4),
            "Std_Jaccard_Stability": round(std_jaccard, 4),
            "Jaccard_Formatted": f"{mean_jaccard:.3f} ± {std_jaccard:.3f}",
            "Avg_Selected_Features": round(avg_num_feats, 1),
            "Avg_Runtime_Seconds": round(avg_runtime, 2)
        })

    df = pd.DataFrame(rows)
    df.to_csv("results/feature_stability.csv", index=False)
    print("Saved results/feature_stability.csv")
    print(df.to_string())
    return df


if __name__ == "__main__":
    run_stability_benchmark()
