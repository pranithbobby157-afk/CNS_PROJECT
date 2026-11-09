"""
Unified IR-IDS 2.0 Intrusion Detection System
Coordinates:
1. Robust Causal Feature Selection (Corrected DMB with Dirichlet smoothing).
2. Cost-Sensitive Invariant Classifier with Focal weighting.
3. Multi-Class Marginalized CVAE with Mahalanobis Reconstruction Distance.
4. Adaptive Peaks-Over-Threshold (POT-GPD) Extreme Value Detector.
5. True Symbolic KAN / Feature Attribution Explainability for SOC teams.
"""

import numpy as np
import torch
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from models.causal_feature_selection import RobustCausalSelector
from models.cost_sensitive_classifier import CostSensitiveClassifier, explain_prediction_shap
from models.marginalized_cvae import MultiClassMarginalizedCVAE
from models.dynamic_evt import AdaptiveExtremeValueDetector
from models.symbolic_kan import KolmogorovArnoldLayer, extract_symbolic_representation
from data.preprocessor import FlowDataPreprocessor


@dataclass
class FlowDiagnosis:
    flow_id: int
    predicted_class: str
    is_unknown_attack: bool
    free_energy: float
    anomaly_threshold: float
    confidence: float
    top_explanations: List[Dict[str, Any]]


class IRIDS2System:
    """
    End-to-End Enterprise Intrusion Detection System (IR-IDS 2.0).
    """

    def __init__(
        self,
        known_class_names: List[str],
        alpha_cfs: float = 0.015,
        latent_dim: int = 8,
        target_far: float = 1e-3,
        focal_gamma: float = 0.6,
    ):
        self.known_class_names = known_class_names
        self.num_classes = len(known_class_names)
        self.alpha_cfs = alpha_cfs
        self.latent_dim = latent_dim
        self.target_far = target_far
        self.focal_gamma = focal_gamma

        # Sub-modules
        self.preprocessor = FlowDataPreprocessor()
        self.causal_selector = RobustCausalSelector(alpha_threshold=alpha_cfs)
        self.classifier = CostSensitiveClassifier(
            num_classes=self.num_classes,
            focal_gamma=focal_gamma
        )
        self.cvae = None
        self.evt_detector = AdaptiveExtremeValueDetector(target_far=target_far)
        self.symbolic_kan_encoder = None
        self.selected_feature_indices_: List[int] = []
        self.all_feature_names: List[str] = []

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: Optional[List[str]] = None,
        cvae_epochs: int = 20,
        verbose: bool = True,
    ) -> "IRIDS2System":
        if feature_names is not None:
            self.all_feature_names = feature_names
        else:
            self.all_feature_names = [f"f_{i}" for i in range(X_train.shape[1])]

        if verbose:
            print("=" * 70)
            print("🚀 TRAINING IR-IDS 2.0 PIPELINE")
            print("=" * 70)

        # 1. Preprocessing
        if verbose:
            print("[Stage 1/5] Robust Preprocessing and Outlier Scaling...")
        X_scaled = self.preprocessor.fit_transform(X_train)

        # 2. Causal Feature Selection
        if verbose:
            print("[Stage 2/5] Running Corrected Double Markov Blanket (Dirichlet CMI)...")
        self.causal_selector.fit(X_scaled, y_train)
        self.selected_feature_indices_ = self.causal_selector.selected_features_
        selected_names = [self.all_feature_names[i] for i in self.selected_feature_indices_]
        if verbose:
            print(f"            Selected {len(selected_names)} causal features (pruned {X_train.shape[1] - len(selected_names)} spurious features)")

        X_causal = X_scaled[:, self.selected_feature_indices_]

        # 3. Cost-Sensitive Invariant Classifier
        if verbose:
            print("[Stage 3/5] Fitting Cost-Sensitive Classifier with Focal Balancing...")
        self.classifier.fit(X_causal, y_train)

        # 4. Multi-Class Marginalized CVAE & Symbolic KAN
        if verbose:
            print("[Stage 4/5] Training Multi-Class Marginalized CVAE on Inliers...")
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        input_dim = len(self.selected_feature_indices_)
        self.cvae = MultiClassMarginalizedCVAE(
            input_dim=input_dim,
            num_classes=self.num_classes,
            latent_dim=self.latent_dim
        ).to(device)

        # Covariance for Mahalanobis metric
        cov = np.cov(X_causal, rowvar=False) + 1e-4 * np.eye(input_dim)
        prec = np.linalg.pinv(cov)
        self.cvae.set_precision_matrix(prec)
        self.cvae.fit_cvae(X_causal, y_train, epochs=cvae_epochs, verbose=False)

        # Train Symbolic KAN Layer mapping causal inputs to latent representation
        self.symbolic_kan_encoder = KolmogorovArnoldLayer(
            in_features=input_dim,
            out_features=self.latent_dim,
            degree=3
        ).to(device)

        # 5. Dynamic POT-EVT Anomaly Calibration
        if verbose:
            print("[Stage 5/5] Calibrating Dynamic Peaks-Over-Threshold (POT-EVT)...")
        probs = self.classifier.predict_proba(X_causal)
        train_energies = self.cvae.compute_marginalized_energy(X_causal, probs)
        self.evt_detector.fit(train_energies)

        if verbose:
            print(f"            Calibrated Anomaly Energy Cutoff: {self.evt_detector.extreme_threshold_:.3f}")
            print("✅ IR-IDS 2.0 Training Complete!\n")

        return self

    def predict(self, X: np.ndarray, unknown_label: int = -1) -> np.ndarray:
        """
        Classifies incoming flows:
        Returns known class ID (0..K-1) or unknown_label (-1) for zero-day intrusions.
        """
        X_scaled = self.preprocessor.transform(X)
        X_causal = X_scaled[:, self.selected_feature_indices_]

        raw_preds = self.classifier.predict(X_causal)
        probs = self.classifier.predict_proba(X_causal)
        free_energies = self.cvae.compute_marginalized_energy(X_causal, probs)

        final_preds = np.copy(raw_preds)
        is_unknown = self.evt_detector.is_anomaly(free_energies)
        final_preds[is_unknown] = unknown_label
        return final_preds

    def diagnose_flow(self, flow_vector: np.ndarray, flow_id: int = 0) -> FlowDiagnosis:
        """
        Generates an auditable diagnostic report with SHAP feature attributions
        and zero-day risk assessment for a specific flow.
        """
        flow_2d = flow_vector.reshape(1, -1)
        X_scaled = self.preprocessor.transform(flow_2d)
        X_causal = X_scaled[:, self.selected_feature_indices_]

        probs = self.classifier.predict_proba(X_causal)[0]
        pred_cls_id = int(np.argmax(probs))
        pred_cls_name = self.known_class_names[pred_cls_id]
        confidence = float(probs[pred_cls_id])

        energy = float(self.cvae.compute_marginalized_energy(X_causal, probs.reshape(1, -1))[0])
        is_unknown = bool(self.evt_detector.is_anomaly(np.array([energy]))[0])

        causal_names = [self.all_feature_names[i] for i in self.selected_feature_indices_]
        explanations = explain_prediction_shap(
            self.classifier,
            X_causal[0],
            feature_names=causal_names,
            top_k=4
        )

        return FlowDiagnosis(
            flow_id=flow_id,
            predicted_class="UNKNOWN_ATTACK (Zero-Day)" if is_unknown else pred_cls_name,
            is_unknown_attack=is_unknown,
            free_energy=energy,
            anomaly_threshold=float(self.evt_detector.extreme_threshold_),
            confidence=confidence,
            top_explanations=explanations,
        )

    def export_symbolic_formulas(self) -> List[Dict[str, Any]]:
        """Exports human-readable algebraic formulas from the KAN layer."""
        causal_names = [self.all_feature_names[i] for i in self.selected_feature_indices_]
        return extract_symbolic_representation(self.symbolic_kan_encoder, causal_names)

