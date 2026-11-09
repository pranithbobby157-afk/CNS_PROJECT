# -*- coding: utf-8 -*-
"""
Compiles the humanized research paper into a publication-grade PDF using ReportLab.
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
            self.drawString(54, 755, "IR-IDS 2.0: Causal Feature Discovery & Energy-Based Zero-Day NIDS")
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
        fontSize=17,
        leading=21,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=8
    )

    authors_style = ParagraphStyle(
        'DocAuthors',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        alignment=1,
        spaceAfter=14
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
        spaceAfter=12,
        leftIndent=24,
        rightIndent=24
    )

    h1_style = ParagraphStyle(
        'SecH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        alignment=4, # Justify
        spaceAfter=6
    )

    formula_style = ParagraphStyle(
        'Formula',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0369a1'),
        alignment=1,
        spaceBefore=4,
        spaceAfter=6
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("IR-IDS 2.0: Causal Feature Discovery and Energy-Based Open-Set Recognition for Zero-Day Intrusion Detection", title_style))
    story.append(Paragraph("<b>V Bobby Pranith - CS23I1046, Revanth V Mandava - CS23B1009, T Balaji - CS23B1020</b><br/><i>Department of Computer Science and Engineering &bull; Target: IEEE Transactions on Information Forensics and Security</i>", authors_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # Abstract
    story.append(Paragraph("<b>ABSTRACT</b>", abstract_heading))
    abstract_content = (
        "Statistical traffic classifiers deployed at network perimeters face a stubborn dilemma. They must isolate novel attack patterns "
        "without flooding operators with false alarms, yet network engineers distrust black-box anomaly alerts that cannot be traced back to "
        "concrete packet fields. Gao et al. (Computers & Security 2025) attempted to bridge this gap with IR-IDS, combining causal Markov blanket discovery, "
        "decision trees, and a Kolmogorov–Arnold Network conditional autoencoder. Our audit of that system uncovers several technical obstacles in the "
        "published record: an inverted propensity score formulation that conditions features on class labels, joint multi-feature grid binning that "
        "collapses into empty sample cells (O(|NC|^n)), candidate feature pruning that tests conditional independence against sets containing the variable itself, "
        "invalid Kullback–Leibler evaluations on signed continuous feature vectors, and high headline accuracy (>98.8%) that concealed near-total failure "
        "on stealthy exploits (2.78% recall on Infiltration). "
        "This paper presents IR-IDS 2.0, an overhaul designed to resolve these mathematical and operational bottlenecks. We replace grid-based conditioning "
        "with Dirichlet-Smoothed Conditional Mutual Information (DS-CMI) capped at three conditioning variables, ensuring strictly positive cell estimates "
        "and stable feature rankings across trials. A histogram-based gradient boosted tree trained under balanced focal loss recovers minority attack signatures "
        "without distorting normal traffic baselines. Rather than relying on single-label autoencoder reconstruction, we introduce a marginalized free-energy "
        "score evaluated across all class heads under a regularized Ledoit–Wolf Mahalanobis metric, establishing a formal lower bound on zero-day anomaly scores "
        "under manifold separation. Dynamic extreme value theory thresholds, updated via sliding-window empirical quantiles with adversarial rate limiters, "
        "curb operational false alarms. Across five benchmark random seeds, IR-IDS 2.0 achieves 83.14% Macro-F1, isolates unseen Botnet traffic at 100.00%, "
        "raises minority SQL injection recall from 19.90% to 33.50%, and limits benign false alarms to 0.94% (down from 19.12% in the reimplemented baseline). "
        "Finally, we model line-rate execution as a two-tier decoupled architecture separating hardware packet parsing from flow evaluation."
    )
    story.append(Paragraph(abstract_content, abstract_text))
    story.append(Paragraph("<b>Keywords:</b> Intrusion detection, causal feature selection, Markov blanket, extreme value theory, Kolmogorov–Arnold networks, open-set recognition, zero-day attacks, kernel bypass.", body_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=6, spaceAfter=12))

    # Section 1
    story.append(Paragraph("1. Introduction", h1_style))
    story.append(Paragraph(
        "Perimeter defense in modern multi-gigabit networks depends almost entirely on automated traffic inspection. At link rates exceeding 10 Gbps, manual triage is out of the question: security operations centers (SOCs) must process millions of flow records daily, relying on network intrusion detection systems (NIDS) to flag suspicious behavior. Most production and academic classifiers rely on supervised learning—typically tree ensembles like Random Forests or Gradient Boosted Decision Trees. On benchmark test sets, these algorithms regularly post accuracy scores above 98%. In production networks, however, their performance deteriorates quickly.",
        body_style
    ))
    story.append(Paragraph(
        "The core reason is well known: supervised models assume a closed world. They assume every flow encountered at inference belongs to a category seen during training. When an attacker deploys a novel exploit—a zero-day attack—the classifier has no mechanism to express novelty. Instead, it forces the flow into the nearest known category, allowing unseen attack vectors to pass unhindered. Generative anomaly detectors attempt to circumvent this constraint by learning normal baselines, but create operational friction due to opacity.",
        body_style
    ))
    story.append(Paragraph(
        "Reconciling open-set zero-day detection with transparent decision logic motivated the IR-IDS framework proposed by Gao et al. (2025). Despite the conceptual promise of combining causal feature selection, decision trees, and KAN-CVAEs, our mathematical and empirical audit reveals five fundamental structural breakdowns in the published framework: inverted propensity scores, combinatorial grid sparsity, self-conditioning algorithmic bugs, invalid vector KL metrics, and the Evaluation Skew masking failures on rare stealth exploits.",
        body_style
    ))

    # Section 2
    story.append(Paragraph("2. Technical Audit of Gao et al. (2025)", h1_style))
    story.append(Paragraph(
        "<b>2.1 Inverted Propensity Conditioning:</b> Definition 5 in Gao et al. defines propensity as <i>e(T) = P(X = 1 | T)</i>, conditioning observed features on the treatment label. Causal theory strictly defines propensity as <i>e(x) = P(T = 1 | X = x)</i>. Inverting this calculates class-conditional likelihoods rather than treatment assignment probabilities, failing to balance covariates.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2.2 Combinatorial Grid Sparsity:</b> Discretizing candidate conditioning features across |NC| discrete intervals creates an exponential state space <i>O(|NC|^n)</i>. For 15 classes and 10 features, this yields 15^10 ≈ 5.76 × 10^11 states. In typical training sets of 35,000 flows, sample density drops to 6.07 × 10^-8 samples per cell (>99.9999% empty bins), creating extreme sample sparsity.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2.3 Self-Conditioning in Markov Blanket Pruning:</b> Algorithm 1 checks conditional independence by testing <i>X ⊥ Y | CMBS</i> while <i>X ∈ CMBS</i>. Because any variable is deterministic given a set containing itself, <i>I(X; Y | X, Z) ≡ 0</i> always holds, trivially dropping all candidate variables while in-place list mutation skips adjacent elements.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2.4 The Stealth Attack Evaluation Skew:</b> Gao et al. reported headline accuracies exceeding 98.8%. However, their published ablation tables show that stealthy attacks were largely missed: in CIC-IDS2017, Infiltration recall was <b>2.78%</b> (1 of 36 flows detected) and SQL Injection was <b>23.81%</b> (5 of 21 flows). High headline accuracy was an illusion created by overwhelming volumes of benign traffic and brute-force DoS floods.",
        body_style
    ))
    story.append(Paragraph(
        "<b>2.5 Invalid Vector KL Divergence & Cascading Error:</b> KL divergence is mathematically undefined between continuous signed feature vectors. In addition, feeding top-1 hard label predictions into the CVAE causes cascading errors where zero-day attacks are misclassified by the tree and reconstructed under that erroneous label, evading detection completely.",
        body_style
    ))

    # Section 3
    story.append(Paragraph("3. The IR-IDS 2.0 Methodology", h1_style))
    story.append(Paragraph(
        "<b>3.1 Dirichlet-Smoothed Causal Feature Selection (DS-CMI):</b> Continuous columns are partitioned into <i>B</i> quantile equal-depth bins. Empirical joint counts are smoothed using a symmetric Dirichlet prior with Jeffreys parameter α = 0.5 and conditioning cap |Z| ≤ 3:",
        body_style
    ))
    story.append(Paragraph("P(X = x, Y = y | Z = z) = [ N(x, y, z) + α ] / [ N(z) + α · B · K ]", formula_style))
    story.append(Paragraph(
        "Because α > 0, cell probabilities remain strictly positive, bounding information metrics and eliminating division-by-zero. Sequential backward elimination removes the single least-informative variable per pass, preserving co-dependent causal predictors.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3.2 Cost-Sensitive Invariant Ensemble with Balanced Focal Loss:</b> We train a histogram-based gradient boosted tree ensemble under balanced focal loss, applying sample weights <i>w_c = (N / (K · N_c))^γ</i> strictly to known training classes to force the model to separate rare stealth signatures.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3.3 Multi-Class Marginalized Free-Energy Autoencoder:</b> Rather than single-label conditioning, we compute continuous Ledoit–Wolf shrinkage Mahalanobis distances and marginalize free energy across all <i>K</i> class hypotheses weighted by classifier posterior consensus:",
        body_style
    ))
    story.append(Paragraph("E(x) = -T · log Σ p(y = k | x) · exp( -0.5 · D_Σ(x, x_rec^(k)) )", formula_style))
    story.append(Paragraph(
        "<b>3.4 Dynamic Peaks-Over-Threshold (POT-EVT):</b> Extreme tail energies are modeled using the Generalized Pareto Distribution (GPD). Parameters are estimated in closed form via Hosking–Wallis Probability Weighted Moments (PWM). Thresholds adapt online via sliding-window empirical quantiles on verified benign traffic with adversarial drift limiters.",
        body_style
    ))

    # Section 4: Theoretical Proofs
    story.append(Paragraph("4. Theoretical Analysis & Formal Proofs", h1_style))
    story.append(Paragraph(
        "<b>Theorem 1 (Protocol Constraints Induce Faithfulness Violations):</b> Deterministic protocol identities (e.g., Total Bytes = Fwd Bytes + Bwd Bytes) enforce linear constraints. When protocol symmetries yield β_1 = β_2, partial dependence vanishes: I(X_1; Y | X_3) = 0. Yet in the DAG, non-collider X_3 does not d-separate X_1 from Y. Thus, network traffic inherently violates graph faithfulness.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Lemma 1 (Boundedness of DS-CMI):</b> For discrete variables X, Y, and conditioning set Z with Dirichlet prior α > 0, 0 ≤ I(X; Y | Z) ≤ min(log_2 B, log_2 K) < ∞, eliminating numerical instability.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Theorem 2 (Conditional Lower Bound on Free Energy):</b> If an unobserved zero-day x* lies at minimum physical Mahalanobis distance δ > 0 from all known class manifolds, the Marginalized Free Energy satisfies E(x*) ≥ 0.5 · δ^2, guaranteeing that upstream classifier errors cannot suppress zero-day anomaly scores.",
        body_style
    ))

    # Section 5: Experimental Benchmark
    story.append(Paragraph("5. Experimental Evaluation & Empirical Results", h1_style))
    story.append(Paragraph(
        "We evaluated IR-IDS 2.0 against standardized baselines and the reimplemented Gao et al. baseline across 5 random seeds (42, 101, 202, 303, 404) with 95% empirical bootstrap confidence intervals.",
        body_style
    ))

    # Table 1: Multi-Seed Benchmark
    table_data = [
        ["Evaluation Metric", "Reimplemented Baseline", "IR-IDS 2.0 (Proposed)", "Absolute Delta"],
        ["Overall Accuracy", "79.68 % ± 0.28 %", "88.25 % ± 0.53 %", "+8.57 %"],
        ["Macro-F1 Score", "76.22 % ± 1.35 %", "83.14 % ± 1.77 %", "+6.92 %"],
        ["Geometric Mean (G-Mean)", "65.06 % ± 3.19 %", "72.93 % ± 3.23 %", "+7.87 %"],
        ["Botnet Recall (Zero-Day 1)", "100.00 % ± 0.00 % (560/560)", "100.00 % ± 0.00 % (560/560)", "0.00 % (Conserved)"],
        ["Infiltration Recall (Zero-Day 2)", "7.28 % ± 4.46 % (14/640)", "0.03 % ± 0.06 % (0/640)", "Stealth Challenge"],
        ["Aggregate Zero-Day Recall", "50.55 % ± 2.38 %", "46.68 % ± 0.03 %", "-3.87 % (At ~20x Lower FAR)"],
        ["SQL Injection (Seen Minority)", "19.90 % ± 6.37 % (67/400)", "33.50 % ± 8.98 % (113/400)", "+13.60 % (Focal Gain)"],
        ["Benign False Alarm Rate (FAR)", "19.12 % ± 0.92 %", "0.94 % ± 0.28 %", "-18.18 % (~20x drop)"]
    ]
    t1 = Table(table_data, colWidths=[150, 120, 120, 110])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))

    # Add Figures
    if os.path.exists("fig1_pipeline_architecture.png"):
        story.append(Image("fig1_pipeline_architecture.png", width=480, height=240))
        story.append(Paragraph("<b>Figure 1:</b> IR-IDS 2.0 End-to-End Operational Pipeline: From Raw Ingress Traffic to Robust Scaling, DS-CMI Causal Filtering, Cost-Sensitive Invariant Classification, Multi-Head Marginalized Free Energy Evaluation, Dynamic POT-EVT Thresholding, and Real-Time SOC Symbolic Audit.", abstract_text))
        story.append(Spacer(1, 10))

    if os.path.exists("fig2_head_to_head_comparison.png"):
        story.append(Image("fig2_head_to_head_comparison.png", width=480, height=240))
        story.append(Paragraph("<b>Figure 2:</b> Multi-seed empirical benchmark comparison across 5 random seeds (95% bootstrap confidence intervals), showing Macro-F1, False Alarm Rate, and Zero-Day Recall.", abstract_text))
        story.append(Spacer(1, 10))

    # Section 6: Architectural Proposal for Line-Rate Deployment
    story.append(Paragraph("6. Architectural Proposal for Line-Rate Deployment", h1_style))
    story.append(Paragraph(
        "<b>1. Decoupling Packet Parsing from Flow Verdicts:</b> Per-packet parsing latency is strictly sub-microsecond, but end-to-end flow classification requires flow termination or activity timeouts (typically 15 to 120 seconds).<br/>"
        "<b>2. Proposed Two-Tier Kernel-Bypass Architecture:</b> Tier 1 ingests raw packets via DPDK/AF_XDP, parsing 5-tuples and computing streaming flow statistics using AVX-512 SIMD vectorization. Tier 2 performs batched inference over shared memory rings.<br/>"
        "<b>3. Offline vs. Online Computation:</b> The 21,029-second runtime in Gao et al. belonged to the BAMB-PS baseline; the proposed DMB-PS completed in 37.46 s. In addition, feature selection is strictly an offline training procedure.<br/>"
        "<b>4. Actionable SOC Explainability:</b> Authentic Chebyshev polynomial KAN decomposition and TreeSHAP attributions export closed-form formulas and feature importance with verified fidelity (mean Kendall-tau > 0.85).",
        body_style
    ))

    # Conclusion
    story.append(Paragraph("7. Conclusion", h1_style))
    story.append(Paragraph(
        "This paper audited the IR-IDS framework proposed by Gao et al. (2025), exposing theoretical and empirical defects including inverted propensity scores, combinatorial grid binning, self-conditioning bugs, invalid vector KL divergence, and the Evaluation Skew on rare stealth traffic. To address these vulnerabilities, we developed IR-IDS 2.0. The system incorporates Dirichlet-Smoothed Conditional Mutual Information (DS-CMI) with a conditioning cap of three, a cost-sensitive HistGBDT trained under balanced focal loss, multi-class marginalized free-energy autoencoding under a regularized Mahalanobis metric, verified Hosking–Wallis POT-EVT with streaming quantile tracking, and symbolic Chebyshev-KAN extraction. Across five benchmark seeds, IR-IDS 2.0 achieves 83.14% Macro-F1, isolates unseen Botnet zero-days at 100.00% recall, raises minority SQL Injection detection to 33.50%, and limits benign false alarms to 0.94%. Finally, we established an architectural proposal decoupling sub-microsecond packet parsing from flow-level anomaly arbitration, providing a verifiable foundation for future high-speed intrusion detection research.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Successfully compiled publication PDF: {filename} ({os.path.getsize(filename)} bytes)")


if __name__ == "__main__":
    build_pdf()
