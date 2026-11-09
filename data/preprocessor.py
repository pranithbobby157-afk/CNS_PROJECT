"""
Flow Data Preprocessing and Outlier Scaling Pipeline
Replaces the flawed Equations (6)-(9) 1D K-means binning with robust non-linear scaling.
"""

import numpy as np
from typing import Tuple, Optional


class FlowDataPreprocessor:
    """
    Robust feature scaling pipeline designed for heavy-tailed, bursty network traffic.
    Prevents outlier distortion in distance metrics without negative binning artifacts.
    """

    def __init__(self, clip_quantile: float = 0.995):
        self.clip_quantile = clip_quantile
        self.medians_: Optional[np.ndarray] = None
        self.iqr_: Optional[np.ndarray] = None
        self.upper_limits_: Optional[np.ndarray] = None
        self.lower_limits_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray) -> "FlowDataPreprocessor":
        self.medians_ = np.median(X, axis=0)
        q25 = np.percentile(X, 25, axis=0)
        q75 = np.percentile(X, 75, axis=0)
        iqr = q75 - q25
        # Avoid division by zero on static features
        iqr[iqr < 1e-4] = 1.0
        self.iqr_ = iqr

        self.lower_limits_ = np.percentile(X, (1.0 - self.clip_quantile) * 100, axis=0)
        self.upper_limits_ = np.percentile(X, self.clip_quantile * 100, axis=0)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if self.medians_ is None or self.iqr_ is None:
            raise RuntimeError("Preprocessor must be fitted first.")

        # Robust Winsorization (clipping extreme burst outliers)
        X_clipped = np.clip(X, self.lower_limits_, self.upper_limits_)
        # Median / Interquartile Range scaling
        X_scaled = (X_clipped - self.medians_) / self.iqr_
        return X_scaled.astype(np.float32)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)

