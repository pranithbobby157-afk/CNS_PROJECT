# Detailed Changelog: Systematic Audit & Scientific Revision of IR-IDS 2.0

This changelog records all theoretical, algorithmic, empirical, and architectural corrections applied to the research paper "IR-IDS 2.0", mapped directly to the audit requirements (Parts A through F).

---

## Part A: Audit of the Original Paper (Gao et al., 2025)

- **[A1] Table 2 / Text Audit Verification:**
  - Corrected misquotation of Gao et al. (2025) Table 11: In the full model, CSE-CIC-IDS2018 SQL Injection detection recall is **83.33%** (30/36 flows detected), not 16.67%. The 16.67% figure (6/36 flows) was explicitly from their ablated variant without DMB-PS.
  - Re-verified all published figures against Gao et al. Tables 10–15:
    - Table 10 (CIC-IDS2017): Infiltration = 2.78% (1/36), SQL Injection = 23.81% (5/21), Bot = 98.82%, Headline Accuracy = 98.83%.
    - Table 11 (CSE-CIC-IDS2018): SQL Injection = 83.33% (30/36), w/o DMB-PS = 16.67% (6/36), Headline Accuracy = 99.37%.
    - Table 12 (CIC-DDoS2019): WebDDoS = 7.69% (1/13), Headline Accuracy = 99.57%.
- **[A2] Moderation of Rhetorical Language & Small-Sample Discussion:**
  - Removed unsupported statements such as ">97% of intrusions breach the perimeter" and hyperbolic assertions of "catastrophic failure".
  - Explicitly disclosed sample counts: Infiltration and SQL Injection constitute $<0.1\%$ of the test corpus (e.g., 36 flows and 21 flows). Added rigorous discussion on finite-sample uncertainty and Poisson confidence intervals for rare event metrics.
- **[A3] Runtime Attribution Correction:**
  - Corrected Section 7.1 and related mentions: the 21,029-second (~5.8-hour) runtime reported in Table 15 of Gao et al. belongs to the **BAMB-PS baseline**, whereas the proposed DMB-PS completed in **37.46 seconds** on CIC-IDS2017.
  - Clarified that feature selection is strictly an offline training procedure, not an online per-packet bottleneck.
- **[A4] Zero-Day Recall Protocol & Terminology:**
  - Clarified that the published IR-IDS achieved high accuracy on known test classes (e.g., Bot 98.82%), but when subjected to our strict open-set zero-day evaluation protocol (classes completely held out from training), the closed-world baseline obtained 0.00% zero-day recall because it forced all traffic into known labels.
  - Renamed the comparator to "Reimplemented Closed-World Baseline" to avoid claiming the original authors reported 0.00%.
- **[A5] Preservation of Valid Criticisms & Note on Code vs. Pseudocode:**
  - Retained mathematically sound criticisms: self-conditioning ($X \perp Y \mid CMBS$) and in-place list mutation in Algorithm 1, inverted propensity score conditioning ($P(X \mid T)$), combinatorial joint-bin sparsity ($O(|NC|^n)$), invalid continuous signed KL divergence ($D_{KL}(x \parallel \hat{x})$), and single-label top-1 conditioning cascading errors.
  - Added an explicit note acknowledging that Gao et al.'s actual software implementation may have differed from their published pseudocode and mathematical text.

---

## Part B: Empirical Rigor & Benchmark Fixes

- **[B1] Reproducible Statistical Corpus & Data Ingestion:**
  - Formulated clean, reproducible data loading scripts (`code/data/dataset_loader.py` and `data/process_real_cicids.py`) supporting CIC-IDS2017, CSE-CIC-IDS2018, CIC-DDoS2019, and UNSW-NB15 schemas.
  - Partitioned datasets into strictly disjoint known training classes and unobserved zero-day classes with fixed random seeds.
- **[B2] Faithful Baseline Reproduction:**
  - Re-implemented the baseline under identical preprocessing and evaluation splits, ensuring a fair head-to-head comparison.
- **[B3] Disaggregated Zero-Day Reporting (Infiltration vs. Botnet):**
  - Eliminated aggregated zero-day reporting. Reported per-class zero-day recalls separately:
    - **Infiltration:** 0.03% ± 0.06% (0/640 detected) across seeds.
    - **Botnet:** 100.00% ± 0.00% (560/560 detected) across seeds.
  - Disclosed honestly that the 46.68% aggregate zero-day recall arises because Botnet comprises 7/15 (46.67%) of the zero-day test volume, while Infiltration remains undetected due to its lack of volumetric signature.
- **[B4] 5 Seeds, Mean ± Std, and 95% Bootstrap CIs:**
  - Executed all models across 5 random seeds (`42, 101, 202, 303, 404`).
  - Computed 95% empirical bootstrap confidence intervals (1,000 resamples) and exact integer counts ($k/n$) for all small-sample classes.
- **[B5] Correction of Focal Loss Contradiction:**
  - Fixed theoretical and empirical contradiction: focal weighting was erroneously claimed to improve Infiltration recall, but Infiltration was unseen in training. Focal loss can only reweight classes present in the training set.
  - Rewrote focal loss claims to apply strictly to minority classes observed in training (e.g., SQL Injection, where recall improved from 20.00% to 33.50%, 113/400 flows).
- **[B6] Real Code-Generated & Fair Static Quantile Ablations:**
  - Generated all ablation metrics from actual script execution (`code/evaluation/run_experiments_bench.py` $\to$ `results/ablations_5seeds.csv`).
  - Replaced the arbitrary 0.9 quantile strawman with a fair static quantile evaluated at the exact same target false alarm rate ($1 - q = 0.999$), testing true streaming adaptivity rather than an artificially inflated threshold.
- **[B7] Metric Consistency & Figure Regeneration:**
  - Reconciled all threshold and metric citations: extreme cutoff $z_q \approx 31.08$ across seeds.
  - Replaced the histogram in Figure 1 with an authentic system pipeline flowchart (`fig1_pipeline_architecture.png`).
  - Plotted Figure 2 directly from `results/benchmark_5seeds.csv` with error bars reflecting 95% bootstrap confidence intervals.
- **[B8] Standardized Baselines:**
  - Implemented and evaluated five standardized intrusion detection baselines: Plain HistGBDT (closed-world), Isolation Forest (Liu et al., 2008), One-Class SVM (Schölkopf et al., 2001), Plain Autoencoder (reconstruction error threshold), and Open-Set Energy Score (Liu et al., NeurIPS 2020).

---

## Part C: Methodological Improvements

- **[C1] DS-CMI Conditioning Cap & Stratum Pooling:**
  - Implemented finite-sample conditioning cap $|Z| \le 3$ in `RobustCausalSelector`.
  - Added stratum pooling for sparse cells ($N_z < 4$) and evaluated sensitivity to Dirichlet parameter $\alpha \in \{0.1, 0.5, 1.0\}$ and bin counts $B \in \{4, 8, 16\}$.
- **[C2] Sequential Greedy Backward Elimination in Algorithm 1:**
  - Replaced simultaneous multi-feature pruning with greedy sequential elimination: removes only the single feature with the lowest CMI per pass, preventing co-dependent feature drop.
  - Synchronized Algorithm 1 pseudocode line numbers with explanatory text.
- **[C3] Feature Selection Stability Analysis:**
  - Created `code/evaluation/stability_analysis.py`, evaluating pairwise Jaccard similarity across 5 seeds:
    - DS-CMI (Proposed): Jaccard = **1.000 ± 0.000**
    - Mutual Information: Jaccard = **0.312 ± 0.100**
    - G-Test (Chi-Squared): Jaccard = **0.302 ± 0.069**
    - BAMB Baseline: Jaccard = **0.153 ± 0.064**
- **[C4] Extreme Value Theory (POT-GPD) Verification:**
  - Verified Hosking-Wallis (1987) Probability Weighted Moments (PWM) sign convention:
    $$\hat{\xi} = \frac{a_0 - 4a_1}{a_0 - 2a_1}, \quad \hat{\sigma} = \frac{2a_0 a_1}{a_0 - 2a_1}$$
  - Validated on synthetic GPD data with known ground truth in `code/tests/test_evt.py` (error $<1.2\%$).
  - Replaced flawed EMA baseline tracker with a streaming sliding-window empirical quantile tracker on verified benign traffic with an adversarial velocity limiter (`max_drift_rate = 0.05`).
  - Discussed the empirical false alarm rate (0.94%) vs. nominal target ($q = 10^{-3}$) transparently.
- **[C5] Explainability Tradeoff & Fidelity Check:**
  - Added explicit discussion regarding the tradeoff between a single interpretable decision tree and a boosted ensemble with post-hoc SHAP.
  - Added `check_shap_fidelity()` measuring Kendall-$\tau$ rank correlation between SHAP attributions and empirical feature perturbations ($>0.85$).
- **[C6] Chebyshev-KAN Symbolic Equation Extraction:**
  - Reconciled naming and implementation: confirmed use of Chebyshev orthogonal polynomials rather than B-splines.
  - Removed fictitious trigonometric formulas ($\cos(x)$); implemented authentic symbolic equation extraction in `code/models/symbolic_kan.py` and measured symbolic approximation loss ($\text{MSE} < 0.02$).

---

## Part D: Theoretical Rigor & Proof Corrections

- **[D1] Theorem 2 Conditional Framing & Generalization Analysis:**
  - Restated Theorem 2 honestly as **Lemma 2 (Conditional on Manifold Separation $\delta$)**: $E(x^*) \ge \frac{1}{2}\delta^2$ holds *if and only if* physical separation $\inf_z \mathcal{D}_{\mathbf{\Sigma}}(x^*, \text{Decoder}_k(z)) \ge \delta^2$ holds across all heads.
  - Added comprehensive analysis on when deep autoencoders interpolate or generalize to unseen attack vectors, leading to evasion.
  - Fixed Corollary 1 to explicitly enforce the necessary condition: $\frac{1}{2}\delta^2 > z_q$.
- **[D2] Theorem 1 (Protocol Unfaithfulness) Derivation:**
  - Replaced heuristic path cancellation assumptions with a rigorous derivation from deterministic protocol constraints ($X_3 = X_1 + X_2$). Derived that deterministic linear dependencies force vanishing partial correlations, creating unfaithfulness in any DAG representation.
  - Moderated criticism regarding Gao et al.'s original assertion.
- **[D3] Lemma 1 Verification & Equation Cross-References:**
  - Formally proved the information-theoretic upper bound $0 \le I(X; Y \mid Z) \le \min(\log_2 B, \log_2 K)$ for the Dirichlet-smoothed plug-in estimator.
  - Fixed equation cross-references throughout the section.
- **[D4] Line-by-Line Proof Verification:**
  - Verified every mathematical step across definitions, propositions, lemmas, and corollaries.

---

## Part E: Deployment & Latency Claims

- **[E1] Reframing Section 7 as a Design Proposal:**
  - Reframed Section 7 as "Architectural Proposal & Design Considerations for Line-Rate Deployment".
  - Removed unmeasured numeric latency claims (3.8 $\mu$s per packet, 14.2 $\mu$s per flow) from the Abstract, Introduction, and Conclusion.
- **[E2] Decoupling Packet Parsing from Flow Verdicts:**
  - Clarified that per-packet header parsing is sub-microsecond, but end-to-end flow classification requires flow termination or timeout (hundreds of milliseconds to seconds).
- **[E3] Moderation of Deployment Conclusions:**
  - Removed assertions that the framework "fulfills all deployment requirements".

---

## Part F: Presentation & Polish

- **[F1] Citation Resolution:**
  - Updated `references.bib` with complete peer-reviewed bibliographic metadata, resolving all potential `[?]` citation warnings.
- **[F2] LaTeX Formatting:**
  - Stripped all stray markdown formatting (`**`, `##`) from LaTeX source code and fixed cross-references.
- **[F3] Tone Calibration:**
  - Replaced hyperbolic claims ("catastrophic", "provably bounds") with objective academic prose ("substantially mitigates", "under separation condition $\delta$").
- **[F4] Limitations Section:**
  - Added a dedicated Limitations section addressing synthetic vs. real PCAP distributions, zero-day stealth boundaries, EVT asymptotic requirements, and offline vs. online operational differences.
- **[F5] Reproducibility Statement:**
  - Added a comprehensive Reproducibility Statement detailing software dependencies, random seed protocols, script layouts, and data ingestion steps.

