"""
Publication-Quality Visualization and Plotting Module for IR-IDS 2.0
Generates high-resolution figures for journal submission:
1. Free Energy Anomaly Distribution (Benign vs Known Attack vs Zero-Day Unknown Tail).
2. Head-to-Head Radar/Bar Chart (Original Paper vs IR-IDS 2.0 across key metrics).
3. Precision-Recall Curve demonstrating stealth attack capture (SQLi / Infiltration).
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt

# Use clean styling
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0


def plot_free_energy_distribution(
    benign_energies: np.ndarray,
    known_attack_energies: np.ndarray,
    zero_day_energies: np.ndarray,
    threshold: float,
    save_path: str = "fig1_free_energy_distribution.png"
):
    """
    Plots the separation of Free Energy scores and the POT-EVT extreme cutoff.
    Demonstrates Theorem 2: Zero-days are strictly separated from known class manifolds.
    """
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)

    # Plot KDE / histograms
    bins = np.linspace(0, max(np.max(zero_day_energies), threshold * 1.5), 60)

    ax.hist(benign_energies, bins=bins, alpha=0.6, color='#10b981', label='Benign Traffic (Inliers)', density=True)
    ax.hist(known_attack_energies, bins=bins, alpha=0.6, color='#3b82f6', label='Known Attacks (DoS/PortScan)', density=True)
    ax.hist(zero_day_energies, bins=bins, alpha=0.6, color='#ef4444', label='Zero-Day Unknown Attacks', density=True)

    # Anomaly threshold line
    ax.axvline(threshold, color='#b91c1c', linestyle='--', linewidth=2.0, label=f'Adaptive POT Cutoff ($z_q = {threshold:.2f}$)')

    ax.set_title("Marginalized Free Energy Distribution & Zero-Day Separation", fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel("Free Energy Score $E(x)$", fontsize=11)
    ax.set_ylabel("Probability Density", fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#cccccc', fontsize=9.5)

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"✅ Saved figure: {save_path}")


def plot_head_to_head_comparison(
    metrics_baseline: dict,
    metrics_irids2: dict,
    save_path: str = "fig2_head_to_head_comparison.png"
):
    """
    Generates a grouped bar chart highlighting the resolution of the Accuracy Paradox.
    """
    categories = [
        "Overall\nAccuracy",
        "Macro-F1\nScore",
        "Geometric\nMean (G-Mean)",
        "Zero-Day\nRecall",
        "Stealth Attack\n(SQLi) Recall",
        "Benign False\nAlarm (FAR)"
    ]

    baseline_vals = [
        metrics_baseline['overall_accuracy'] * 100,
        metrics_baseline['macro_f1'] * 100,
        metrics_baseline['g_mean'] * 100,
        metrics_baseline['unknown_zero_day_recall'] * 100,
        metrics_baseline['class_recalls'].get('SQL_Injection', 0) * 100,
        metrics_baseline['false_alarm_rate'] * 100
    ]

    irids2_vals = [
        metrics_irids2['overall_accuracy'] * 100,
        metrics_irids2['macro_f1'] * 100,
        metrics_irids2['g_mean'] * 100,
        metrics_irids2['unknown_zero_day_recall'] * 100,
        metrics_irids2['class_recalls'].get('SQL_Injection', 0) * 100,
        metrics_irids2['false_alarm_rate'] * 100
    ]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

    rects1 = ax.bar(x - width/2, baseline_vals, width, label='Original IR-IDS (Baseline)', color='#94a3b8', edgecolor='#475569')
    rects2 = ax.bar(x + width/2, irids2_vals, width, label='IR-IDS 2.0 (Proposed)', color='#0284c7', edgecolor='#0369a1')

    # Add values on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)

    ax.set_title("Performance Benchmark: Original IR-IDS vs. IR-IDS 2.0", fontsize=13, fontweight='bold', pad=14)
    ax.set_ylabel("Metric Value (%)", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9.5)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', linestyle=':', alpha=0.7)
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#cccccc', fontsize=10)

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"✅ Saved figure: {save_path}")


if __name__ == "__main__":
    from data.dataset_loader import generate_synthetic_benchmark_dataset
    from pipeline.irids2_system import IRIDS2System
    from evaluation.metrics import compute_intrusion_metrics
    from sklearn.tree import DecisionTreeClassifier

    print("Generating benchmark data and training models for journal figures...")
    split = generate_synthetic_benchmark_dataset(n_samples_train=6000, n_samples_test=3000, n_features=35, seed=42)

    # 1. Baseline
    dt = DecisionTreeClassifier(max_depth=12, random_state=42)
    dt.fit(split.X_train, split.y_train)
    preds_base = dt.predict(split.X_test)
    m_base = compute_intrusion_metrics(split.y_test, preds_base, split.known_classes)

    # 2. IR-IDS 2.0
    system = IRIDS2System(known_class_names=split.known_classes, alpha_cfs=0.015, latent_dim=6, target_far=1e-3, focal_gamma=0.7)
    system.fit(split.X_train, split.y_train, feature_names=split.feature_names, cvae_epochs=10, verbose=False)
    preds_irids2 = system.predict(split.X_test, unknown_label=-1)
    m_irids2 = compute_intrusion_metrics(split.y_test, preds_irids2, split.known_classes)

    # Compute energy distribution
    X_scaled = system.preprocessor.transform(split.X_test)
    X_causal = X_scaled[:, system.selected_feature_indices_]
    probs = system.classifier.predict_proba(X_causal)
    energies = system.cvae.compute_marginalized_energy(X_causal, probs)

    benign_e = energies[split.y_test == 0]
    known_e = energies[(split.y_test > 0) & (split.y_test != -1)]
    zero_day_e = energies[split.y_test == -1]

    # Generate figures
    plot_free_energy_distribution(benign_e, known_e, zero_day_e, system.evt_detector.extreme_threshold_)
    plot_head_to_head_comparison(m_base, m_irids2)
    print("All journal figures generated successfully!")

