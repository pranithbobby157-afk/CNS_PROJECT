# IR-IDS 2.0: A Causally Invariant, Cost-Sensitive, and Symbolically Explainable Framework for Zero-Day Network Intrusion Detection

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains the scientific codebase, reproducible experimental benchmarks, mathematical proofs, and publication-ready LaTeX manuscripts for **IR-IDS 2.0**.

IR-IDS 2.0 provides an exhaustive theoretical and empirical audit of the recently proposed IR-IDS framework (Gao et al., 2025, *Computers & Security* 155:104496), rectifying five foundational vulnerabilities and establishing a scientifically sound, honestly evidenced standard for zero-day network intrusion detection.

---

## 🔍 Key Vulnerabilities in Gao et al. (2025) & IR-IDS 2.0 Solutions

| Dimension | Published Paper (Gao et al., 2025) | Critical Limitation | IR-IDS 2.0 Solution |
| :--- | :--- | :--- | :--- |
| **Causal Selection** | "DMB-PS" ($P(X \mid T)$ and joint grid binning) | Inverted propensity conditioning; joint grid state explosion ($O(\|NC\|^n) \approx 5.76 \times 10^{11}$ cells) inducing severe sample sparsity. | **Dirichlet-Smoothed CMI (DS-CMI)**: Quantile equal-depth partitions, Jeffreys prior ($\alpha=0.5$), finite conditioning cap ($\|Z\| \le 3$), and stratum pooling. |
| **Algorithm 1 Logic** | Tests $X \perp Y \mid CMBS$ with $X \in CMBS$; list mutated in-loop. | Self-conditioning trivializes the test ($I(X; Y \mid X, Z) \equiv 0$); in-place `.remove()` skips elements during iteration. | **Evaluated on $CMBS \setminus \{X\}$**; sequential greedy backward elimination drops only the single lowest CMI feature per pass. |
| **Pre-Classifier & Rare Classes** | Unweighted "Shapley Tree" | **Accuracy Paradox**: High headline accuracy ($98.83\%$), but stealth attacks collapsed (Infiltration at 2.78\%, SQLi at 16.67\%–23.81\%). | **Cost-Sensitive HistGBDT with Balanced Focal Loss**: Scales inverse-class penalties on training classes, lifting SQLi recall from 19.90\% to 33.50\% ± 8.98\%. |
| **Reconstruction Metric** | KL-Divergence $D_{KL}(x \parallel \hat{x})$ on feature vectors | Continuous signed feature vectors are not probability densities; KL divergence violates information theory. | **Regularized Mahalanobis Distance**: Scaled by the Ledoit–Wolf shrinkage covariance matrix $\mathbf{\Sigma}$. |
| **Zero-Day Pipeline** | Hard top-1 label feed: Classifier $\to \hat{y} \to \text{CVAE}(\hat{y})$ | **Cascading Error**: Classifier mispredicts zero-day into known class; CVAE reconstructs under wrong label, suppressing anomaly error. | **Marginalized Free Energy**: Evaluates reconstruction consensus across all class hypotheses weighted by posterior probabilities. |
| **Tail Anomaly Gate** | Static 0.9 quantile cutoff | Arbitrary thresholding guaranteeing high false alarms; EMA baseline tracker pulled threshold toward the mean. | **Verified Hosking–Wallis POT-EVT**: Closed-form PWM parameter recovery; streaming sliding-window quantile tracker with drift limiter. |
| **Explainability** | Uninspected 12-node KAN layer | No formulas, splines, or equations shown. | **Chebyshev-KAN Decomposition**: Orthogonal Chebyshev polynomials with $L_1$ pruning exporting explicit algebraic formulas and SHAP fidelity. |

---

## 📁 Repository Structure

```
CNS_PROJECT/
├── paper.tex                      # Full-length IEEEtran LaTeX journal source (~760 lines)
├── paper_elsevier.tex             # Full-length Elsevier Computers & Security format
├── references.bib                 # Complete BibTeX bibliography (35 peer-reviewed citations)
├── fig1_pipeline_architecture.png # Publication-grade system architecture flowchart
├── fig2_head_to_head_comparison.png # 5-seed empirical benchmark bar plot (95% CI)
├── IR_IDS_2_0_Research_Paper.pdf  # Compiled publication PDF with embedded figures & tables
├── IR_IDS_2_0_LaTeX_Source.zip    # Standalone LaTeX archive ready for Overleaf / TeX Live
├── IR_IDS_2_0_Research_Package.zip# Complete package ZIP (LaTeX + Code + Results + Docs)
├── CLAIMS_LOG.md                  # Verification ledger mapping every number to its source
├── CHANGELOG.md                   # Systematic item-by-item record of all revisions
├── DEFENSE_GUIDE.md               # Comprehensive Q&A defense preparation guide
├── TODO.md                        # Compute constraints & large PCAP ingestion notes
│
├── code/                          # Production-grade algorithmic implementation
│   ├── models/
│   │   ├── causal_feature_selection.py  # DS-CMI causal selector with conditioning cap
│   │   ├── cost_sensitive_classifier.py # Balanced Focal HistGBDT & SHAP fidelity check
│   │   ├── marginalized_cvae.py         # Multi-head CVAE & Marginalized Free Energy
│   │   ├── dynamic_evt.py               # Hosking-Wallis PWM EVT & streaming quantile tracker
│   │   ├── symbolic_kan.py              # Chebyshev-KAN polynomial layer & formula extraction
│   │   └── baselines.py                 # 5 standard baselines (IF, OC-SVM, AE, Energy, GBDT)
│   ├── data/
│   │   ├── dataset_loader.py            # Reproducible multi-seed benchmark splits
│   │   └── preprocessor.py              # Winsorization & Median/IQR robust scaling
│   ├── pipeline/
│   │   └── irids2_system.py             # End-to-end integrated IR-IDS 2.0 pipeline
│   ├── evaluation/
│   │   ├── run_experiments_bench.py     # 5-seed benchmark & fair ablation evaluation
│   │   ├── stability_analysis.py        # Jaccard stability analysis across 5 seeds
│   │   └── generate_figures.py          # High-resolution publication figure generator
│   └── tests/
│       └── test_evt.py                  # Unit test verifying PWM parameter estimation on GPD
│
└── results/                       # Raw CSV outputs & publication figures
    ├── benchmark_5seeds.csv             # 5-seed metrics across all models (95% bootstrap CIs)
    ├── per_class_recalls_5seeds.csv     # Disaggregated recalls (Infiltration vs. Botnet vs. SQLi)
    ├── ablations_5seeds.csv             # Fair ablation study results
    └── feature_stability.csv            # Pairwise Jaccard stability across 5 seeds
```

---

## 🚀 Quickstart & Verification

### 1. Verify Unit Tests
Validate that the Hosking–Wallis Probability Weighted Moments estimator accurately recovers GPD shape ($\xi$) and scale ($\sigma$) parameters against known ground truth:
```bash
python code/tests/test_evt.py
```
*Output: Ground Truth $\xi=0.200, \sigma=2.500 \to$ Estimated $\xi=0.198, \sigma=2.469$ ($<1.2\%$ error). PASSED.*

### 2. Execute 5-Seed Benchmark & Fair Ablations
Run the complete multi-seed evaluation across Plain HistGBDT, Isolation Forest, One-Class SVM, Plain Autoencoder, Open-Set Energy, Reimplemented Baseline, and IR-IDS 2.0:
```bash
python code/evaluation/run_experiments_bench.py
```
*Generates `results/benchmark_5seeds.csv`, `results/per_class_recalls_5seeds.csv`, and `results/ablations_5seeds.csv`.*

### 3. Run Feature Stability Analysis
Evaluate pairwise Jaccard feature selection stability across 5 seeds:
```bash
python code/evaluation/stability_analysis.py
```
*Outputs: DS-CMI Jaccard = $1.000 \pm 0.000$, Mutual Information = $0.312 \pm 0.100$, BAMB = $0.153 \pm 0.064$.*

### 4. Regenerate Publication Figures
```bash
python code/evaluation/generate_figures.py
```
*Generates high-resolution figures: `fig1_pipeline_architecture.png` and `fig2_head_to_head_comparison.png`.*

### 5. Compile Publication PDF
```bash
python build_paper_pdf.py
```
*Compiles the complete manuscript into `IR_IDS_2_0_Research_Paper.pdf`.*

---

## 📊 Key Experimental Findings

1. **Disaggregated Zero-Day Recall:**
   Our 5-seed benchmark shows that the aggregate 46.68% zero-day recall breaks down into **100.00% detection of unseen Botnet attacks** ($560/560$ flows) and **0.03% detection of Infiltration** ($0/640$ flows). Because Infiltration flows mimic normal administrative traffic without rate bursts, neither deep autoencoders nor unsupervised density estimators detect them without high false alarms. We report this breakdown openly.
2. **False Alarm Suppression:**
   While the reimplemented baseline produced an unviable 19.12% ± 0.92% false alarm rate on benign traffic, IR-IDS 2.0 bounded false alarms to **0.94% ± 0.28%** (under 1%).
3. **Focal Weighting on Minority Classes:**
   Balanced Focal Loss elevated minority SQL Injection recall from 19.90% to **33.50% ± 8.98%** (113/400 flows detected) across 5 seeds without compromising volumetric DoS detection.

---

## 👥 Authors & Contributors

- **V Bobby Pranith** — `CS23I1046`
- **Revanth V Mandava** — `CS23B1009`
- **T Balaji** — `CS23B1020`

*Department of Computer Science and Engineering, Indian Institute of Information Technology, Design and Manufacturing (IIITDM), Kancheepuram, India.*

---

## 📝 Citation & Contact
For inquiries or citation metadata:
```bibtex
@article{irids2026,
  title={{IR-IDS 2.0: A Causally Invariant, Cost-Sensitive, and Symbolically Explainable Framework for Zero-Day Network Intrusion Detection}},
  author={Pranith, V Bobby and Mandava, Revanth V and Balaji, T},
  journal={IEEE Transactions on Information Forensics and Security},
  year={2026},
  note={Under Review}
}
```
*Repository Maintainer:* [V Bobby Pranith](https://github.com/pranithbobby157-afk)
