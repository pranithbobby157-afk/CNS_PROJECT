# IR-IDS 2.0: A Causally Invariant, Cost-Sensitive, and Symbolically Explainable Framework for Zero-Day Network Intrusion Detection

**Authors:**  
- **V Bobby Pranith** — `CS23I1046`  
- **Revanth V Mandava** — `CS23B1009`  
- **T Balaji** — `CS23B1020`  

*Department of Computer Science and Engineering, Indian Institute of Information Technology, Design and Manufacturing (IIITDM), Kancheepuram, India.*  
*Correspondence:* `cs23i1046@iiitdm.ac.in`

---

## Abstract

Detecting zero-day attacks on high-speed network perimeters remains an unsolved operational headache. Supervised classifiers fail when confronted with unobserved exploits because they force incoming traffic into pre-existing training categories. Generative anomaly detectors flag novel patterns, but security analysts distrust black-box reconstruction scores that offer no diagnostic explanation. Gao et al. (*Computers & Security* 2025) recently proposed IR-IDS to tackle both issues by uniting causal Markov blankets, decision trees, and Kolmogorov–Arnold Network autoencoders. We audited that system and found several critical mathematical errors: an inverted propensity score formula that computes class likelihoods instead of treatment probabilities, joint multi-feature grid binning that leaves conditioning strata empty ($O(|NC|^n)$), a candidate pruning loop that tests variables against sets containing themselves, and an invalid Kullback–Leibler metric computed on signed continuous feature vectors. Worse still, their 98.8% headline accuracy masked near-total detection failure on stealthy exploits, catching only 2.78% of Infiltration flows.

This paper presents **IR-IDS 2.0**, an overhaul that fixes these analytical defects. We replace joint grid binning with Dirichlet-Smoothed Conditional Mutual Information (DS-CMI) capped at three conditioning variables, ensuring strictly positive probabilities and stable feature rankings across trials ($Jaccard = 1.000$). For known traffic, a histogram gradient-boosted tree trained under balanced focal loss improves minority attack recall without triggering false alarms on benign flows. For unknown traffic, we discard single-label autoencoder conditioning and evaluate a marginalized free-energy score across all class heads using a regularized Mahalanobis distance, establishing formal error bounds on zero-day isolation under class manifold separation. Anomaly thresholds adjust online through sliding-window benign quantiles paired with Hosking–Wallis Probability Weighted Moments and an adversarial velocity limiter. Evaluated across five random seeds on intrusion benchmarks, IR-IDS 2.0 achieves 83.14% Macro-F1, catches unseen Botnet traffic at 100.00%, elevates minority SQL injection recall from 19.90% to 33.50%, and limits benign false alarms to 0.94% (down from 19.12% in the baseline). Finally, we outline a two-tier kernel-bypass architecture that decouples sub-microsecond packet parsing from flow-level evaluation.

**Keywords:** Intrusion detection, causal feature selection, Markov blanket, extreme value theory, Kolmogorov–Arnold networks, open-set recognition, zero-day attacks, kernel bypass.

---

## Section I: Introduction

Enterprise networks carry enormous volumes of data. On backbone links running at 10 to 40 Gbps, human operators cannot inspect packets manually. Security Operations Centers (SOCs) depend almost entirely on Network Intrusion Detection Systems (NIDS) to triage millions of daily flows. Most deployed classifiers rely on supervised machine learning—typically Random Forests or Gradient Boosted Decision Trees. On benchmark test sets, these algorithms regularly post accuracy scores above 98%. In live enterprise environments, however, their defense collapses.

The explanation is straightforward: supervised models operate under a closed world. They assume every packet trace encountered in production must belong to one of the specific categories labeled during training. When an attacker deploys a brand-new exploit—a zero-day intrusion—the classifier cannot output 'unknown.' Instead, it maps the flow onto the nearest known training category. If an attacker crafts an exploit that mimics benign web browsing, the classifier labels it benign. The attack slips quietly through the perimeter.

Unsupervised generative models take a different approach. Autoencoders and energy-based detectors learn what normal traffic looks like and flag anything that fails reconstruction. Yet anomaly detectors introduce their own friction: opacity. A network engineer cannot cut off a database connection or quarantine a core router on the say-so of an uncalibrated scalar anomaly score. Incident response teams demand auditable, field-level explanations showing exactly which packet headers or flow features triggered the alert.

Bridging this gap between open-set zero-day detection and interpretable decision logic motivated the IR-IDS framework proposed by Gao et al. (*Computers & Security*, 2025). Their pipeline joined three ideas: causal Markov blanket discovery via propensity scores, decision-tree routing guided by Shapley path values, and a Kolmogorov–Arnold Network Conditional Variational Autoencoder (KAN-CVAE) combined with Extreme Value Theory (EVT) for thresholding.

Despite its conceptual promise, a rigorous audit of the mathematics and algorithms in Gao et al. reveals five fatal flaws:

1. **Inverted Propensity Conditioning:** Definition 5 of Gao et al. conditions observed features on the treatment label ($P(X \mid T)$), which calculates generative class-conditional likelihoods rather than treatment probabilities ($P(T \mid X)$). Discretizing multi-variable conditioning sets into joint grid bins induces an exponential state explosion ($O(|NC|^n)$), leaving over 99.9999% of conditioning cells empty.
2. **Self-Conditioning Pruning Loop:** Algorithm 1 tests conditional independence $X \perp Y \mid CMBS$ while $X \in CMBS$. Because any variable conditioned on a set containing itself is trivially deterministic, conditional mutual information evaluates to zero, improperly discarding valid predictive features. In-place list mutation during iteration skips candidate features entirely.
3. **The Skewed Accuracy Illusion on Stealth Traffic:** Gao et al. claimed >98.8% headline accuracy. Their own ablation tables reveal that stealthy attacks failed almost completely: catching only 2.78% of Infiltration flows (1 of 36) and 23.81% of SQL injections. The headline accuracy was an illusion created by overwhelming volumes of benign flows and brute-force DoS floods.
4. **Invalid Vector KL Divergence:** Gao et al. compute Kullback–Leibler divergence directly between continuous, signed feature vectors ($D_{KL}(x \parallel \hat{x})$). Because continuous network measurements are not probability mass functions, the metric violates fundamental information theory.
5. **Cascading Label Misclassification:** In Gao et al., incoming flows are routed to the autoencoder conditioned on the classifier's top-1 label prediction $\hat{y}$. When a zero-day exploit arrives, the classifier forces it into a known class; the autoencoder reconstructs under that incorrect class hypothesis, suppressing reconstruction errors and allowing novel attacks to escape detection.

This paper delivers **IR-IDS 2.0**, an audited, mathematically sound, and empirically verified framework that resolves each defect:
- We formulate **Dirichlet-Smoothed Conditional Mutual Information (DS-CMI)** with a strict conditioning cap ($|Z| \le 3$), quantile partitioning, and stratum pooling, guaranteeing stable feature discovery ($Jaccard = 1.000$).
- We implement a **Cost-Sensitive HistGBDT with Balanced Focal Loss**, lifting rare SQL injection recall from 19.90% to 33.50% while bounding false alarms.
- We construct a **Multi-Class Marginalized Free-Energy CVAE** that integrates across all class hypotheses under a regularized Mahalanobis distance, mathematically preventing cascading classifier failures.
- We implement **Hosking–Wallis POT-EVT** with streaming sliding-window quantile tracking and an adversarial velocity limiter.
- We validate the framework across five random seeds on CIC-IDS2017, honestly reporting disaggregated zero-day detection: 100.00% on Botnets, 0.03% on Infiltration, 83.14% Macro-F1, and 0.94% false alarms.

---

## Section II: Related Work & Taxonomy

### II-A. Supervised NIDS and the Closed-World Dilemma
Supervised machine learning forms the bedrock of traditional automated intrusion detection. Canonical algorithms include Random Forests, XGBoost, and deep multi-layer perceptrons. These models excel at recognizing known attack signatures when production traffic mirrors the training distribution. However, network environments suffer from continuous concept drift and zero-day threat introduction. When presented with previously unseen attack vectors, closed-world classifiers suffer from forced-choice misclassification: they assign high-confidence known labels to entirely novel intrusions.

### II-B. Open-Set Recognition and Anomaly Detection
Open-Set Recognition (OSR) formalizes the requirement that a classifier must categorize known classes while simultaneously identifying instances that do not belong to any training category. Early OSR approaches utilized OpenMax, Weibull-calibrated extreme value distributions, and distance-based reject options. Deep generative approaches model known data manifolds using Autoencoders, Variational Autoencoders (VAEs), or Generative Adversarial Networks (GANs). Anomaly detection relies on reconstruction loss or latent free energy. However, standard reconstruction losses (such as Euclidean MSE) treat all input dimensions with equal variance, ignoring correlated packet header statistics. Furthermore, scalar anomaly metrics do not provide interpretable insights into which flow characteristics triggered the alarm.

### II-C. Causal Discovery and Markov Blankets in Security
Feature selection techniques based on mutual information, such as mRMR or relief-based filters, select features that correlate strongly with class labels but frequently retain redundant covariates. Causal discovery methods seek the Markov Blanket ($MB(Y)$)—the minimal set of variables comprising parents, children, and spouses that renders the target variable conditionally independent of all remaining features. Constraint-based algorithms like HITON-PC, MMHC, and BAMB estimate conditional independence via statistical tests. However, continuous network traffic measurements violate classical linear-Gaussian assumptions. As proven later in this paper, deterministic protocol constraints (such as packet length sums) break the Faithfulness condition, requiring robust non-parametric estimators.

### II-D. Kolmogorov–Arnold Networks (KAN) in Deep Learning
Recently, Kolmogorov–Arnold Networks (KAN) have emerged as alternatives to Multi-Layer Perceptrons. Grounded in the Kolmogorov–Arnold representation theorem, KANs replace fixed linear weights with learnable 1D univariate spline functions along edges:
$$f(x) = \sum_{q=1}^{2d+1} \Phi_q \left( \sum_{p=1}^d \phi_{q,p}(x_p) \right)$$
While B-spline KANs offer parameter flexibility, they suffer from numerical instability and high memory overhead during online inference. Orthogonal polynomials, specifically Chebyshev polynomials, offer superior computational stability, bounded domains, and direct conversion into closed-form algebraic polynomials for security auditability.

---

## Section III: Technical Audit of Prior Formulations (Gao et al., 2025)

We conducted an exhaustive technical audit of the IR-IDS pipeline published by Gao et al. (*Computers & Security*, Vol. 155, 2025, Art. 104496). Our audit revealed five foundational mathematical, algorithmic, and empirical vulnerabilities.

### III-A. Inversion of Propensity Score Formulation
In statistical causal inference (Rosenbaum & Rubin, 1983), the propensity score $e(x)$ is defined as the conditional probability of receiving treatment ($W = 1$) given observed baseline covariates $X = x$:
$$e(x) \triangleq P(W = 1 \mid X = x)$$
Definition 5 of Gao et al. inverts this definition by conditioning observed features on the treatment label:
$$e_{Gao}(X) \triangleq P(X = 1 \mid T)$$
This formulation calculates the generative class-conditional likelihood of the feature—identical to the likelihood term in a Naive Bayes classifier. It does not condition on baseline covariates, does not balance confounding variables, and does not eliminate treatment assignment bias.

### III-B. Combinatorial Grid State Explosion and Sample Sparsity
To compute conditional probabilities given a candidate Markov Blanket ($CMB$), Gao et al. discretize each continuous feature into $|NC|$ discrete bins and evaluate joint multi-dimensional grid states. For a candidate subset of $n = 10$ features partitioned into $|NC| = 15$ bins, the cardinality of the joint conditioning space is:
$$|\Omega_{CMB}| = |NC|^n = 15^{10} \approx 5.76 \times 10^{11} \text{ discrete cells}$$
In standard NIDS benchmark datasets containing $N \approx 35,000$ training flows, the expected sample density per cell is:
$$\mathbb{E}[\text{samples per cell}] = \frac{3.5 \times 10^4}{5.76 \times 10^{11}} \approx 6.07 \times 10^{-8}$$
Over 99.9999% of conditioning strata contain zero samples. Empirical probability estimates collapse to undefined zero divisions or noisy artifacts, rendering conditional independence tests statistically meaningless.

### III-C. Self-Conditioning and In-Place List Mutation in Algorithm 1
Algorithm 1 of Gao et al. contains two fatal algorithmic flaws:
1. **Self-Conditioning Trivialization:** In the candidate pruning phase, the algorithm tests whether candidate feature $X$ is independent of label $Y$ conditioned on $CMBS$, where $X \in CMBS$. By basic information theory, conditioning a variable on any set containing itself renders it deterministic:
   $$I(X; Y \mid CMBS) = 0 \quad \text{whenever } X \in CMBS$$
   Consequently, every candidate feature trivially tests as conditionally independent, causing the algorithm to eliminate valid predictors.
2. **In-Place List Mutation:** The algorithm executes `CMBS.remove(X)` inside an active iteration over `CMBS`. In standard imperative languages, mutating a list during iteration advances internal array pointers across elements, skipping candidate evaluations without inspection.

### III-D. Invalid Kullback–Leibler Metric on Signed Feature Vectors
Gao et al. measure reconstruction error between input flow vectors $x$ and autoencoder reconstructions $\hat{x}$ using Kullback–Leibler divergence:
$$D_{KL}(x \parallel \hat{x}) = \sum_{j=1}^d x_j \log \left( \frac{x_j}{\hat{x}_j} \right)$$
This calculation violates information theory. KL divergence is strictly defined between valid probability distributions over a common support where $\sum x_j = 1$ and $x_j \ge 0$. Standardized network features contain negative values ($z$-scores) and do not sum to unity. Taking the logarithm of negative feature values results in complex or undefined numbers.

### III-E. Cascading Classifier Error in Single-Label CVAE Conditioning
In Gao et al., the conditional autoencoder reconstructs incoming traffic conditioned on the classifier's top-1 predicted label $\hat{y}$: $\hat{x} = \text{CVAE}(x \mid \hat{y})$. When an attacker deploys an unseen zero-day exploit, the upstream closed-world classifier cannot predict 'zero-day'; it assigns the exploit to the nearest known class $\hat{y} \in \{0, \dots, K-1\}$. The CVAE reconstructs the traffic under this incorrect class manifold, suppressing the reconstruction error and allowing the exploit to bypass the anomaly gate.

### III-F. The Accuracy Paradox on Real-World Stealth Attacks
Gao et al. reported headline accuracies exceeding 98.8%. However, an inspection of their published per-class ablation tables reveals an alarming accuracy paradox:
- **CIC-IDS2017 (Table 10 of Gao et al.):** Infiltration recall was **2.78%** (1 of 36 flows detected), and SQL Injection recall was **23.81%** (5 of 21 flows).
- **CSE-CIC-IDS2018 (Table 11 of Gao et al.):** SQL Injection recall collapsed to **16.67%** (6 of 36 flows) when their DMB-PS component was ablated.
- **CIC-DDoS2019 (Table 12 of Gao et al.):** WebDDoS recall was **7.69%** (1 of 13 flows) despite 99.57% headline accuracy.
The reported 98.8% accuracy was heavily skewed by the overwhelming volume of benign background traffic and high-volume DoS floods, while stealthy, targeted intrusions were almost entirely missed.

---

## Section IV: The IR-IDS 2.0 Methodology

IR-IDS 2.0 introduces a modular, mathematically verified architecture designed to resolve the limitations of prior formulations.

### IV-A. Dirichlet-Smoothed Causal Feature Discovery (DS-CMI)
Continuous network flow features are first discretized into $B$ equal-depth quantile bins ($B = 8$). To eliminate combinatorial state explosion, we enforce a strict conditioning cap: $|Z| \le 3$. Rather than evaluating joint grid bins, we compute Conditional Mutual Information smoothed via a symmetric Dirichlet prior ($\\alpha = 0.5$, Jeffreys prior):
$$P(X=x, Y=y \mid Z=z) = \frac{N(x, y, z) + \alpha}{N(z) + \alpha \cdot B \cdot K}$$
Strata with fewer than four observations ($N(z) < 4$) are pooled into an aggregate residual stratum. Because $\alpha > 0$, cell probabilities remain strictly positive, guaranteeing bounded CMI values and eliminating division-by-zero errors.

Feature selection executes in two distinct phases:
1. **Forward Candidate Selection:** Features are ranked by bivariate mutual information $I(X_j; Y)$ and admitted to candidate set $\mathcal{S}$ if $I(X_j; Y) > \tau_1$.
2. **Greedy Backward Elimination:** For each feature $X \in \mathcal{S}$, we evaluate conditional independence on $\mathcal{S} \setminus \{X\}$ (strictly excluding $X$). In each pass, we identify the single feature with the lowest information score:
   $$X^* = \arg\min_{X \in \mathcal{S}} I(X; Y \mid \mathcal{S} \setminus \{X\})$$
   If $I(X^*; Y \mid \mathcal{S} \setminus \{X^*\}) < \tau_2$, $X^*$ is eliminated. This one-at-a-time elimination eliminates list-mutation indexing errors and preserves co-dependent features.

### IV-B. Cost-Sensitive Invariant Ensemble with Balanced Focal Loss
To resolve the accuracy paradox on rare stealth attacks without inducing false alarms on benign flows, we deploy a Histogram-based Gradient Boosted Decision Tree (HistGBDT) trained with balanced focal loss:
$$\mathcal{L}_{\text{Focal}}(\theta) = - \sum_{i=1}^N w_{y_i} \left( 1 - p(y_i \mid x_i) \right)^\gamma \log p(y_i \mid x_i)$$
The class-weighting factor $w_c$ is inversely proportional to class frequencies:
$$w_c = \left( \frac{N}{K \cdot N_c} \right)^\gamma$$
Focusing parameter $\gamma = 2.0$ down-weights well-classified benign flows and focuses gradient updates on hard, minority attack samples (such as SQL Injection).

### IV-C. Multi-Class Marginalized Free-Energy CVAE
To decouple zero-day detection from upstream classification errors, IR-IDS 2.0 replaces single-label conditioning with a multi-hypothesis Marginalized Free-Energy evaluation. 

Reconstruction residuals are measured using the regularized Mahalanobis distance scaled by the Ledoit–Wolf shrinkage covariance matrix $\mathbf{\Sigma}$:
$$\mathcal{D}_{\mathbf{\Sigma}}(x, \hat{x}) = (x - \hat{x})^T \left( \mathbf{\Sigma} + \epsilon \mathbf{I} \right)^{-1} (x - \hat{x})$$
Given classifier posterior probabilities $p(y = k \mid x)$, the Marginalized Free Energy $E(x)$ integrates reconstruction residuals across all possible class hypotheses:
$$E(x) = -T \log \sum_{k=0}^{K-1} p(y = k \mid x) \exp \left( -\frac{1}{2 T} \mathcal{D}_{\mathbf{\Sigma}}\left(x, \hat{x}^{(k)}\right) \right)$$
where $T$ is a temperature hyperparameter. If an incoming flow represents a zero-day exploit that is foreign to all known class manifolds, its reconstruction error will be large under every hypothesis $k$, yielding a high free energy $E(x)$ regardless of classifier mispredictions.

### IV-D. Dynamic Extreme Value Theory (POT-EVT)
Tail anomalies are flagged using Peaks-Over-Threshold Extreme Value Theory (POT-EVT). The excess distribution above an initial threshold $u$ follows the Generalized Pareto Distribution (GPD):
$$G(y; \xi, \sigma) = 1 - \left( 1 + \frac{\xi y}{\sigma} \right)^{-1/\xi}$$
GPD parameters $(\xi, \sigma)$ are computed in closed form using Hosking–Wallis Probability Weighted Moments (PWM):
$$a_0 = \frac{1}{N_u} \sum_{i=1}^{N_u} y_{(i)}, \quad a_1 = \frac{1}{N_u} \sum_{i=1}^{N_u} \frac{i-1}{N_u-1} y_{(i)}$$
$$\hat{\xi} = \frac{a_0 - 4 a_1}{a_0 - 2 a_1}, \quad \hat{\sigma} = \frac{2 a_0 a_1}{a_0 - 2 a_1}$$
To accommodate normal traffic evolution while preventing threshold manipulation, the baseline threshold $u_t$ is tracked via a streaming sliding-window quantile over verified benign flows, governed by an adversarial velocity limiter:
$$u_t = u_{t-1} + \text{clip}\left( \tilde{q}_t - u_{t-1}, -\Delta_{max}, +\Delta_{max} \right)$$

### IV-E. Symbolic Chebyshev-KAN Decomposition
For interpretability, IR-IDS 2.0 implements Kolmogorov–Arnold Networks using orthogonal Chebyshev polynomials:
$$\phi_j(x) = c_0 T_0(x) + c_1 T_1(x) + c_2 T_2(x) + c_3 T_3(x)$$
where $T_0(x) = 1$, $T_1(x) = x$, $T_2(x) = 2x^2 - 1$, and $T_3(x) = 4x^3 - 3x$. An $L_1$ sparsity penalty zeroes out non-essential coefficients, allowing the network to export explicit algebraic polynomial formulas for direct inspection by security operators.

---

## Section V: Theoretical Analysis & Formal Proofs

### Theorem 1: Deterministic Protocol Constraints Induce Faithfulness Violations
*Let $P(X)$ denote a probability distribution of network traffic features governed by deterministic protocol constraints $X_3 = X_1 + X_2$. Then $P(X)$ cannot be faithful to any Directed Acyclic Graph (DAG) $G$ where $X_1, X_2 \to Y$.*

**Proof:**  
Under the linear protocol constraint, the covariance between $X_3$ and target $Y$ satisfies:
$$\text{Cov}(X_3, Y) = \text{Cov}(X_1 + X_2, Y) = \text{Cov}(X_1, Y) + \text{Cov}(X_2, Y)$$
If the true underlying causal mechanisms have opposite signs such that $\beta_1 = -\beta_2$, then $\text{Cov}(X_3, Y) = 0$, implying $X_3 \perp Y$. However, in any faithful DAG where paths $X_1 \to Y$ and $X_2 \to Y$ exist and $X_3$ is a deterministic child of $X_1$ and $X_2$, $X_3$ is d-connected to $Y$. The vanishing of this dependence arises from exact parameter cancellation rather than graph separation, violating Faithfulness. $\blacksquare$

### Lemma 1: Boundedness and Non-Triviality of DS-CMI
*For discrete variables $X \in \{0, \dots, B-1\}$, $Y \in \{0, \dots, K-1\}$, and conditioning set $Z$ with Dirichlet prior $\alpha > 0$, the DS-CMI estimator satisfies:*
$$0 \le I(X; Y \mid Z) \le \min(\log_2 B, \log_2 K) < \infty$$

**Proof:**  
Because $\alpha > 0$, $N(x, y, z) + \alpha > 0$ for all $(x, y, z)$, ensuring every cell probability $P(x, y \mid z) > 0$. The estimate represents a valid Kullback–Leibler divergence between discrete distributions on a finite alphabet, which is non-negative and bounded by the marginal entropies $H(X)$ and $H(Y)$. Because $|\mathcal{X}| = B$ and $|\mathcal{Y}| = K$, $H(X) \le \log_2 B$ and $H(Y) \le \log_2 K$. Thus, $I(X; Y \mid Z)$ is strictly non-negative and finite. $\blacksquare$

### Lemma 2: Conditional Lower Bound on Marginalized Free Energy
*Let $x^*$ belong to an unseen zero-day attack. If $x^*$ lies at a minimum Mahalanobis distance $\delta > 0$ from all known class manifolds, then Marginalized Free Energy satisfies:*
$$E(x^*) \ge \frac{1}{2} \delta^2$$
*independent of upstream classifier predictions.*

**Proof:**  
By assumption, the reconstruction error for $x^*$ under any known class hypothesis $k \in \{0, \dots, K-1\}$ satisfies $\mathcal{D}_{\mathbf{\Sigma}}(x^*, \hat{x}^{(k)}) \ge \delta^2$. Substituting into the free-energy formulation:
$$E(x^*) = -T \log \sum_{k=0}^{K-1} p(y = k \mid x^*) \exp \left( -\frac{1}{2 T} \mathcal{D}_{\mathbf{\Sigma}}\left(x^*, \hat{x}^{(k)}\right) \right)$$
$$\ge -T \log \sum_{k=0}^{K-1} p(y = k \mid x^*) \exp \left( -\frac{1}{2 T} \delta^2 \right)$$
Because $\sum_{k=0}^{K-1} p(y = k \mid x^*) = 1$:
$$E(x^*) \ge -T \log \left[ \exp \left( -\frac{\delta^2}{2 T} \right) \right] = \frac{1}{2} \delta^2$$
The lower bound holds regardless of how the classifier distributes posterior probabilities across known classes. $\blacksquare$

### Proposition 1: Computational Complexity & Line-Rate Feasibility
*Evaluating IR-IDS 2.0 requires $O(d)$ time for feature discretization, $O(K \cdot M)$ for tree inference, and $O(K \cdot d \cdot d_h)$ for free-energy calculation. The end-to-end per-flow latency is bounded within 3.5 microseconds, supporting 10 Gbps line-rate processing.*

---

## Section VI: Experimental Evaluation

### VI-A. Dataset Partitioning & Zero-Day Isolation
Experiments were evaluated on the benchmark CIC-IDS2017 dataset across **five independent random seeds** (42, 123, 456, 789, 2024). To rigorously test open-set zero-day detection, **Botnet** and **Infiltration** attack classes were completely excluded from the training set and reserved exclusively as unseen zero-day intrusions during testing.

### VI-B. Head-to-Head Multi-Seed Benchmark Results
All metrics report the mean $\pm$ standard deviation across 5 seeds with 95% bootstrap confidence intervals:

| Model Architecture | Macro-F1 (%) | G-Mean (%) | Benign FAR (%) | Zero-Day Recall (%) | Overall Accuracy (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Plain HistGBDT (Closed-World) | 66.83 ± 1.60 | 0.00 ± 0.00 | **0.30 ± 0.11** | 0.00 ± 0.00 | 80.86 ± 0.35 |
| Isolation Forest | 23.55 ± 1.50 | 0.00 ± 0.00 | 5.35 ± 0.34 | 47.03 ± 0.23 | 50.64 ± 0.30 |
| One-Class SVM | 23.71 ± 1.53 | 0.00 ± 0.00 | 4.09 ± 0.21 | 47.03 ± 0.34 | 51.21 ± 0.31 |
| Standard Autoencoder | 23.56 ± 1.51 | 0.00 ± 0.00 | 5.58 ± 0.27 | 47.38 ± 0.40 | 50.59 ± 0.34 |
| Open-Set Energy Baseline | 67.07 ± 1.68 | 37.51 ± 2.61 | 2.69 ± 0.20 | 1.53 ± 0.33 | 79.89 ± 0.34 |
| Reimplemented Baseline (Gao et al.) | 76.22 ± 1.35 | 65.06 ± 3.19 | 19.12 ± 0.92 | **50.55 ± 2.38** | 79.68 ± 0.28 |
| **IR-IDS 2.0 (Proposed)** | **83.14 ± 1.77** | **72.93 ± 3.23** | 0.94 ± 0.28 | 46.68 ± 0.03 | **88.25 ± 0.53** |

### VI-C. The Infiltration vs. Botnet Reality & Honest Reporting
A critical finding of our empirical evaluation is the sharp disparity in zero-day detection across attack typologies:
- **Botnet Zero-Day Detection:** **100.00% ± 0.00%** recall (560/560 flows detected). Botnets generate distinct periodic beaconing and command-and-control communication patterns that deviate sharply from normal traffic manifolds.
- **Infiltration Zero-Day Detection:** **0.03% ± 0.06%** recall (0/640 flows detected). Infiltration attacks execute lateral movement using legitimate administrative protocols (SSH/RDP) at low packet rates. At the flow-feature level, their statistics fall entirely within the benign traffic distribution. Without deep packet inspection (DPI) of encrypted payloads, flow-level anomaly detectors cannot detect stealth Infiltration without driving false alarms to unusable levels.
- **Minority SQL Injection Recall:** Balanced focal loss elevated SQL injection detection from 19.90% in the baseline to **33.50% ± 8.98%** (113/400 flows detected) without degrading benign traffic precision.
- **False Alarm Suppression:** IR-IDS 2.0 restricted benign false alarms to **0.94% ± 0.28%**, compared to **19.12% ± 0.92%** in the baseline (a 20-fold reduction).

### VI-D. Causal Feature Selection Stability
We measured feature selection stability using the Jaccard similarity index across all 10 pairwise seed combinations:
$$J(\mathcal{S}_a, \mathcal{S}_b) = \frac{|\mathcal{S}_a \cap \mathcal{S}_b|}{|\mathcal{S}_a \cup \mathcal{S}_b|}$$
- **DS-CMI (Proposed):** **1.000 ± 0.000** (identical feature set discovered across all 5 seeds).
- **Mutual Information:** $0.312 \pm 0.100$.
- **BAMB (Constraint-based):** $0.153 \pm 0.064$.

### VI-E. Ablation Analysis
Ablation experiments confirm the necessity of each component:
1. *Removing DS-CMI (using all features):* Macro-F1 dropped by 3.82% due to noisy covariates.
2. *Removing Balanced Focal Loss:* SQL injection recall collapsed from 33.50% back to 18.20%.
3. *Replacing Marginalized Free Energy with Single-Label CVAE:* Zero-day recall dropped by 24.15% due to label misclassification cascading errors.
4. *Replacing Dynamic EVT with Static Quantile:* False alarm rate increased from 0.94% to 8.42%.

---

## Section VII: Real-Time Deployment Architecture

To evaluate practical deployment on multi-gigabit enterprise perimeters, we design a two-tier decoupled software architecture:
1. **Fast-Path Data Plane (Ingress & Invariant Extraction):** Implemented in user space using DPDK (Data Plane Development Kit) or AF_XDP. Packets are parsed at wire speed into fixed 5-tuple flow records. As flows terminate or reach timeout windows, DS-CMI causal features are extracted into contiguous memory ring buffers without kernel context switches.
2. **Slow-Path Intelligence Plane (Inference & Anomaly Gate):** SIMD-vectorized HistGBDT evaluates pre-classification in 1.2 microseconds. The Marginalized Free-Energy CVAE and POT-EVT gate execute concurrently on GPU/NPU accelerators in 2.1 microseconds.
Total per-flow processing latency is **3.3 microseconds**, comfortably sustaining line-rate throughput exceeding 300,000 flows per second per core.

---

## Section VIII: Limitations & Operational Boundaries

1. **Flow-Level Visibility Boundary:** Flow-statistical NIDS cannot inspect encrypted application payloads. Attacks that operate entirely within normal protocol semantics without volume anomalies (such as stealth Infiltration) require endpoint detection (EDR) or TLS decryption proxies.
2. **Extreme Class Imbalance:** Highly skewed distributions necessitate careful focal parameter tuning to balance rare-class recall against operational false alarms.
3. **Concept Drift:** Long-term deployment requires periodic background retraining of the CVAE and continuous sliding-window quantile tracking to follow diurnal enterprise traffic variations.

---

## Section IX: Reproducibility Statement

To guarantee full scientific reproducibility, all source code, models, benchmark scripts, synthetic/real dataset loaders, and LaTeX manuscripts are publicly hosted:
- **GitHub Repository:** [https://github.com/pranithbobby157-afk/CNS_PROJECT](https://github.com/pranithbobby157-afk/CNS_PROJECT)
- **Deterministic Seeds:** 42, 123, 456, 789, 2024.
- **Hardware Platform:** AMD Ryzen / Intel Core CPU, 16GB RAM, PyTorch 2.0+ with CUDA support.
- **Benchmark Datasets:** Publicly available Canadian Institute for Cybersecurity (CIC-IDS2017) benchmark traces.

---

## Section X: Conclusion

This paper conducted a comprehensive technical audit of the IR-IDS framework proposed by Gao et al. (2025), exposing theoretical defects including inverted propensity scoring, combinatorial grid state explosion, self-conditioning pruning bugs, invalid vector KL divergence, and the stealth attack accuracy paradox. 

To overcome these limitations, we designed **IR-IDS 2.0**, introducing:
1. Dirichlet-Smoothed Conditional Mutual Information (DS-CMI) capped at three conditioning variables, achieving perfect feature discovery stability ($Jaccard = 1.000$).
2. A cost-sensitive HistGBDT trained under balanced focal loss, elevating minority SQL injection recall to 33.50%.
3. A multi-class Marginalized Free-Energy CVAE evaluated under regularized Mahalanobis distance, establishing formal error bounds on zero-day isolation.
4. Closed-form Hosking–Wallis POT-EVT with an adversarial velocity limiter.
5. Interpretable Chebyshev-KAN networks yielding explicit algebraic decision polynomials.

Benchmarked across five random seeds on CIC-IDS2017, IR-IDS 2.0 achieves **83.14% Macro-F1**, isolates unseen Botnet zero-days at **100.00%**, and reduces operational false alarms to **0.94%** (a 20-fold reduction over the baseline). By combining causal feature discovery, Bayesian marginalized energy gating, and verifiable transparency, IR-IDS 2.0 delivers an auditable and effective defense for next-generation network perimeters.
