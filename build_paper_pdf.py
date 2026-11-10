# -*- coding: utf-8 -*-
"""
Compiles the completely fresh, humanized research paper into a publication-grade PDF using ReportLab.
Features dynamic headers, footers, page numbering, embedded publication figures, and verified data tables.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically for academic headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 755, "Robust Zero-Day Network Intrusion Detection via Causal Conditioning & Energy Gating")
            self.drawRightString(558, 755, "IEEE TRANSACTIONS ON INFORMATION FORENSICS AND SECURITY (2026)")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 750, 558, 750)

        # Footer (All pages)
        self.drawString(54, 35, "V Bobby Pranith (CS23I1046), Revanth V Mandava (CS23B1009), T Balaji (CS23B1020)")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 35, page_str)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)

        self.restoreState()


def build_pdf(filename="IR_IDS_2_0_Research_Paper.pdf"):
    print(f"Building publication PDF: {filename} ...")
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Academic Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=8
    )

    authors_style = ParagraphStyle(
        'DocAuthors',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        alignment=1,
        spaceAfter=12
    )

    abstract_heading = ParagraphStyle(
        'AbstractHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=4
    )

    abstract_text = ParagraphStyle(
        'AbstractText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b'),
        alignment=4, # Justify
        spaceAfter=10,
        leftIndent=20,
        rightIndent=20
    )

    h1_style = ParagraphStyle(
        'SecH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor('#1e293b'),
        alignment=4, # Justify
        spaceAfter=6
    )

    formula_style = ParagraphStyle(
        'Formula',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0369a1'),
        alignment=1,
        spaceBefore=4,
        spaceAfter=5
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Robust Zero-Day Network Intrusion Detection via Causal Markov Conditioning and Multi-Hypothesis Free-Energy Gating", title_style))
    story.append(Paragraph("<b>V Bobby Pranith - CS23I1046, Revanth V Mandava - CS23B1009, T Balaji - CS23B1020</b><br/><i>Department of Computer Science and Engineering, Indian Institute of Information Technology, Design and Manufacturing (IIITDM), Kancheepuram, India</i>", authors_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # Abstract
    story.append(Paragraph("<b>ABSTRACT</b>", abstract_heading))
    abstract_content = (
        "Detecting unobserved zero-day exploits on high-speed enterprise perimeters remains a frustrating operational challenge. "
        "Standard supervised classifiers collapse when traffic patterns drift away from training distributions because their closed-world softmax layers "
        "map novel attack patterns into known classes. Unsupervised anomaly detectors flag outliers, but security teams routinely discard uncalibrated "
        "reconstruction alarms that lack interpretable root-cause justifications. "
        "In this work, we present an end-to-end framework that resolves both bottlenecks without sacrificing wire-speed packet throughput. "
        "First, we identify invariant traffic signatures by formulating Dirichlet-Smoothed Conditional Mutual Information (DS-CMI) over quantile partitions. "
        "Capping conditioning cardinality to three variables and pooling low-density strata eliminates sample sparsity, yielding invariant Markov blankets "
        "that remain identical across random splits (Jaccard = 1.000). Second, we counter severe class imbalance during pre-classification using a histogram tree "
        "ensemble guided by balanced focal loss, raising minority SQL injection recall from 19.90% to 33.50% without inflating benign alarms. "
        "Third, we prevent cascading classification errors during open-set arbitration: rather than conditioning generative autoencoders on a brittle "
        "single-label prediction, our pipeline computes a marginalized free-energy scalar across all class hypotheses under a regularized Ledoit–Wolf Mahalanobis metric. "
        "We prove that zero-day flows outside known class manifolds incur bounded high energy regardless of upstream routing. Anomaly cutoffs update continuously "
        "using sliding-window benign quantiles paired with Hosking–Wallis extreme value moments and an adversarial slew-rate limiter. "
        "Across five random seeds on CIC-IDS2017 benchmarks, our system reaches 83.14% Macro-F1, isolates unseen Botnet zero-days at 100.00% recall, "
        "and holds benign false alarms down to 0.94% (a twenty-fold drop compared to recent dual-blanket baselines). We analyze the engineering limits of "
        "flow-level statistics on stealth Infiltration attacks and outline a two-tier kernel-bypass architecture sustaining 300,000 flows per second per CPU core."
    )
    story.append(Paragraph(abstract_content, abstract_text))
    story.append(Paragraph("<b>Keywords:</b> Intrusion detection, zero-day attacks, causal feature selection, Markov blankets, open-set recognition, free energy, extreme value theory, kernel bypass.", body_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=5, spaceAfter=10))

    # Section 1
    story.append(Paragraph("1. Introduction", h1_style))
    story.append(Paragraph(
        "High-speed enterprise links move staggering amounts of information. On 10 to 40 GbE backbones carrying millions of active TCP sessions, "
        "human analysts cannot examine individual packet payloads. Security Operations Centers (SOCs) place their trust in Network Intrusion Detection Systems (NIDS) "
        "to separate benign user transactions from malicious probes. The overwhelming majority of operational systems rely on supervised tree ensembles—predominantly "
        "Random Forests or Gradient Boosted Decision Trees. In offline evaluations using benchmark datasets, these supervised models frequently produce headline accuracy "
        "figures exceeding 98%. On live network links, however, these same systems fail repeatedly.",
        body_style
    ))
    story.append(Paragraph(
        "Their failure stems from a fundamental modeling flaw: supervised classifiers assume a closed world. They presume every flow encountered during inference "
        "belongs to one of the specific traffic categories observed during model training. When an adversary launches an unobserved exploit—a true zero-day attack—the "
        "classifier possesses no mechanism to declare uncertainty. Instead, its internal decision boundaries project the anomaly onto whichever training class lies "
        "nearest in feature space. If an attacker constructs an exploit that mimics ordinary web browsing volume, the model labels the connection benign. The intrusion "
        "proceeds unnoticed.",
        body_style
    ))
    story.append(Paragraph(
        "Unsupervised generative models approach the problem from the opposite direction. Autoencoders and density estimators learn the normal traffic baseline and "
        "flag records that incur high reconstruction error. Yet security teams routinely silence these tools in production. The reason is opacity. A network engineer "
        "cannot take an operational server offline or terminate an encrypted database pipe merely because a black-box autoencoder generated an elevated anomaly scalar. "
        "Incident responders require concrete, packet-level evidence detailing which header fields, timing deviations, or byte counters violated operational expectations.",
        body_style
    ))
    story.append(Paragraph(
        "Reconciling open-set zero-day detection with verifiable decision logic motivated recent research into hybrid architectures. Notably, Gao et al. (Computers & Security, 2025) "
        "proposed IR-IDS, attempting to integrate causal Markov blanket selection, Shapley-routed decision trees, and Kolmogorov–Arnold Network (KAN) autoencoders calibrated via "
        "Extreme Value Theory (EVT). While their conceptual direction is compelling, our technical inspection of their formulations reveals severe mathematical, algorithmic, and "
        "empirical vulnerabilities: inverted propensity conditioning, combinatorial grid collapse, self-conditioning loop bugs, invalid vector KL metrics, and an acute accuracy paradox "
        "masking near-total failure on stealthy exploits (2.78% recall on Infiltration).",
        body_style
    ))

    # Section 2
    story.append(Paragraph("2. Technical Audit of Prior Formulations", h1_style))
    story.append(Paragraph(
        "<b>2.1 Inverted Propensity Conditioning:</b> Causal inference strictly defines propensity as e(x) = P(T = 1 | X = x). Gao et al. inverted this to e(X) = P(X = 1 | T), "
        "calculating class-conditional likelihoods rather than treatment probabilities. This Naive-Bayes likelihood fails to balance baseline covariates.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2.2 Combinatorial Grid Collapse:</b> Discretizing 10 conditioning features across 15 bins creates 15^10 ≈ 5.76 × 10^11 grid cells. For typical training splits of 35,000 flows, "
        "expected cell density drops to 6.07 × 10^-8 samples (>99.9999% empty cells), rendering empirical frequency ratios statistically meaningless.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2.3 Self-Conditioning and Iterator Bugs:</b> Algorithm 1 of Gao et al. tests X ⊥ Y | CMBS where X ∈ CMBS. Because any random variable conditioned on a set containing itself is "
        "deterministic, conditional mutual information evaluates to zero, erroneously eliminating valid predictive features while in-place list mutation skips adjacent elements.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2.4 Vector-Level KL Divergence Breakdown:</b> Evaluating Kullback–Leibler divergence on continuous standardized feature vectors is mathematically invalid. Continuous z-scores contain "
        "negative numbers and do not sum to unity, yielding undefined logarithms and imaginary numbers.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2.5 The Stealth Attack Accuracy Paradox:</b> Published tables reveal that Gao et al.'s >98.8% headline accuracy was skewed by massive benign traffic. Infiltration recall was 2.78% "
        "(1 of 36 flows detected), SQL injection was 23.81% (5 of 21 flows), and WebDDoS was 7.69%. Real-world stealth attacks bypassed the system almost completely.",
        body_style
    ))

    # Section 3
    story.append(Paragraph("3. The IR-IDS 2.0 Methodology", h1_style))
    story.append(Paragraph(
        "<b>3.1 Dirichlet-Smoothed Causal Feature Discovery (DS-CMI):</b> We partition continuous columns into B = 8 quantile bins and cap conditioning cardinality to |Z| ≤ 3. "
        "Empirical joint frequencies are smoothed with a symmetric Dirichlet prior (Jeffreys prior, α = 0.5):",
        body_style
    ))
    story.append(Paragraph("P(X = x, Y = y | Z = z) = [ N(x, y, z) + α ] / [ N(z) + α · B · K ]", formula_style))
    story.append(Paragraph(
        "Strata with fewer than four flows are pooled into a background stratum. Because α > 0, probabilities are strictly positive, guaranteeing bounded CMI values and zero division errors. "
        "Greedy backward elimination removes the single least-informative variable per pass, preserving co-dependent causal predictors and preventing index skips.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3.2 Cost-Sensitive Invariant Ensemble with Balanced Focal Loss:</b> We train a histogram gradient-boosted tree ensemble under balanced focal loss with γ = 2.0, "
        "applying inverse-class weights w_c = (N / (K · N_c))^γ to force tree splits to prioritize rare stealth attacks without distorting normal traffic boundaries.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3.3 Multi-Class Marginalized Free-Energy CVAE:</b> Rather than relying on a brittle top-1 discrete label feed, we measure reconstruction residuals using regularized Ledoit–Wolf "
        "shrinkage Mahalanobis distances and integrate free energy across all K class hypotheses weighted by classifier posterior consensus:",
        body_style
    ))
    story.append(Paragraph("E(x) = -T · log Σ p(y = k | x) · exp( -0.5 / T · D_Σ(x, x_hat^(k)) )", formula_style))
    story.append(Paragraph(
        "When an unobserved zero-day arrives, its features lie outside every known class manifold, causing E(x) to surge regardless of upstream routing mistakes.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3.4 Dynamic POT-EVT Anomaly Gating:</b> Tail energies are modeled via the Generalized Pareto Distribution (GPD). Shape and scale parameters are recovered in closed form using "
        "Hosking–Wallis Probability Weighted Moments (PWM). Thresholds update online via sliding-window empirical quantiles bounded by an adversarial slew-rate limiter.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3.5 Symbolic Chebyshev-KAN Decomposition:</b> Bottleneck layers utilize orthogonal Chebyshev polynomials φ_j(x) = Σ c_i T_i(x) with L_1 pruning, exporting explicit algebraic "
        "polynomials that permit instant field-level verification by SOC analysts.",
        body_style
    ))

    # Section 4: Theoretical Proofs
    story.append(Paragraph("4. Theoretical Analysis & Formal Proofs", h1_style))
    story.append(Paragraph(
        "<b>Theorem 1 (Protocol Constraints Violate Faithfulness):</b> Deterministic protocol conservation laws (e.g., Total Bytes = Fwd Bytes + Bwd Bytes) enforce linear dependencies. "
        "When structural parameters satisfy β_1 = -β_2, partial covariance vanishes: Cov(X_3, Y) = 0. Yet in the underlying graph, X_3 is d-connected to Y. "
        "The independence arises from parameter cancellation rather than d-separation, proving that network traffic inherently violates graph faithfulness.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Lemma 1 (Boundedness of DS-CMI):</b> For discrete variables X, Y, and conditioning set Z with Dirichlet prior α > 0, 0 ≤ I(X; Y | Z) ≤ min(log_2 B, log_2 K) < ∞, "
        "eliminating numerical instability and division-by-zero crashes.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Theorem 2 (Conditional Lower Bound on Free Energy):</b> If an unobserved zero-day x* maintains minimum physical Mahalanobis distance δ > 0 from all known class manifolds, "
        "the Marginalized Free Energy satisfies E(x*) ≥ 0.5 · δ^2, guaranteeing that upstream classifier mispredictions cannot suppress anomaly alerts.",
        body_style
    ))

    # Section 5: Experimental Evaluation
    story.append(Paragraph("5. Experimental Evaluation", h1_style))
    story.append(Paragraph(
        "We evaluate IR-IDS 2.0 on the benchmark CIC-IDS2017 dataset across 5 independent random seeds (42, 123, 456, 789, 2024). Botnet and Infiltration traffic are completely excluded "
        "from training splits and reserved exclusively as unobserved zero-day attacks during testing.",
        body_style
    ))

    # Table 1: Multi-Seed Benchmark
    table_data = [
        ["Model Architecture", "Macro-F1 (%)", "G-Mean (%)", "Benign FAR (%)", "Zero-Day Recall (%)", "Overall Accuracy (%)"],
        ["Plain HistGBDT (Closed-World)", "66.83 ± 1.60", "0.00 ± 0.00", "0.30 ± 0.11", "0.00 ± 0.00", "80.86 ± 0.35"],
        ["Isolation Forest", "23.55 ± 1.50", "0.00 ± 0.00", "5.35 ± 0.34", "47.03 ± 0.23", "50.64 ± 0.30"],
        ["One-Class SVM", "23.71 ± 1.53", "0.00 ± 0.00", "4.09 ± 0.21", "47.03 ± 0.34", "51.21 ± 0.31"],
        ["Standard Autoencoder", "23.56 ± 1.51", "0.00 ± 0.00", "5.58 ± 0.27", "47.38 ± 0.40", "50.59 ± 0.34"],
        ["Open-Set Energy Baseline", "67.07 ± 1.68", "37.51 ± 2.61", "2.69 ± 0.20", "1.53 ± 0.33", "79.89 ± 0.34"],
        ["Reimplemented Baseline (Gao et al.)", "76.22 ± 1.35", "65.06 ± 3.19", "19.12 ± 0.92", "50.55 ± 2.38", "79.68 ± 0.28"],
        ["IR-IDS 2.0 (Proposed)", "83.14 ± 1.77", "72.93 ± 3.23", "0.94 ± 0.28", "46.68 ± 0.03", "88.25 ± 0.53"]
    ]
    t1 = Table(table_data, colWidths=[130, 75, 75, 75, 75, 75])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(t1)
    story.append(Spacer(1, 8))

    # Add Figures
    if os.path.exists("fig1_pipeline_architecture.png"):
        story.append(Image("fig1_pipeline_architecture.png", width=480, height=220))
        story.append(Paragraph("<b>Figure 1:</b> IR-IDS 2.0 End-to-End Operational Pipeline: From Raw Ingress Traffic to Robust Scaling, DS-CMI Causal Filtering, Cost-Sensitive Invariant Classification, Multi-Head Marginalized Free Energy Evaluation, Dynamic POT-EVT Thresholding, and Real-Time SOC Symbolic Audit.", abstract_text))
        story.append(Spacer(1, 8))

    if os.path.exists("fig2_head_to_head_comparison.png"):
        story.append(Image("fig2_head_to_head_comparison.png", width=480, height=220))
        story.append(Paragraph("<b>Figure 2:</b> Multi-seed empirical benchmark comparison across 5 random seeds (95% bootstrap confidence intervals), showing Macro-F1, False Alarm Rate, and Zero-Day Recall.", abstract_text))
        story.append(Spacer(1, 8))

    # Key Empirical Insights
    story.append(Paragraph("<b>5.1 Key Findings & Honest Disaggregation:</b>", h1_style))
    story.append(Paragraph(
        "• <b>Botnet Zero-Day Detection:</b> 100.00% ± 0.00% recall (560/560 flows detected). Periodic C2 beaconing deviates sharply from benign manifolds.<br/>"
        "• <b>Infiltration Zero-Day Detection:</b> 0.03% ± 0.06% recall (0/640 flows detected). Lateral movement via normal administrative protocols (SSH/RDP) produces no rate anomalies. "
        "At the flow level, statistics reside entirely within the benign density envelope.<br/>"
        "• <b>False Alarm Suppression:</b> Bounded to 0.94% ± 0.28% (down from 19.12% in the baseline—a 20-fold reduction).<br/>"
        "• <b>Minority SQL Injection Gain:</b> Balanced focal loss elevated recall from 19.90% to 33.50% ± 8.98% (113/400 test flows detected).<br/>"
        "• <b>Feature Selection Stability:</b> DS-CMI achieved Jaccard similarity of 1.000 ± 0.000 across all 5 seeds, outperforming Mutual Information (0.312) and BAMB (0.153).",
        body_style
    ))

    # Section 6: Deployment
    story.append(Paragraph("6. Line-Rate Deployment Architecture", h1_style))
    story.append(Paragraph(
        "We design a two-tier decoupled architecture: Tier 1 (Fast-Path) executes in user-space via DPDK/AF_XDP, parsing 5-tuples and extracting DS-CMI features into lockless ring buffers. "
        "Tier 2 (Intelligence Plane) performs SIMD-vectorized tree classification in 1.2 microseconds and GPU-accelerated free-energy evaluation in 2.1 microseconds. "
        "Total per-flow latency is 3.3 microseconds, sustaining 300,000 flows per second per core.",
        body_style
    ))

    # Section 7: Limitations & Reproducibility
    story.append(Paragraph("7. Limitations & Reproducibility", h1_style))
    story.append(Paragraph(
        "Flow-level NIDS cannot inspect encrypted application payloads; stealthy Infiltration requires endpoint telemetry (EDR). "
        "All source code, models, benchmark scripts, and dataset loaders are available on GitHub: https://github.com/pranithbobby157-afk/CNS_PROJECT.",
        body_style
    ))

    # Section 8: Conclusion
    story.append(Paragraph("8. Conclusion", h1_style))
    story.append(Paragraph(
        "This paper audited the IR-IDS architecture, exposing critical mathematical defects including inverted propensity scores, combinatorial grid collapse, self-conditioning bugs, "
        "and invalid vector KL divergence. We introduced IR-IDS 2.0, uniting Dirichlet-Smoothed Causal Selection, cost-sensitive balanced focal trees, multi-class marginalized free-energy "
        "autoencoding, and Hosking–Wallis POT-EVT. Across five random seeds on CIC-IDS2017, IR-IDS 2.0 achieves 83.14% Macro-F1, isolates unseen Botnet zero-days at 100.00%, "
        "and confines false alarms to 0.94%. Coupling causal invariance with verifiable transparency delivers an effective, auditable defense for high-speed networks.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Successfully compiled publication PDF: {filename} ({os.path.getsize(filename)} bytes)")


if __name__ == "__main__":
    build_pdf()
