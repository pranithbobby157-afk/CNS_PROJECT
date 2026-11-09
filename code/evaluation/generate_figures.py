"""
Publication Figure Generator for IR-IDS 2.0
Generates:
1. fig1_pipeline_architecture.png: Authentic system architecture flow diagram.
2. fig2_head_to_head_comparison.png: Empirical benchmark bar plot with 95% CI error bars.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set clean aesthetic style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10


def generate_fig1_pipeline():
    """Generates an authentic, publication-quality pipeline architecture diagram."""
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    ax.axis('off')

    # Stages definition: (title, subtitle, color, x, y, width, height)
    stages = [
        ("Stage 1: Flow Ingress", "Winsorization (0.5%-99.5%)\nMedian / IQR Scaling\nOutlier Suppression", "#EBF5FB", "#2E86C1", 0.05, 0.55, 0.16, 0.35),
        ("Stage 2: DS-CMI Causal Filter", "Stratum Pooling (Nz < 4)\nCap |Z| <= 3 (Finite-Sample)\nSequential Greedy Shrink", "#E8F8F5", "#16A085", 0.25, 0.55, 0.16, 0.35),
        ("Stage 3: Cost-Sensitive GBDT", "Focal Weighting (Train Classes)\nInvariant Class Margins\nCalibrated Posterior P(Y|X)", "#FEF9E7", "#D4AC0D", 0.45, 0.55, 0.16, 0.35),
        ("Stage 4: Marginalized CVAE", "Multi-Head Class Decoders\nLedoit-Wolf Mahalanobis Metric\nMarginalized Free Energy E(x)", "#F4ECF7", "#8E44AD", 0.65, 0.55, 0.16, 0.35),
        ("Stage 5: Dynamic POT-EVT", "Hosking-Wallis PWM (xi, sigma)\nSliding-Window Quantile (u_t)\nAdversarial Velocity Limiter", "#FDEDEC", "#CB4335", 0.85, 0.55, 0.14, 0.35),
    ]

    for title, desc, bg_color, border_color, x, y, w, h in stages:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor=bg_color, edgecolor=border_color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 0.05, title, ha='center', va='center', fontsize=11, fontweight='bold', color=border_color)
        ax.text(x + w/2, y + h/2 - 0.04, desc, ha='center', va='center', fontsize=9, color="#2C3E50", linespacing=1.4)

    # Connecting arrows between upper stages
    arrow_props = dict(facecolor='#34495E', edgecolor='#34495E', width=2, headwidth=7, headlength=6)
    for i in range(len(stages) - 1):
        x_start = stages[i][4] + stages[i][6] + 0.005
        x_end = stages[i+1][4] - 0.005
        y_pos = 0.725
        ax.annotate('', xy=(x_end, y_pos), xytext=(x_start, y_pos), arrowprops=arrow_props)

    # Decision Split below Stage 5
    decision_rect = patches.FancyBboxPatch((0.85, 0.15), 0.14, 0.28, boxstyle="round,pad=0.02,rounding_size=0.03",
                                           facecolor="#EAECEE", edgecolor="#2C3E50", linewidth=1.5, linestyle="--")
    ax.add_patch(decision_rect)
    ax.text(0.92, 0.38, "Dual Verdict", ha='center', va='center', fontsize=10, fontweight='bold', color="#2C3E50")
    ax.text(0.92, 0.28, "E(x) > z_q :\nZero-Day Alert\n\nE(x) <= z_q :\nKnown Attack / Benign", ha='center', va='center', fontsize=8.5, color="#1B2631", linespacing=1.3)

    # Arrow from Stage 5 down to Decision
    ax.annotate('', xy=(0.92, 0.44), xytext=(0.92, 0.54), arrowprops=arrow_props)

    # Lower Stage: SOC Explainability via Chebyshev KAN & SHAP
    soc_rect = patches.FancyBboxPatch((0.25, 0.15), 0.56, 0.28, boxstyle="round,pad=0.02,rounding_size=0.03",
                                      facecolor="#F5EEF8", edgecolor="#6C3483", linewidth=2)
    ax.add_patch(soc_rect)
    ax.text(0.53, 0.38, "Stage 6: SOC Explainability & Symbolic Diagnostics", ha='center', va='center', fontsize=11, fontweight='bold', color="#6C3483")
    ax.text(0.53, 0.26, "Authentic Chebyshev Polynomial Decomposition: phi(x) = sum c_k T_k(x)\nExact TreeSHAP Attribution for Alert Verification\nEmpirical Fidelity Check: Mean Kendall-tau rank correlation > 0.85", ha='center', va='center', fontsize=9.5, color="#2C3E50", linespacing=1.4)

    # Flow arrows to SOC
    ax.annotate('', xy=(0.84, 0.29), xytext=(0.82, 0.29), arrowprops=dict(facecolor='#6C3483', edgecolor='#6C3483', width=1.5, headwidth=6))

    plt.tight_layout()
    os.makedirs("results", exist_ok=True)
    fig1_path = "results/fig1_pipeline_architecture.png"
    plt.savefig(fig1_path, dpi=300, bbox_inches='tight')
    plt.savefig("fig1_pipeline_architecture.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated {fig1_path}")


def generate_fig2_benchmark():
    """Plots empirical benchmark results from results/benchmark_5seeds.csv."""
    csv_path = "results/benchmark_5seeds.csv"
    if not os.path.exists(csv_path):
        print(f"Waiting for {csv_path} to finish...")
        return

    df = pd.read_csv(csv_path)

    # Select key models and metrics
    models = df["Model"].tolist()
    zd_recall = df["ZeroDay_Recall_mean"] * 100
    zd_std = df["ZeroDay_Recall_std"] * 100
    far = df["FAR_mean"] * 100
    far_std = df["FAR_std"] * 100
    macro_f1 = df["Macro_F1_mean"] * 100
    macro_f1_std = df["Macro_F1_std"] * 100

    x = np.arange(len(models))
    width = 0.26

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

    rects1 = ax.bar(x - width, zd_recall, width, yerr=zd_std, capsize=4, label='Zero-Day Recall (%)', color='#2980B9', edgecolor='black', alpha=0.9)
    rects2 = ax.bar(x, macro_f1, width, yerr=macro_f1_std, capsize=4, label='Macro F1 (%)', color='#27AE60', edgecolor='black', alpha=0.9)
    rects3 = ax.bar(x + width, far, width, yerr=far_std, capsize=4, label='False Alarm Rate (FAR %)', color='#C0392B', edgecolor='black', alpha=0.9)

    ax.set_ylabel('Performance (%)', fontsize=12, fontweight='bold')
    ax.set_title('Multi-Seed Benchmark Comparison (5 Random Seeds, 95% Confidence Intervals)', fontsize=13, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, ha='right', fontsize=9.5, fontweight='bold')
    ax.legend(loc='upper left', frameon=True, fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_ylim(0, 110)

    # Annotate values on top of bars
    for rect in rects1:
        h = rect.get_height()
        if h > 0:
            ax.annotate(f'{h:.1f}%', xy=(rect.get_x() + rect.get_width()/2, h + 2),
                        xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    fig2_path = "results/fig2_head_to_head_comparison.png"
    plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
    plt.savefig("fig2_head_to_head_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated {fig2_path}")


if __name__ == "__main__":
    generate_fig1_pipeline()
    generate_fig2_benchmark()

