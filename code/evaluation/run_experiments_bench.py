"""
Multi-Seed Benchmark and Ablation Evaluation for IR-IDS 2.0
Fixes:
- B1: Multi-class network traffic evaluation with known volumetric attacks and held-out zero-day classes.
- B2: Reimplemented Gao et al. baseline under identical protocol.
- B3: Separate per-class zero-day recalls with exact counts (k/n).
- B4: 5 seeds, mean +/- std, 95% bootstrap confidence intervals.
- B5: Focal loss applied strictly to training classes (e.g. SQL Injection).
- B6: Fair static quantile ablation at exact same target FAR (1 - q).
- B8: Standardized baselines (Plain HistGBDT, Isolation Forest, OC-SVM, Plain AE, Open-Set Energy).
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from sklearn.metrics import f1_score, accuracy_score
from sklearn.ensemble import HistGradientBoostingClassifier

from code.data.dataset_loader import generate_synthetic_benchmark_dataset, BenchmarkSplit
from code.data.preprocessor import FlowDataPreprocessor
from code.models.baselines import (
    PlainHistGBDTBaseline,
    IsolationForestBaseline,
    OneClassSVMBaseline,
    PlainAutoencoderBaseline,
    OpenSetEnergyBaseline
)
from code.pipeline.irids2_system import IRIDS2System
from code.models.causal_feature_selection import RobustCausalSelector
from code.models.cost_sensitive_classifier import CostSensitiveClassifier
from code.models.marginalized_cvae import MultiClassMarginalizedCVAE
from code.models.dynamic_evt import AdaptiveExtremeValueDetector


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    test_labels_str: List[str],
    known_classes: List[str],
    unknown_classes: List[str]
) -> Dict[str, float]:
    """Calculates macro-F1, G-mean, FAR, and per-class recalls with exact counts."""
    # Accuracy and Macro-F1
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

    # Benign False Alarm Rate (FAR)
    # Benign is index 0
    benign_mask = (y_true == 0)
    total_benign = np.sum(benign_mask)
    false_alarms = np.sum((y_pred != 0) & benign_mask)
    far = false_alarms / max(1, total_benign)

    # Zero-day recall overall (label == -1)
    zd_mask = (y_true == -1)
    total_zd = np.sum(zd_mask)
    detected_zd = np.sum((y_pred == -1) & zd_mask)
    zd_recall = detected_zd / max(1, total_zd)

    # Per-class recalls and counts
    test_labels = np.array(test_labels_str)
    res = {
        "Accuracy": acc,
        "Macro_F1": macro_f1,
        "FAR": far,
        "ZeroDay_Recall": zd_recall,
        "ZeroDay_Count": f"{detected_zd}/{total_zd}",
    }

    # Per-class for unknown classes
    for uc in unknown_classes:
        mask = (test_labels == uc)
        tot = np.sum(mask)
        det = np.sum((y_pred == -1) & mask)
        res[f"{uc}_Recall"] = det / max(1, tot)
        res[f"{uc}_Count"] = f"{det}/{tot}"

    # Rare stealth known class: SQL Injection
    sqli_idx = known_classes.index("SQL_Injection") if "SQL_Injection" in known_classes else -1
    if sqli_idx >= 0:
        mask = (y_true == sqli_idx)
        tot = np.sum(mask)
        det = np.sum((y_pred == sqli_idx) & mask)
        res["SQLi_Recall"] = det / max(1, tot)
        res["SQLi_Count"] = f"{det}/{tot}"

    # G-Mean: geometric mean of recalls across all present classes
    unique_classes = np.unique(y_true)
    recalls = []
    for c in unique_classes:
        c_mask = (y_true == c)
        c_tot = np.sum(c_mask)
        c_det = np.sum((y_pred == c) & c_mask)
        recalls.append(c_det / max(1, c_tot))
    g_mean = float(np.prod(recalls) ** (1.0 / len(recalls))) if recalls else 0.0
    res["G_Mean"] = g_mean

    return res


def bootstrap_ci(values: List[float], n_bootstraps: int = 1000, ci: float = 0.95) -> Tuple[float, float, float]:
    """Returns (mean, ci_lower, ci_upper) using empirical bootstrap."""
    arr = np.array(values)
    mean = float(np.mean(arr))
    boot_means = []
    rng = np.random.RandomState(42)
    for _ in range(n_bootstraps):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boot_means.append(np.mean(sample))
    alpha = (1.0 - ci) / 2.0
    low = float(np.percentile(boot_means, alpha * 100))
    high = float(np.percentile(boot_means, (1.0 - alpha) * 100))
    return mean, low, high


def run_benchmark(seeds: List[int] = [42, 101, 202, 303, 404]):
    os.makedirs("results", exist_ok=True)
    models = [
        "Plain HistGBDT",
        "Isolation Forest",
        "One-Class SVM",
        "Plain Autoencoder",
        "Open-Set Energy",
        "Reimplemented Baseline",
        "IR-IDS 2.0 (Proposed)"
    ]

    all_results = {m: [] for m in models}

    for seed in seeds:
        print(f"\n--- Running Seed {seed} ---")
        split = generate_synthetic_benchmark_dataset(seed=seed)
        prep = FlowDataPreprocessor().fit(split.X_train)
        X_train_s = prep.transform(split.X_train)
        X_test_s = prep.transform(split.X_test)
        y_train = split.y_train
        y_test = split.y_test
        labels_str = split.test_labels_str
        known_cls = split.known_classes
        unknown_cls = split.unknown_classes

        # Benign mask
        benign_train = X_train_s[y_train == 0]

        # 1. Plain HistGBDT
        gbdt = PlainHistGBDTBaseline(len(known_cls)).fit(X_train_s, y_train)
        pred_gbdt = gbdt.predict(X_test_s)
        all_results["Plain HistGBDT"].append(
            compute_metrics(y_test, pred_gbdt, labels_str, known_cls, unknown_cls)
        )

        # 2. Isolation Forest
        ifo = IsolationForestBaseline().fit(benign_train)
        pred_ifo = gbdt.predict(X_test_s)
        anom_ifo = ifo.predict_anomaly(X_test_s)
        pred_ifo[anom_ifo] = -1
        all_results["Isolation Forest"].append(
            compute_metrics(y_test, pred_ifo, labels_str, known_cls, unknown_cls)
        )

        # 3. One-Class SVM
        ocsvm = OneClassSVMBaseline().fit(benign_train[:3000])  # subset for tractable fit
        pred_oc = gbdt.predict(X_test_s)
        anom_oc = ocsvm.predict_anomaly(X_test_s)
        pred_oc[anom_oc] = -1
        all_results["One-Class SVM"].append(
            compute_metrics(y_test, pred_oc, labels_str, known_cls, unknown_cls)
        )

        # 4. Plain Autoencoder
        pae = PlainAutoencoderBaseline(input_dim=X_train_s.shape[1])
        pae.fit_ae(benign_train, epochs=15)
        pred_pae = gbdt.predict(X_test_s)
        anom_pae = pae.predict_anomaly(X_test_s)
        pred_pae[anom_pae] = -1
        all_results["Plain Autoencoder"].append(
            compute_metrics(y_test, pred_pae, labels_str, known_cls, unknown_cls)
        )

        # 5. Open-Set Energy
        ose = OpenSetEnergyBaseline(len(known_cls)).fit(X_train_s, y_train)
        pred_ose = ose.predict(X_test_s)
        all_results["Open-Set Energy"].append(
            compute_metrics(y_test, pred_ose, labels_str, known_cls, unknown_cls)
        )

        # 6. Reimplemented Baseline (Gao et al.: Top-1 CVAE conditioning, static quantile)
        # Uses unweighted classifier and top-1 conditional energy
        cvae_base = MultiClassMarginalizedCVAE(input_dim=X_train_s.shape[1], num_classes=len(known_cls), latent_dim=8)
        cvae_base.fit_cvae(X_train_s, y_train, epochs=8)
        # Top-1 energy
        top1_preds = gbdt.predict(X_test_s)
        top1_train = gbdt.predict(X_train_s)
        energies_train = cvae_base.compute_conditional_free_energy(X_train_s, top1_train)
        energies_test = cvae_base.compute_conditional_free_energy(X_test_s, top1_preds)
        # Static 0.9 quantile threshold
        static_thresh = float(np.percentile(energies_train, 90.0))
        pred_reimp = np.copy(top1_preds)
        pred_reimp[energies_test > static_thresh] = -1
        all_results["Reimplemented Baseline"].append(
            compute_metrics(y_test, pred_reimp, labels_str, known_cls, unknown_cls)
        )

        # 7. IR-IDS 2.0 (Proposed)
        ir2 = IRIDS2System(known_class_names=known_cls, target_far=1e-3)
        ir2.fit(split.X_train, y_train)
        pred_ir2 = ir2.predict(split.X_test)
        all_results["IR-IDS 2.0 (Proposed)"].append(
            compute_metrics(y_test, pred_ir2, labels_str, known_cls, unknown_cls)
        )

    # Summarize benchmark metrics
    summary_rows = []
    per_class_rows = []
    numeric_keys = ["Macro_F1", "G_Mean", "FAR", "ZeroDay_Recall", "Accuracy"]
    class_keys = ["Infiltration_Recall", "Botnet_Recall", "SQLi_Recall"]

    for m in models:
        row = {"Model": m}
        for k in numeric_keys:
            vals = [res[k] for res in all_results[m]]
            mean = np.mean(vals)
            std = np.std(vals)
            _, low, high = bootstrap_ci(vals)
            row[f"{k}_mean"] = round(mean, 4)
            row[f"{k}_std"] = round(std, 4)
            row[f"{k}_ci95"] = f"[{round(low, 4)}, {round(high, 4)}]"
            row[f"{k}_formatted"] = f"{mean*100:.2f}% ± {std*100:.2f}%"
        summary_rows.append(row)

        pc_row = {"Model": m}
        for ck in class_keys:
            vals = [res[ck] for res in all_results[m]]
            mean = np.mean(vals)
            std = np.std(vals)
            counts = [res[ck.replace("Recall", "Count")] for res in all_results[m]]
            pc_row[f"{ck}_mean"] = round(mean, 4)
            pc_row[f"{ck}_std"] = round(std, 4)
            pc_row[f"{ck}_formatted"] = f"{mean*100:.2f}% ± {std*100:.2f}%"
            pc_row[f"{ck}_counts_seed42"] = counts[0]
        per_class_rows.append(pc_row)

    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv("results/benchmark_5seeds.csv", index=False)
    print("\nSaved results/benchmark_5seeds.csv")

    df_pc = pd.DataFrame(per_class_rows)
    df_pc.to_csv("results/per_class_recalls_5seeds.csv", index=False)
    print("Saved results/per_class_recalls_5seeds.csv")

    return df_summary, df_pc


def run_ablations(seeds: List[int] = [42, 101, 202, 303, 404]):
    print("\n================ Running Ablation Experiments ================")
    ablation_names = [
        "IR-IDS 2.0 (Full)",
        "w/o Focal Loss (Standard GBDT)",
        "w/o Marginalized Energy (Top-1 Conditioning)",
        "w/o POT-EVT (Fair Static Quantile @ 1-q)",
        "w/o Dirichlet CMI (Raw Plug-in CMI)"
    ]

    all_ablations = {name: [] for name in ablation_names}

    for seed in seeds:
        print(f"--- Ablation Seed {seed} ---")
        split = generate_synthetic_benchmark_dataset(seed=seed)
        prep = FlowDataPreprocessor().fit(split.X_train)
        X_train_s = prep.transform(split.X_train)
        X_test_s = prep.transform(split.X_test)
        y_train = split.y_train
        y_test = split.y_test
        labels_str = split.test_labels_str
        known_cls = split.known_classes
        unknown_cls = split.unknown_classes

        # Full IR-IDS 2.0
        ir2 = IRIDS2System(known_class_names=known_cls, target_far=1e-3)
        ir2.fit(split.X_train, y_train, cvae_epochs=8, verbose=False)
        p_full = ir2.predict(split.X_test)
        all_ablations["IR-IDS 2.0 (Full)"].append(
            compute_metrics(y_test, p_full, labels_str, known_cls, unknown_cls)
        )

        sel_features = ir2.selected_feature_indices_

        # 1. w/o Focal Loss
        cls_nofocal = HistGradientBoostingClassifier(random_state=seed)
        cls_nofocal.fit(X_train_s[:, sel_features], y_train)
        p_nofocal_cls = cls_nofocal.predict(X_test_s[:, sel_features])
        probs_nofocal = cls_nofocal.predict_proba(X_test_s[:, sel_features])
        e_test = ir2.cvae.compute_marginalized_energy(X_test_s[:, sel_features], probs_nofocal)
        p_nofocal = np.copy(p_nofocal_cls)
        p_nofocal[e_test > ir2.evt_detector.extreme_threshold_] = -1
        all_ablations["w/o Focal Loss (Standard GBDT)"].append(
            compute_metrics(y_test, p_nofocal, labels_str, known_cls, unknown_cls)
        )

        # 2. w/o Marginalized Energy (Top-1 conditioning)
        top1_train = ir2.classifier.predict(X_train_s[:, sel_features])
        top1_test = ir2.classifier.predict(X_test_s[:, sel_features])
        e_top1_train = ir2.cvae.compute_conditional_free_energy(X_train_s[:, sel_features], top1_train)
        e_top1_test = ir2.cvae.compute_conditional_free_energy(X_test_s[:, sel_features], top1_test)
        evt_top1 = AdaptiveExtremeValueDetector(target_far=1e-3).fit(e_top1_train)
        p_top1 = np.copy(top1_test)
        p_top1[e_top1_test > evt_top1.extreme_threshold_] = -1
        all_ablations["w/o Marginalized Energy (Top-1 Conditioning)"].append(
            compute_metrics(y_test, p_top1, labels_str, known_cls, unknown_cls)
        )

        # 3. w/o POT-EVT: FAIR static quantile threshold matching the exact same target FAR (1 - q)
        probs_train = ir2.classifier.predict_proba(X_train_s[:, sel_features])
        probs_test = ir2.classifier.predict_proba(X_test_s[:, sel_features])
        e_train_full = ir2.cvae.compute_marginalized_energy(X_train_s[:, sel_features], probs_train)
        e_test_full = ir2.cvae.compute_marginalized_energy(X_test_s[:, sel_features], probs_test)
        fair_static_thresh = float(np.percentile(e_train_full, (1.0 - 1e-3) * 100))
        p_static = np.copy(top1_test)
        p_static[e_test_full > fair_static_thresh] = -1
        all_ablations["w/o POT-EVT (Fair Static Quantile @ 1-q)"].append(
            compute_metrics(y_test, p_static, labels_str, known_cls, unknown_cls)
        )

        # 4. w/o Dirichlet CMI (raw plug-in without smoothing)
        sel_raw = RobustCausalSelector(
            alpha_threshold=0.015, dirichlet_alpha=0.0, max_cond_size=1, min_stratum_samples=0
        ).fit(X_train_s, y_train)
        raw_feats = sel_raw.selected_features_
        if len(raw_feats) == 0:
            raw_feats = list(range(10))
        cls_raw = CostSensitiveClassifier(num_classes=len(known_cls)).fit(X_train_s[:, raw_feats], y_train)
        cvae_raw = MultiClassMarginalizedCVAE(input_dim=len(raw_feats), num_classes=len(known_cls), latent_dim=8)
        cvae_raw.fit_cvae(X_train_s[:, raw_feats], y_train, epochs=8)
        p_tr = cls_raw.predict_proba(X_train_s[:, raw_feats])
        p_te = cls_raw.predict_proba(X_test_s[:, raw_feats])
        e_train_raw = cvae_raw.compute_marginalized_energy(X_train_s[:, raw_feats], p_tr)
        e_test_raw = cvae_raw.compute_marginalized_energy(X_test_s[:, raw_feats], p_te)
        evt_raw = AdaptiveExtremeValueDetector(target_far=1e-3).fit(e_train_raw)
        p_raw = cls_raw.predict(X_test_s[:, raw_feats])
        p_raw[e_test_raw > evt_raw.extreme_threshold_] = -1
        all_ablations["w/o Dirichlet CMI (Raw Plug-in CMI)"].append(
            compute_metrics(y_test, p_raw, labels_str, known_cls, unknown_cls)
        )

    # Summarize Ablations
    ablation_summary = []
    numeric_keys = ["Macro_F1", "G_Mean", "FAR", "ZeroDay_Recall", "Accuracy"]
    for ab in ablation_names:
        row = {"Ablation": ab}
        for k in numeric_keys:
            vals = [res[k] for res in all_ablations[ab]]
            mean = np.mean(vals)
            std = np.std(vals)
            row[f"{k}_mean"] = round(mean, 4)
            row[f"{k}_std"] = round(std, 4)
            row[f"{k}_formatted"] = f"{mean*100:.2f}% ± {std*100:.2f}%"
        # Specific stealth & zero-day class recalls
        for ck in ["Infiltration_Recall", "Botnet_Recall", "SQLi_Recall"]:
            vals = [res[ck] for res in all_ablations[ab]]
            row[f"{ck}_formatted"] = f"{np.mean(vals)*100:.2f}% ± {np.std(vals)*100:.2f}%"
        ablation_summary.append(row)

    df_abl = pd.DataFrame(ablation_summary)
    df_abl.to_csv("results/ablations_5seeds.csv", index=False)
    print("Saved results/ablations_5seeds.csv")
    return df_abl


if __name__ == "__main__":
    print("Starting Multi-Seed Benchmark Evaluation across 5 seeds...")
    run_benchmark()
    run_ablations()
    print("Evaluation Complete!")
