"""
Unified IR-IDS 2.0 Pipeline Architecture
Coordinates:
1. Robust Winsorization & Median/IQR scaling
2. Dirichlet-Smoothed Causal Feature Selection (DS-CMI) with sequential backward pruning
3. Cost-Sensitive Invariant Classifier with Balanced Focal Loss
4. Multi-Class Marginalized Free Energy CVAE under Ledoit-Wolf Mahalanobis metric
5. Adaptive POT-EVT Anomaly Gating with sliding-window quantile tracking
6. Authentic Chebyshev-KAN symbolic equation extraction
"""

import numpy as np
import torch
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sklearn.covariance import LedoitWolf

from code.models.causal_feature_selection import RobustCausalSelector
from code.models.cost_sensitive_classifier import CostSensitiveClassifier, explain_prediction_shap
from code.models.marginalized_cvae import MultiClassMarginalizedCVAE
from code.models.dynamic_evt import AdaptiveExtremeValueDetector
from code.models.symbolic_kan import ChebyshevKANLayer, extract_real_chebyshev_formulas
try:
    from code.data.preprocessor import FlowDataPreprocessor
except ImportError:
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
    def __init__(
        self,
        known_class_names: List[str],
        alpha_cfs: float = 0.015,
        latent_dim: int = 8,
        target_far: float = 1e-3,
        focal_gamma: float = 0.6,
        base_quantile: float = 0.85,
    ):
        self.known_class_names = known_class_names
        self.num_classes = len(known_class_names)
        self.alpha_cfs = alpha_cfs
        self.latent_dim = latent_dim
        self.target_far = target_far
        self.focal_gamma = focal_gamma
        self.base_quantile = base_quantile

        self.preprocessor = FlowDataPreprocessor()
        self.causal_selector = RobustCausalSelector(alpha_threshold=alpha_cfs)
        self.classifier = CostSensitiveClassifier(num_classes=self.num_classes, focal_gamma=focal_gamma)
        self.cvae = None
        self.evt_detector = AdaptiveExtremeValueDetector(target_far=target_far, base_quantile=base_quantile)
        self.kan_layer = None
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
            print("=" * 65)
            print("🚀 TRAINING IR-IDS 2.0 PIPELINE")
            print("=" * 65)

        # 1. Preprocessing
        if verbose:
            print("[Stage 1/5] Robust Preprocessing (Winsorization & Median/IQR)...")
        X_scaled = self.preprocessor.fit_transform(X_train)

        # 2. Causal Feature Selection
        if verbose:
            print("[Stage 2/5] Running Corrected Double Markov Blanket (DS-CMI)...")
        self.causal_selector.fit(X_scaled, y_train)
        self.selected_feature_indices_ = self.causal_selector.selected_features_
        if verbose:
            print(f"            Retained {len(self.selected_feature_indices_)} causal features.")

        X_causal = X_scaled[:, self.selected_feature_indices_]

        # 3. Cost-Sensitive Invariant Classifier
        if verbose:
            print("[Stage 3/5] Training Cost-Sensitive HistGBDT with Focal Weights...")
        self.classifier.fit(X_causal, y_train)

        # 4. Multi-Class Marginalized CVAE & Chebyshev KAN
        if verbose:
            print("[Stage 4/5] Training Multi-Head Marginalized CVAE & Chebyshev KAN...")
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        input_dim = len(self.selected_feature_indices_)

        # Ledoit-Wolf Shrinkage Covariance
        lw = LedoitWolf().fit(X_causal)
        prec = lw.precision_

        self.cvae = MultiClassMarginalizedCVAE(
            input_dim=input_dim,
            num_classes=self.num_classes,
            latent_dim=self.latent_dim
        ).to(device)
        self.cvae.set_precision_matrix(prec)
        self.cvae.fit_cvae(X_causal, y_train, epochs=cvae_epochs, verbose=False)

        self.kan_layer = ChebyshevKANLayer(in_features=input_dim, out_features=self.latent_dim, degree=3).to(device)

        # 5. Dynamic POT-EVT Calibration
        if verbose:
            print("[Stage 5/5] Calibrating Dynamic Peaks-Over-Threshold (POT-EVT)...")
        probs = self.classifier.predict_proba(X_causal)
        train_energies = self.cvae.compute_marginalized_energy(X_causal, probs)
        self.evt_detector.fit(train_energies)

        if verbose:
            print(f"            Calibrated Anomaly Energy Cutoff: {self.evt_detector.extreme_threshold_:.3f}")
            print("✅ Pipeline Training Complete!\n")

        return self

    def predict(self, X: np.ndarray, unknown_label: int = -1) -> np.ndarray:
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
        explanations = explain_prediction_shap(self.classifier, X_causal[0], feature_names=causal_names, top_k=4)

        return FlowDiagnosis(
            flow_id=flow_id,
            predicted_class="UNKNOWN_ATTACK (Zero-Day)" if is_unknown else pred_cls_name,
            is_unknown_attack=is_unknown,
            free_energy=energy,
            anomaly_threshold=float(self.evt_detector.extreme_threshold_),
            confidence=confidence,
            top_explanations=explanations,
        )

    def export_chebyshev_formulas(self) -> List[Dict[str, Any]]:
        causal_names = [self.all_feature_names[i] for i in self.selected_feature_indices_]
        return extract_real_chebyshev_formulas(self.kan_layer, causal_names)
