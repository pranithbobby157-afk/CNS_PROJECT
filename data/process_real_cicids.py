"""
Real-World Dataset Ingestion and Evaluation Pipeline (IR-IDS 2.0)
Processes real CSV exports from:
- CIC-IDS2017
- CSE-CIC-IDS2018
- CIC-DDoS2019
- UNSW-NB15
- CIC-IoT-IDAD-2024

Automatically handles:
1. Header sanitization, whitespace trimming, Inf/NaN cleaning.
2. Partitioning into known training classes and held-out zero-day attack classes.
3. Fitting IR-IDS 2.0 pipeline and outputting detailed evaluation metrics and confusion reports.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any

from pipeline.irids2_system import IRIDS2System
from evaluation.metrics import compute_intrusion_metrics, print_evaluation_report


def clean_and_load_csv(csv_path: str, label_col: str = "Label") -> Tuple[pd.DataFrame, pd.Series]:
    """Loads and sanitizes raw intrusion detection CSVs."""
    print(f"Loading raw dataset from: {csv_path} ...")
    df = pd.read_csv(csv_path, low_memory=False)
    
    # Strip whitespace from column names
    df.columns = [c.strip() for c in df.columns]

    # Find label column
    matched_label_cols = [c for c in df.columns if c.lower() in [label_col.lower(), "label", "attack_cat", "class"]]
    if not matched_label_cols:
        raise ValueError(f"Could not find label column '{label_col}' in columns: {list(df.columns)}")
    actual_label_col = matched_label_cols[0]

    y_raw = df[actual_label_col].astype(str).str.strip()
    X_raw = df.drop(columns=[actual_label_col])

    # Drop non-numeric identifier columns if present (IPs, Timestamps, Flow IDs)
    drop_patterns = ["id", "timestamp", "ip", "flow_id", "date"]
    cols_to_drop = [c for c in X_raw.columns if any(p in c.lower() for p in drop_patterns)]
    if cols_to_drop:
        X_raw = X_raw.drop(columns=cols_to_drop)

    # Sanitize Infinite and NaN values
    X_numeric = X_raw.select_dtypes(include=[np.number])
    X_numeric = X_numeric.replace([np.inf, -np.inf], np.nan)
    X_numeric = X_numeric.fillna(X_numeric.median(numeric_only=True))

    print(f"Sanitized dataset: {len(X_numeric)} samples, {X_numeric.shape[1]} numeric features.")
    print(f"Class distribution:\n{y_raw.value_counts()}")

    return X_numeric, y_raw


def create_zero_day_split(
    X: pd.DataFrame,
    y: pd.Series,
    zero_day_classes: List[str],
    train_ratio: float = 0.7,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Creates a realistic zero-day evaluation split:
    - Zero-day classes are completely held out from training (0% in train).
    - Known classes are stratified across train and test.
    """
    np.random.seed(seed)
    unique_classes = sorted(y.unique())

    known_classes = [c for c in unique_classes if c not in zero_day_classes]
    print(f"\nKnown Classes for Training : {known_classes}")
    print(f"Held-out Zero-Day Attacks  : {zero_day_classes}")

    train_indices = []
    test_indices = []

    for cls in known_classes:
        cls_idx = np.where(y == cls)[0]
        np.random.shuffle(cls_idx)
        n_train = int(len(cls_idx) * train_ratio)
        train_indices.extend(cls_idx[:n_train])
        test_indices.extend(cls_idx[n_train:])

    # All zero-day instances go exclusively to the test set
    for cls in zero_day_classes:
        cls_idx = np.where(y == cls)[0]
        test_indices.extend(cls_idx)

    train_indices = np.array(train_indices)
    test_indices = np.array(test_indices)

    np.random.shuffle(train_indices)
    np.random.shuffle(test_indices)

    # Integer encode labels
    label_map = {c: i for i, c in enumerate(known_classes)}
    for zc in zero_day_classes:
        label_map[zc] = -1  # -1 represents unknown zero-day anomaly

    y_train = np.array([label_map[y.iloc[i]] for i in train_indices], dtype=np.int64)
    y_test = np.array([label_map[y.iloc[i]] for i in test_indices], dtype=np.int64)

    return {
        "X_train": X.iloc[train_indices].values.astype(np.float32),
        "y_train": y_train,
        "X_test": X.iloc[test_indices].values.astype(np.float32),
        "y_test": y_test,
        "feature_names": list(X.columns),
        "known_classes": known_classes,
        "zero_day_classes": zero_day_classes
    }


def evaluate_real_traffic(csv_path: str, zero_days: List[str]):
    """Runs end-to-end IR-IDS 2.0 on real network traffic."""
    X, y = clean_and_load_csv(csv_path)
    split = create_zero_day_split(X, y, zero_day_classes=zero_days)

    print("\nInitializing IR-IDS 2.0 Engine...")
    system = IRIDS2System(
        known_class_names=split["known_classes"],
        alpha_cfs=0.015,
        latent_dim=8,
        target_far=1e-3,
        focal_gamma=0.7
    )

    system.fit(
        split["X_train"],
        split["y_train"],
        feature_names=split["feature_names"],
        cvae_epochs=15,
        verbose=True
    )

    print("Evaluating against test traffic (Known + Zero-Day)...")
    y_preds = system.predict(split["X_test"], unknown_label=-1)

    metrics = compute_intrusion_metrics(split["y_test"], y_preds, split["known_classes"])
    print_evaluation_report(metrics, title="REAL TRAFFIC BENCHMARK REPORT (IR-IDS 2.0)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate IR-IDS 2.0 on real PCAP/CSV datasets.")
    parser.add_argument("--csv", type=str, help="Path to real network traffic CSV file.")
    parser.add_argument("--zero_days", nargs="+", default=["Infiltration", "Heartbleed", "Bot"], help="Class names to hold out as zero-day attacks.")
    args = parser.parse_args()

    if args.csv and os.path.exists(args.csv):
        evaluate_real_traffic(args.csv, args.zero_days)
    else:
        print("No CSV provided or file not found. Running benchmark generator demo...")
        from data.dataset_loader import generate_synthetic_benchmark_dataset
        demo_split = generate_synthetic_benchmark_dataset(n_samples_train=5000, n_samples_test=2000, n_features=35)
        sys = IRIDS2System(known_class_names=demo_split.known_classes, alpha_cfs=0.015)
        sys.fit(demo_split.X_train, demo_split.y_train, feature_names=demo_split.feature_names, cvae_epochs=8)
        preds = sys.predict(demo_split.X_test)
        m = compute_intrusion_metrics(demo_split.y_test, preds, demo_split.known_classes)
        print_evaluation_report(m, title="DEMO PIPELINE VERIFICATION")

