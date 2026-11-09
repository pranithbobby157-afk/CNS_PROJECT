"""
Evaluation Metrics for Intrusion Detection
Exposes the "Accuracy Paradox" by computing:
- Macro-F1 and G-Mean (penalizing stealth misses).
- Per-class detection rates (Infiltration, SQLi, DoS).
- Zero-day unknown attack detection rate.
- Benign False Alarm Rate (FAR).
"""

import numpy as np
from typing import Dict, Any, List


def compute_intrusion_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    known_classes: List[str],
    unknown_label: int = -1,
) -> Dict[str, Any]:
    """
    Computes rigorous cybersecurity metrics beyond misleading overall accuracy.
    """
    total_samples = len(y_true)
    overall_accuracy = float(np.mean(y_true == y_pred))

    # Identify Benign index (assumed to be 0)
    benign_mask = (y_true == 0)
    if np.sum(benign_mask) > 0:
        benign_false_positives = np.sum((y_pred != 0) & benign_mask)
        far = float(benign_false_positives / np.sum(benign_mask))
    else:
        far = 0.0

    # Unknown / Zero-day attack recall
    unknown_mask = (y_true == unknown_label)
    if np.sum(unknown_mask) > 0:
        unknown_detected = np.sum(y_pred[unknown_mask] == unknown_label)
        unknown_recall = float(unknown_detected / np.sum(unknown_mask))
    else:
        unknown_recall = 1.0

    # Per-class detection rate for known classes
    class_recalls = {}
    recalls_for_gmean = []

    for c_idx, c_name in enumerate(known_classes):
        c_mask = (y_true == c_idx)
        if np.sum(c_mask) > 0:
            rec = float(np.sum(y_pred[c_mask] == c_idx) / np.sum(c_mask))
            class_recalls[c_name] = rec
            recalls_for_gmean.append(max(rec, 1e-4))

    # Geometric Mean of Recalls
    g_mean = float(np.exp(np.mean(np.log(recalls_for_gmean)))) if recalls_for_gmean else 0.0

    # Macro-F1 across known classes
    f1_list = []
    for c_idx, c_name in enumerate(known_classes):
        tp = np.sum((y_pred == c_idx) & (y_true == c_idx))
        fp = np.sum((y_pred == c_idx) & (y_true != c_idx))
        fn = np.sum((y_pred != c_idx) & (y_true == c_idx))
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        f1_list.append(f1)

    macro_f1 = float(np.mean(f1_list))

    return {
        "overall_accuracy": overall_accuracy,
        "macro_f1": macro_f1,
        "g_mean": g_mean,
        "false_alarm_rate": far,
        "unknown_zero_day_recall": unknown_recall,
        "class_recalls": class_recalls,
    }


def print_evaluation_report(metrics: Dict[str, Any], title: str = "PERFORMANCE REPORT"):
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)
    print(f"Overall Accuracy         : {metrics['overall_accuracy'] * 100:.2f} %")
    print(f"Macro-F1 Score           : {metrics['macro_f1'] * 100:.2f} %")
    print(f"Geometric Mean (G-Mean)  : {metrics['g_mean'] * 100:.2f} %")
    print(f"Benign False Alarm (FAR) : {metrics['false_alarm_rate'] * 100:.3f} %")
    print(f"Zero-Day Unknown Recall  : {metrics['unknown_zero_day_recall'] * 100:.2f} %")
    print("-" * 65)
    print("Individual Class Recalls:")
    for cls_name, rec in metrics["class_recalls"].items():
        print(f"  • {cls_name:<22}: {rec * 100:.2f} %")
    print("=" * 65 + "\n")

