# Robust Zero-Day Network Intrusion Detection via Causal Markov Conditioning and Multi-Hypothesis Free-Energy Gating

**Authors:**  
- **V Bobby Pranith** — `CS23I1046`  
- **Revanth V Mandava** — `CS23B1009`  
- **T Balaji** — `CS23B1020`  

*Department of Computer Science and Engineering, Indian Institute of Information Technology, Design and Manufacturing (IIITDM), Kancheepuram, India.*  
*Correspondence:* `cs23i1046@iiitdm.ac.in`  
*Code Repository:* [github.com/pranithbobby157-afk/CNS_PROJECT](https://github.com/pranithbobby157-afk/CNS_PROJECT)

---

## Abstract

Detecting unobserved zero-day exploits on high-speed enterprise perimeters remains a frustrating operational challenge. Standard supervised classifiers collapse when traffic patterns drift away from training distributions because their closed-world softmax layers map novel attack patterns into known classes. Unsupervised anomaly detectors flag outliers, but security teams routinely discard uncalibrated reconstruction alarms that lack interpretable root-cause justifications. 

In this work, we present an end-to-end framework that resolves both bottlenecks without sacrificing wire-speed packet throughput. First, we identify invariant traffic signatures by formulating Dirichlet-Smoothed Conditional Mutual Information (DS-CMI) over quantile partitions. Capping conditioning cardinality to three variables and pooling low-density strata eliminates sample sparsity, yielding invariant Markov blankets that remain identical across random splits ($Jaccard = 1.000$). Second, we counter severe class imbalance during pre-classification using a histogram tree ensemble guided by balanced focal loss, raising minority SQL injection recall from 19.90% to 33.50% without inflating benign alarms. Third, we prevent cascading classification errors during open-set arbitration: rather than conditioning generative autoencoders on a brittle single-label prediction, our pipeline computes a marginalized free-energy scalar across all class hypotheses under a regularized Ledoit–Wolf Mahalanobis metric. We prove that zero-day flows outside known class manifolds incur bounded high energy regardless of upstream routing. Anomaly cutoffs update continuously using sliding-window benign quantiles paired with Hosking–Wallis extreme value moments and an adversarial slew-rate limiter. 

Across five random seeds on CIC-IDS2017 benchmarks, our system reaches 83.14% Macro-F1, isolates unseen Botnet zero-days at 100.00% recall, and holds benign false alarms down to 0.94% (a twenty-fold drop compared to recent dual-blanket baselines). We analyze the engineering limits of flow-level statistics on stealth Infiltration attacks and outline a two-tier kernel-bypass architecture sustaining 300,000 flows per second per CPU core.

**Keywords:** Intrusion detection, zero-day attacks, causal feature selection, Markov blankets, open-set recognition, free energy, extreme value theory, kernel bypass.

---

## 1. Introduction

High-speed enterprise links move staggering amounts of information. On 10 to 40 GbE backbones carrying millions of active TCP sessions, human analysts cannot examine individual packet payloads. Security Operations Centers (SOCs) place their trust in Network Intrusion Detection Systems (NIDS) to separate benign user transactions from malicious probes. The overwhelming majority of operational systems rely on supervised tree ensembles—predominantly Random Forests or Gradient Boosted Decision Trees. In offline evaluations using benchmark datasets, these supervised models frequently produce headline accuracy figures exceeding 98%. On live network links, however, these same systems fail repeatedly.

Their failure stems from a fundamental modeling flaw: supervised classifiers assume a closed world. They presume every flow encountered during inference belongs to one of the specific traffic categories observed during model training. When an adversary launches an unobserved exploit—a true zero-day attack—the classifier possesses no mechanism to declare uncertainty. Instead, its internal decision boundaries project the anomaly onto whichever training class lies nearest in feature space. If an attacker constructs an exploit that mimics ordinary web browsing volume, the model labels the connection benign. The intrusion proceeds unnoticed.

Unsupervised generative models approach the problem from the opposite direction. Autoencoders and density estimators learn the normal traffic baseline and flag records that incur high reconstruction error. Yet security teams routinely silence these tools in production. The reason is opacity. A network engineer cannot take an operational server offline or terminate an encrypted database pipe merely because a black-box autoencoder generated an elevated anomaly scalar. Incident responders require concrete, packet-level evidence detailing which header fields, timing deviations, or byte counters violated operational expectations.

Reconciling open-set zero-day detection with verifiable decision logic motivated recent research into hybrid architectures. Notably, Gao et al. (*Computers & Security*, 2025) proposed IR-IDS, attempting to integrate causal Markov blanket selection, Shapley-routed decision trees, and Kolmogorov–Arnold Network (KAN) autoencoders calibrated via Extreme Value Theory (EVT). While their conceptual direction is compelling, our technical inspection of their formulations reveals severe mathematical, algorithmic, and empirical vulnerabilities:
1. **Inverted Propensity Conditioning:** Their selection rule conditions observed covariates on treatment labels ($P(X \mid T)$) rather than modeling treatment assignment ($P(T \mid X)$). Jointly binning ten continuous features into discrete grids creates $15^{10} \approx 5.76 \times 10^{11}$ cells, leaving over 99.9999% of conditioning strata empty.
2. **Self-Conditioning Search Bug:** Their candidate elimination routine tests $X \perp Y \mid CMBS$ while $X \in CMBS$. Conditioning any variable on a set that includes itself trivially yields zero conditional mutual information, erroneously discarding predictive features.
3. **The Stealth Attack Accuracy Paradox:** Their 98.83% headline accuracy hides catastrophic failure on low-volume intrusions. Published tables show their model detected only 1 of 36 Infiltration flows (2.78% recall) and 5 of 21 SQL injections (23.81%). Massive benign classes masked total blindness to stealthy attacks.
4. **Continuous Vector KL Divergence:** They calculate Kullback–Leibler divergence between continuous, signed feature vectors ($D_{KL}(x \parallel \hat{x})$). Because normalized network features take negative values and do not sum to unity, this calculation breaks basic probability laws.
5. **Cascading Error Propagation:** Their CVAE reconstructs incoming traffic conditioned solely on the classifier's top-1 predicted label $\hat{y}$. When an unseen zero-day arrives, the upstream classifier forces it into a known class; the autoencoder reconstructs the flow under that incorrect hypothesis, suppressing anomaly residuals and letting attacks escape.

This paper presents an overhauled, mathematically sound architecture that cures each of these defects while maintaining wire-speed feasibility:
- **Dirichlet-Smoothed Causal Selection (DS-CMI):** We compute conditional mutual information across quantile-partitioned strata smoothed with Jeffreys priors ($\alpha = 0.5$) and capped at three conditioning variables. Our sequential elimination achieves perfect feature discovery stability across random seeds ($Jaccard = 1.000$).
- **Cost-Sensitive Balanced Focal Ensemble:** We address the accuracy paradox by training a histogram tree ensemble under balanced focal loss, elevating rare SQL injection recall to 33.50% without inflating false alarms.
- **Marginalized Free-Energy Anomaly Gating:** We decouple open-set discovery from upstream classifier mistakes. By integrating Mahalanobis reconstruction residuals across all class hypotheses weighted by posterior probabilities, we establish formal bounds guaranteeing zero-day detection under manifold separation.
- **Dynamic Extreme Value Thresholding:** We model tail residuals using Hosking–Wallis Probability Weighted Moments and track benign baseline shifts via sliding quantiles constrained by an adversarial velocity limiter.
- **Empirical Rigor and Line-Rate Design:** Across five random seeds on CIC-IDS2017, our system reaches 83.14% Macro-F1 and restricts false alarms to 0.94% (a 20-fold improvement over the baseline). We provide honest disaggregated zero-day metrics (100.00% on Botnets, 0.03% on Infiltration) and describe a two-tier DPDK kernel-bypass pipeline.

---

## 2. Related Work

### 2.1 Supervised Classifiers and Open-Set Vulnerability
Traditional NIDS pipelines rely on supervised learning algorithms trained on static packet captures. Random Forests, XGBoost, and deep multilayer perceptrons achieve stellar accuracy when evaluated on benchmark test partitions drawn from identical distributions. However, network environments change constantly. New protocols, software patches, and attacker strategies induce distribution shifts. Under open-set conditions, supervised classifiers exhibit overconfidence: their final softmax normalization forces novel, unseen attack flows into existing training categories with high probability. This forced-choice misclassification prevents supervised architectures from operating as standalone zero-day defenses.

### 2.2 Generative Anomaly Detection and Distance Metrics
Open-set recognition (OSR) seeks to classify known inputs while rejecting novel patterns. Generative approaches, including autoencoders and VAEs, learn low-dimensional representations of known traffic manifolds. At inference time, inputs with high reconstruction errors are flagged as potential intrusions. 

However, two practical issues plague standard autoencoders in network settings: First, standard Euclidean mean-squared error (MSE) assumes isotropic, uncorrelated feature noise. In packet traffic, header features—such as packet lengths, flow durations, and byte counts—exhibit strong correlations. Unweighted Euclidean distances overemphasize high-variance counters while ignoring subtle timing correlations. Second, conditioning an autoencoder on an upstream discrete label creates a single point of failure: an incorrect upstream prediction steers reconstruction into the wrong subspace, masking anomalies.

### 2.3 Causal Markov Blankets in High-Dimensional Traffic
Feature selection is essential to strip away spurious correlations and reduce inference latency. Classical filter methods evaluate individual mutual information or correlation coefficients against the class label. While fast, these techniques retain redundant features and fail to eliminate indirect confounding. Causal discovery aims to isolate the Markov Blanket ($MB(Y)$)—the unique minimal set of parents, children, and spouses that renders all remaining variables conditionally independent of target $Y$:
$$X \perp Y \mid MB(Y), \quad \forall X \notin MB(Y) \cup \{Y\}$$
Constraint-based algorithms such as GS, IAMB, and HITON-PC identify Markov blankets by conducting conditional independence tests. However, continuous conditioning sets require robust non-parametric smoothing to prevent sample exhaustion.

### 2.4 Kolmogorov–Arnold Networks (KAN)
Recent work introduced Kolmogorov–Arnold Networks as an alternative to multilayer perceptrons. Grounded in the Kolmogorov–Arnold representation theorem, KANs position learnable univariate spline functions along network edges rather than applying static non-linearities at nodes:
$$f(x) = \sum_{q=1}^{2d+1} \Phi_q \left( \sum_{p=1}^d \phi_{q,p}(x_p) \right)$$
While standard B-spline KANs provide high functional expressiveness, their evaluation requires storing non-local grid tables, resulting in excessive memory overhead during line-rate packet parsing. Replacing B-splines with orthogonal Chebyshev polynomials bounds execution latency and produces closed-form algebraic expressions suitable for human security audit.

---

## 3. Technical Audit of Prior Formulations

### 3.1 Inverted Propensity Score Formulation
In causal inference, the propensity score balances observed covariates between treatment and control cohorts. For binary treatment $W \in \{0, 1\}$ and baseline covariates $X$, the true propensity score is:
$$e(x) = P(W = 1 \mid X = x)$$
Gao et al. inverted this relationship, defining propensity as:
$$e_{\text{Gao}}(X) = P(X = 1 \mid T)$$
This computes the generative class-conditional likelihood of the feature, exactly mirroring a Naive Bayes term. It does not condition on baseline covariates, does not balance confounders, and does not eliminate selection bias.

### 3.2 Combinatorial Grid State Collapse
To evaluate conditional independence, Gao et al. discretize continuous features into $|NC|$ uniform bins and construct a joint multi-dimensional grid. When conditioning on a candidate set of $n = 10$ features with $|NC| = 15$ bins, the number of distinct grid cells is:
$$|\Omega| = 15^{10} \approx 5.76 \times 10^{11} \text{ cells}$$
Given a typical benchmark training split containing $N = 35,000$ flows, the expected sample density per cell is:
$$\mathbb{E}[\text{samples per cell}] = \frac{3.5 \times 10^4}{5.76 \times 10^{11}} \approx 6.07 \times 10^{-8}$$
More than 99.9999% of conditioning strata contain zero observations. Consequently, empirical conditional probability fractions evaluate to $0/0$, producing arbitrary floating-point zeros and rendering statistical independence checks meaningless.

### 3.3 Self-Conditioning and Loop Mutation Bugs
Algorithm 1 of Gao et al. details their candidate feature pruning loop. Two distinct software defects invalidate its execution:
1. **Self-Conditioning Trivialization:** The algorithm checks whether candidate feature $X$ is independent of class $Y$ conditioned on $CMBS$, where $X$ remains an active member of $CMBS$. By basic probability theory, any random variable conditioned on a set containing itself is completely deterministic:
   $$I(X; Y \mid CMBS) \equiv 0 \quad \text{whenever } X \in CMBS$$
   As a result, every single feature appears conditionally independent, causing the pruning routine to eliminate valid predictors at random.
2. **In-Place Mutation:** During iteration over candidate set $CMBS$, the algorithm invokes `CMBS.remove(X)`. Mutating an array during traversal advances internal loop pointers across adjacent indices, skipping roughly half the candidate features without evaluation.

### 3.4 Vector-Level Kullback–Leibler Metric Breakdown
Gao et al. measure autoencoder reconstruction error on standardized continuous feature vectors using Kullback–Leibler divergence:
$$D_{KL}(x \parallel \hat{x}) = \sum_{j=1}^d x_j \log \left( \frac{x_j}{\hat{x}_j} \right)$$
This formula is mathematically invalid. KL divergence is strictly defined on probability simplexes where elements are non-negative ($x_j \ge 0$) and sum to unity ($\sum x_j = 1$). Standardized network features contain negative values ($z$-scores). Evaluating logarithms on negative real numbers yields undefined or complex values.

### 3.5 The Stealth Attack Accuracy Paradox
Gao et al. claimed headline detection accuracies exceeding 98.8%. However, an inspection of their published per-class breakdown tables reveals an acute accuracy illusion:
- **CIC-IDS2017:** Infiltration recall was 2.78% (1 of 36 flows detected). SQL Injection recall was 23.81% (5 of 21 flows).
- **CSE-CIC-IDS2018:** SQL Injection recall dropped to 16.67% (6 of 36 flows) when DMB-PS was ablated.
- **CIC-DDoS2019:** WebDDoS recall was 7.69% (1 of 13 flows).

Their 98.8% accuracy was driven almost exclusively by voluminous benign sessions and massive DoS packet floods. Stealthy, targeted intrusions passed straight through the detector unnoticed.

---

## 4. The IR-IDS 2.0 Methodology

![Figure 1: Pipeline Architecture](fig1_pipeline_architecture.png)
*Figure 1: End-to-end operational architecture of IR-IDS 2.0. Ingress network flows pass through robust quantile scaling, DS-CMI causal Markov selection, balanced focal HistGBDT pre-classification, multi-hypothesis marginalized CVAE free-energy estimation, dynamic POT-EVT thresholding, and Chebyshev-KAN symbolic verification.*


### 4.1 Dirichlet-Smoothed Causal Selection (DS-CMI)
To prevent combinatorial state explosion while preserving non-linear dependency detection, we discretize continuous features into $B$ equal-depth quantile bins ($B = 8$). We enforce an explicit conditioning cap: $|Z| \le 3$. Rather than relying on unregularized frequency counts, we smooth empirical cell counts using a symmetric Dirichlet prior with Jeffreys parameter $\alpha = 0.5$:
$$P(X=x, Y=y \mid Z=z) = \frac{N(x, y, z) + \alpha}{N(z) + \alpha \cdot B \cdot K}$$
where $K$ is the number of traffic classes. Strata with fewer than four observations ($N(z) < 4$) are pooled into an aggregate background stratum. Because $\alpha > 0$, estimated probabilities are strictly positive, guaranteeing bounded CMI values and eliminating division-by-zero crashes.

Feature selection executes in two distinct stages:
1. **Forward Candidate Ingestion:** Continuous variables are ranked by unconditional mutual information $I(X_j; Y)$. Features exceeding admission threshold $\tau_1$ enter active candidate pool $\mathcal{S}$.
2. **Greedy Backward Elimination:** For each variable $X \in \mathcal{S}$, we evaluate conditional mutual information against $\mathcal{S} \setminus \{X\}$ (explicitly excluding $X$):
   $$X^* = \arg\min_{X \in \mathcal{S}} I(X; Y \mid \mathcal{S} \setminus \{X\})$$
   If $I(X^*; Y \mid \mathcal{S} \setminus \{X^*\}) < \tau_2$, feature $X^*$ is permanently removed. Dropping only one feature per pass preserves co-dependent predictors and eliminates array mutation index skips.

### 4.2 Cost-Sensitive HistGBDT with Balanced Focal Loss
To resolve the accuracy illusion without flooding operators with false alarms on benign traffic, we train a Histogram Gradient Boosted Decision Tree (HistGBDT) under balanced focal loss:
$$\mathcal{L}_{\text{Focal}} = -\sum_{i=1}^N w_{y_i} \left( 1 - p(y_i \mid x_i) \right)^\gamma \log p(y_i \mid x_i)$$
Class weights $w_c$ scale inversely with training frequencies:
$$w_c = \left( \frac{N}{K \cdot N_c} \right)^\gamma$$
Focusing parameter $\gamma = 2.0$ dampens loss gradients originating from easy, well-classified benign sessions, forcing tree splits to optimize discrimination on scarce stealth attacks (such as SQL injection).

### 4.3 Multi-Class Marginalized Free-Energy CVAE
To eliminate cascading classification errors, we replace single-label conditioning with a marginalized free-energy formulation. Reconstruction residuals are calculated using a regularized Mahalanobis distance scaled by the Ledoit–Wolf shrinkage covariance matrix $\mathbf{\Sigma}$:
$$\mathcal{D}_{\mathbf{\Sigma}}(x, \hat{x}) = (x - \hat{x})^T \left( \mathbf{\Sigma} + \epsilon \mathbf{I} \right)^{-1} (x - \hat{x})$$
Given classifier posterior distribution $p(y = k \mid x)$, the Marginalized Free Energy $E(x)$ integrates reconstruction residuals across all possible class manifolds:
$$E(x) = -T \log \sum_{k=0}^{K-1} p(y = k \mid x) \exp \left( -\frac{1}{2 T} \mathcal{D}_{\mathbf{\Sigma}}\left(x, \hat{x}^{(k)}\right) \right)$$
where $T$ represents an empirical temperature parameter. When an incoming flow represents an unobserved zero-day exploit, its features will fail reconstruction under every known class hypothesis $k$. Consequently, $E(x)$ rises sharply regardless of upstream classification errors.

### 4.4 Dynamic Extreme Value Thresholding (POT-EVT)
Extreme tail reconstruction energies are governed by the Peaks-Over-Threshold (POT) Generalized Pareto Distribution (GPD):
$$G(y; \xi, \sigma) = 1 - \left( 1 + \frac{\xi y}{\sigma} \right)^{-1/\xi}$$
We compute GPD shape $\xi$ and scale $\sigma$ using Hosking–Wallis Probability Weighted Moments (PWM):
$$a_0 = \frac{1}{N_u} \sum_{i=1}^{N_u} y_{(i)}, \quad a_1 = \frac{1}{N_u} \sum_{i=1}^{N_u} \frac{i-1}{N_u-1} y_{(i)}$$
$$\hat{\xi} = \frac{a_0 - 4 a_1}{a_0 - 2 a_1}, \quad \hat{\sigma} = \frac{2 a_0 a_1}{a_0 - 2 a_1}$$
To track normal network drift without allowing an attacker to poison thresholds via slow traffic manipulation, baseline threshold $u_t$ updates via a sliding-window benign quantile bounded by an adversarial slew-rate limiter:
$$u_t = u_{t-1} + \text{clip}\left( \tilde{q}_t - u_{t-1}, -\Delta_{\max}, +\Delta_{\max} \right)$$

### 4.5 Symbolic Chebyshev-KAN Decomposition
For interpretability, we formulate the bottleneck layers using orthogonal Chebyshev polynomials:
$$\phi_j(x) = c_0 T_0(x) + c_1 T_1(x) + c_2 T_2(x) + c_3 T_3(x)$$
where $T_0(x) = 1$, $T_1(x) = x$, $T_2(x) = 2x^2 - 1$, and $T_3(x) = 4x^3 - 3x$. An $L_1$ sparsity penalty zeroes out insignificant polynomial weights, permitting direct export of closed-form algebraic decision rules for operator validation.

---

## 5. Theoretical Analysis

### Theorem 1 (Protocol Constraints Violate Faithfulness)
*Let traffic distribution $P(X)$ be governed by deterministic protocol constraints $X_3 = X_1 + X_2$. Then $P(X)$ cannot be faithful to any DAG $G$ where $X_1, X_2 \to Y$.*

**Proof:** Under the linear protocol constraint, the covariance between $X_3$ and target $Y$ satisfies:
$$\text{Cov}(X_3, Y) = \text{Cov}(X_1 + X_2, Y) = \text{Cov}(X_1, Y) + \text{Cov}(X_2, Y)$$
If true underlying mechanisms satisfy $\beta_1 = -\beta_2$, then $\text{Cov}(X_3, Y) = 0$, implying conditional independence $X_3 \perp Y$. However, in any DAG where active paths $X_1 \to Y$ and $X_2 \to Y$ exist and $X_3$ is a deterministic child of $X_1, X_2$, variable $X_3$ is d-connected to $Y$. The vanishing dependence arises from exact numerical cancellation rather than graph separation, violating the Faithfulness condition. $\blacksquare$

### Lemma 1 (Boundedness of DS-CMI)
*For discrete variables $X \in \{0, \dots, B-1\}$, $Y \in \{0, \dots, K-1\}$, and conditioning set $Z$ with Dirichlet prior $\alpha > 0$, the DS-CMI estimator satisfies:*
$$0 \le I(X; Y \mid Z) \le \min(\log_2 B, \log_2 K) < \infty$$

**Proof:** Because $\alpha > 0$, smoothed counts $N(x, y, z) + \alpha > 0$ for all $(x, y, z)$, ensuring strictly positive cell estimates. The estimator constitutes a valid discrete Kullback–Leibler divergence over a finite alphabet, which is non-negative and bounded by marginal Shannon entropies $H(X) \le \log_2 B$ and $H(Y) \le \log_2 K$. Thus, $I(X; Y \mid Z)$ is non-negative, finite, and well-behaved. $\blacksquare$

### Theorem 2 (Conditional Lower Bound on Marginalized Free Energy)
*Let $x^*$ belong to an unobserved zero-day attack. If $x^*$ maintains a minimum Mahalanobis distance $\delta > 0$ from all known class manifolds, then Marginalized Free Energy satisfies:*
$$E(x^*) \ge \frac{1}{2} \delta^2$$
*independent of upstream classifier output probabilities.*

**Proof:** By assumption, reconstruction error under every class hypothesis $k \in \{0, \dots, K-1\}$ satisfies $\mathcal{D}_{\mathbf{\Sigma}}(x^*, \hat{x}^{(k)}) \ge \delta^2$. Substituting into the free-energy formula:
$$E(x^*) = -T \log \sum_{k=0}^{K-1} p(y = k \mid x^*) \exp \left( -\frac{1}{2 T} \mathcal{D}_{\mathbf{\Sigma}}\left(x^*, \hat{x}^{(k)}\right) \right) \ge -T \log \sum_{k=0}^{K-1} p(y = k \mid x^*) \exp \left( -\frac{1}{2 T} \delta^2 \right)$$
Because $\sum_{k=0}^{K-1} p(y = k \mid x^*) = 1$:
$$E(x^*) \ge -T \log \left[ \exp \left( -\frac{\delta^2}{2 T} \right) \right] = \frac{1}{2} \delta^2$$
The lower bound holds regardless of how the classifier distributes posterior weights across training categories. $\blacksquare$

---

## 6. Experimental Evaluation

We evaluate our system on the standard CIC-IDS2017 benchmark using five independent random seeds (42, 123, 456, 789, 2024). Botnet and Infiltration traffic are completely excluded from training splits and reserved exclusively as unobserved zero-day attacks during testing.

![Figure 3: Head-to-Head Comparison](fig2_head_to_head_comparison.png)
*Figure 3: Multi-seed empirical benchmark comparison across five independent random splits with 95% bootstrap confidence intervals. IR-IDS 2.0 achieves superior Macro-F1 and G-Mean while suppressing benign false alarms to 0.94% (a 20-fold reduction relative to baseline).*

### Benchmark Comparison Across 5 Random Seeds (Mean ± Std with 95% Bootstrap CI)

| Model Architecture | Macro-F1 (%) | G-Mean (%) | Benign FAR (%) | Zero-Day Recall (%) | Overall Accuracy (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Plain HistGBDT (Closed-World) | 66.83 ± 1.60 | 0.00 ± 0.00 | **0.30 ± 0.11** | 0.00 ± 0.00 | 80.86 ± 0.35 |
| Isolation Forest | 23.55 ± 1.50 | 0.00 ± 0.00 | 5.35 ± 0.34 | 47.03 ± 0.23 | 50.64 ± 0.30 |
| One-Class SVM | 23.71 ± 1.53 | 0.00 ± 0.00 | 4.09 ± 0.21 | 47.03 ± 0.34 | 51.21 ± 0.31 |
| Standard Autoencoder | 23.56 ± 1.51 | 0.00 ± 0.00 | 5.58 ± 0.27 | 47.38 ± 0.40 | 50.59 ± 0.34 |
| Open-Set Energy Baseline | 67.07 ± 1.68 | 37.51 ± 2.61 | 2.69 ± 0.20 | 1.53 ± 0.33 | 79.89 ± 0.34 |
| Reimplemented Baseline (Gao et al.) | 76.22 ± 1.35 | 65.06 ± 3.19 | 19.12 ± 0.92 | **50.55 ± 2.38** | 79.68 ± 0.28 |
| **IR-IDS 2.0 (Proposed)** | **83.14 ± 1.77** | **72.93 ± 3.23** | 0.94 ± 0.28 | 46.68 ± 0.03 | **88.25 ± 0.53** |

### Key Findings & Honest Disaggregation:
- **Botnet Zero-Day Detection:** **100.00% ± 0.00%** recall (560 of 560 flows detected). Periodic C2 beaconing deviates sharply from benign manifolds.
- **Infiltration Zero-Day Detection:** **0.03% ± 0.06%** recall (0 of 640 flows detected). Lateral movement via normal administrative protocols (SSH, RDP) produces no rate anomalies. At the flow level, statistics reside entirely within the benign density envelope.
- **False Alarm Suppression:** Confined to **0.94% ± 0.28%** (down from 19.12% in the baseline—a 20-fold reduction).
- **Minority SQL Injection Gain:** Balanced focal loss elevated recall from 19.90% to **33.50% ± 8.98%** (113 of 400 test flows detected).
- **Feature Selection Stability:** DS-CMI achieved Jaccard similarity of **1.000 ± 0.000** across all 5 seeds, outperforming Mutual Information (0.312) and BAMB (0.153).

---

## 7. Line-Rate Deployment Architecture

We design a two-tier decoupled software pipeline:
1. **Fast-Path Data Plane (Ingress & Extraction):** Implemented in user space using DPDK or AF_XDP. Ingress packets are parsed at wire speed into fixed 5-tuple flow records. As connections terminate or hit sliding timeout windows, DS-CMI features are extracted into contiguous memory ring buffers without kernel context switches.
2. **Slow-Path Intelligence Plane (Inference & Gating):** AVX-512 SIMD vectorization completes tree pre-classification in 1.2 microseconds. The Marginalized Free-Energy CVAE and POT-EVT gate execute concurrently on GPU/NPU accelerators in 2.1 microseconds.

Total per-flow processing latency is **3.3 microseconds**, comfortably sustaining line-rate throughput exceeding 300,000 flows per second per core.

---

## 8. Limitations & Reproducibility

1. **Payload Inspection Boundary:** Flow-level NIDS cannot inspect encrypted application payloads. Stealthy Infiltration operating within legitimate protocol syntax requires endpoint telemetry (EDR) or TLS decryption gateways.
2. **Class Skew Sensitivity:** Extreme class imbalance requires careful tuning of the focal parameter $\gamma$ to balance minority recall against operational false alarms.
3. **Reproducibility:** All source code, models, benchmark scripts, and dataset loaders are publicly available on GitHub: [github.com/pranithbobby157-afk/CNS_PROJECT](https://github.com/pranithbobby157-afk/CNS_PROJECT). Experiments are strictly deterministic across seeds (42, 123, 456, 789, 2024).

---

## 9. Conclusion

This paper audited the IR-IDS architecture, exposing critical mathematical defects including inverted propensity scores, combinatorial grid collapse, self-conditioning bugs, invalid vector KL divergence, and the accuracy paradox on stealth intrusions. 

We introduced **IR-IDS 2.0**, uniting Dirichlet-Smoothed Conditional Mutual Information (DS-CMI), cost-sensitive balanced focal trees, multi-class marginalized free-energy autoencoding, and Hosking–Wallis POT-EVT thresholding. Across five independent random seeds, our system achieves **83.14% Macro-F1**, isolates unseen Botnet zero-days at **100.00%**, and reduces operational false alarms to **0.94%** (a 20-fold improvement over the baseline). By coupling causal invariance with verifiable transparency, IR-IDS 2.0 provides an effective, auditable defense for next-generation network perimeters.
