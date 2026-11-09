# IR-IDS 2.0 Comprehensive Revision Plan

This plan maps all required revisions (Parts A–F) to the workspace codebase and manuscript files, establishing strict scientific rigor, honest reporting, and empirical traceability.

---

## 1. Mapping of Requirements to Files

| Section / Item | Topic | Files to Modify / Create | Status |
| :--- | :--- | :--- | :--- |
| **A1** | Correct Gao et al. Table 2 audit (IDS2018 SQLi is 83.33% in full model; 16.67% is ablated) | `paper.tex`, `RESEARCH_PAPER.md`, `CLAIMS_LOG.md` | In Progress |
| **A2** | Soften rhetoric; add sample counts ($N \approx 36$ flows) and small-sample uncertainty | `paper.tex`, `RESEARCH_PAPER.md` | In Progress |
| **A3** | Correct 21,029 s runtime (belongs to BAMB-PS baseline, not DMB-PS: 37 s); note offline FS | `paper.tex`, `RESEARCH_PAPER.md` | In Progress |
| **A4** | Disentangle 0.00% zero-day recall (reimplemented baseline under open-set protocol vs published Gao et al.) | `paper.tex`, `RESEARCH_PAPER.md`, `run_experiment.py` | In Progress |
| **A5** | Retain valid structural criticisms (self-conditioning, list mutation, inverted PS, vector KL, cascading errors) | `paper.tex`, `RESEARCH_PAPER.md` | In Progress |
| **F1** | Resolve missing citations `[?]` with correct `.bib` entries | `references.bib`, `paper.tex` | In Progress |
| **F2** | Remove stray markdown `**` and fix equation/line cross-references | `paper.tex` | In Progress |
| **F3** | Tone down hyperbolic claims ("provably", "catastrophic", "guarantees") | `paper.tex`, `RESEARCH_PAPER.md` | In Progress |
| **F4** | Add dedicated Limitations section (sample size, manifold assumptions, synthetic vs real) | `paper.tex`, `RESEARCH_PAPER.md` | In Progress |
| **F5** | Add formal Reproducibility Statement and execution guide | `paper.tex`, `README.md` | In Progress |
| **C1** | DS-CMI: Bound $|Z|$ cap + stratum pooling; parameter sensitivity ($\alpha, B$) | `code/models/causal_feature_selection.py` | Planned |
| **C2** | Shrink phase: greedy single-feature elimination per pass; match Algorithm 1 listing | `code/models/causal_feature_selection.py`, `paper.tex` | Planned |
| **C3** | Feature selection stability analysis (Jaccard index across seeds vs MI, $G^2$, BAMB) | `code/evaluation/stability_analysis.py`, `results/` | Planned |
| **C4** | EVT/POT fixes: Hosking-Wallis PWM sign verification; sliding-window quantile $u_t$; honest FAR gap | `code/models/dynamic_evt.py`, `tests/test_evt.py` | Planned |
| **C5** | Explainability: Honest discussion of tree interpretability vs boosted ensemble + SHAP fidelity | `paper.tex`, `code/models/cost_sensitive_classifier.py` | Planned |
| **C6** | KAN alignment: Chebyshev-KAN naming; remove synthetic $\cos(x)$; report symbolic fidelity | `code/models/symbolic_kan.py`, `paper.tex` | Planned |
| **D1** | Theorem 2: Restate as conditional lemma on manifold separation $\delta$; discuss failure modes; fix Corollary 1 | `paper.tex`, `RESEARCH_PAPER.md` | Planned |
| **D2** | Theorem 1: Rigorous deterministic constraint proof / counterexample without path cancellation assumption | `paper.tex`, `RESEARCH_PAPER.md` | Planned |
| **D3** | Lemma 1: Verify proof, correct equation citation, clarify plug-in estimator with smoothing | `paper.tex`, `RESEARCH_PAPER.md` | Planned |
| **B1–B4**| Multi-seed benchmark (5+ seeds), bootstrap CIs, per-class zero-day recalls, real data ingestion script | `code/data/`, `code/run_benchmark.py`, `results/` | Planned |
| **B5** | Fix Focal Loss contradiction: restrict focal weighting claims strictly to training classes | `paper.tex`, `code/models/cost_sensitive_classifier.py` | Planned |
| **B6** | Fair POT ablation (compare dynamic POT against static quantile calibrated to $1-q$) | `code/evaluation/ablations.py`, `results/` | Planned |
| **B7** | Reconcile threshold values; replace Fig 1 with architecture diagram; regenerate Fig 2 from raw data | `paper.tex`, `results/` | Planned |
| **B8** | Baselines: Isolation Forest, One-Class SVM, Autoencoder, Energy/Max-Softmax, Plain HistGBDT | `code/models/baselines.py`, `results/` | Planned |
| **E1–E3**| Reframe Section 7: Wire-speed DPDK to Design Proposal; separate packet parsing vs flow timeout | `paper.tex`, `RESEARCH_PAPER.md` | Planned |

---

## 2. Execution Order

1. **Phase 1 (Parts A & F):** Manuscript text overhaul in `paper.tex` and `RESEARCH_PAPER.md`. Correct all citations, remove markdown artifacts, correct misquoted numbers from Gao et al., soften rhetoric, add Limitations and Reproducibility sections.
2. **Phase 2 (Parts C & D):** Mathematical & Algorithmic fixes. Fix DS-CMI conditioning and greedy shrink phase; verify Hosking-Wallis PWM math with unit tests; rewrite Theorems 1 & 2 and Lemma 1 rigorously.
3. **Phase 3 (Parts B & E):** Codebase reorganization into `/code`, implement baselines, run 5-seed benchmark with bootstrap CIs, output raw CSVs to `/results`, reframe deployment claims, and regenerate publication figures.
4. **Phase 4:** Create `CLAIMS_LOG.md`, `CHANGELOG.md`, and `TODO.md`. Build final PDF.

