"""
Chebyshev Kolmogorov-Arnold Network (Chebyshev-KAN)
Fixes C6:
1. Reconciles naming: Uses Chebyshev polynomial expansions consistently (not B-splines).
2. Extracts authentic algebraic polynomials (T0, T1, T2, T3) without fictitious trigonometric functions.
3. Evaluates symbolic fidelity (MSE between neural spline output and symbolic polynomial).
"""

import numpy as np
import torch
import torch.nn as nn
from typing import List, Dict, Any, Tuple


class ChebyshevKANLayer(nn.Module):
    """
    Chebyshev-polynomial Kolmogorov-Arnold Network Layer:
    phi_{i,j}(x_i) = w_base * SiLU(x_i) + sum_{d=0}^D c_{i,j,d} * T_d(tanh(x_i))
    """

    def __init__(self, in_features: int, out_features: int, degree: int = 3):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.degree = degree

        self.base_weight = nn.Parameter(torch.randn(out_features, in_features) * 0.1)
        self.poly_coeffs = nn.Parameter(torch.randn(out_features, in_features, degree + 1) * 0.05)
        self.act = nn.SiLU()

    def _eval_chebyshev(self, x: torch.Tensor) -> torch.Tensor:
        x_norm = torch.tanh(x)
        T = [torch.ones_like(x_norm), x_norm]
        for d in range(2, self.degree + 1):
            T.append(2.0 * x_norm * T[-1] - T[-2])
        return torch.stack(T, dim=-1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base_out = nn.functional.linear(self.act(x), self.base_weight)
        cheb_basis = self._eval_chebyshev(x)
        poly_out = torch.einsum("bid,oid->bo", cheb_basis, self.poly_coeffs)
        return base_out + poly_out


def extract_real_chebyshev_formulas(
    kan_layer: ChebyshevKANLayer,
    feature_names: List[str],
    prune_threshold: float = 0.02
) -> List[Dict[str, Any]]:
    """
    Extracts authentic Chebyshev algebraic polynomials.
    Replaces synthetic trigonometric terms with real polynomials:
    T0(u)=1, T1(u)=u, T2(u)=2u^2-1, T3(u)=4u^3-3u.
    """
    formulas = []
    base_w = kan_layer.base_weight.detach().cpu().numpy()
    coeffs = kan_layer.poly_coeffs.detach().cpu().numpy()

    out_features, in_features, deg_plus_1 = coeffs.shape

    for out_idx in range(out_features):
        active_terms = []
        for in_idx in range(in_features):
            w_b = base_w[out_idx, in_idx]
            c = coeffs[out_idx, in_idx]
            mag = abs(w_b) + np.sum(np.abs(c))
            if mag < prune_threshold:
                continue

            fname = feature_names[in_idx] if in_idx < len(feature_names) else f"x_{in_idx}"
            u = f"tanh({fname})"
            terms = [f"{c[0]:+.3f}"]
            if abs(c[1]) > 1e-4:
                terms.append(f"{c[1]:+.3f}*{u}")
            if len(c) > 2 and abs(c[2]) > 1e-4:
                terms.append(f"{c[2]:+.3f}*(2*{u}^2 - 1)")
            if len(c) > 3 and abs(c[3]) > 1e-4:
                terms.append(f"{c[3]:+.3f}*(4*{u}^3 - 3*{u})")

            poly_expr = " ".join(terms)
            active_terms.append(f"[{w_b:+.3f}*SiLU({fname}) + ({poly_expr})]")

        eq_str = " + ".join(active_terms) if active_terms else "0.0"
        formulas.append({
            "output_node": out_idx,
            "active_inputs": len(active_terms),
            "symbolic_formula": f"z_{out_idx} = {eq_str}"
        })

    return formulas


def evaluate_symbolic_approximation_loss(
    kan_layer: ChebyshevKANLayer,
    X_val: np.ndarray,
    prune_threshold: float = 0.02
) -> float:
    """Measures reconstruction MSE between full KAN output and pruned symbolic formulas."""
    kan_layer.eval()
    with torch.no_grad():
        X_t = torch.tensor(X_val, dtype=torch.float32)
        full_out = kan_layer(X_t).numpy()

        # Simulate pruned evaluation
        base_w = kan_layer.base_weight.detach().cpu().numpy()
        coeffs = kan_layer.poly_coeffs.detach().cpu().numpy()
        mask = (np.abs(base_w) + np.sum(np.abs(coeffs), axis=-1)) >= prune_threshold

        pruned_base = base_w * mask
        pruned_coeffs = coeffs * mask[:, :, np.newaxis]

        # Re-evaluate
        act_x = torch.nn.functional.silu(X_t).numpy()
        p_base = act_x @ pruned_base.T
        cheb = kan_layer._eval_chebyshev(X_t).numpy()
        p_poly = np.einsum("bid,oid->bo", cheb, pruned_coeffs)
        pruned_out = p_base + p_poly

        mse = float(np.mean((full_out - pruned_out) ** 2))
    return mse

