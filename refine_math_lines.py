# -*- coding: utf-8 -*-
"""
Apply compact, clean notations to equations in paper.tex
so that EVERY SINGLE LINE fits cleanly within 3.5-inch column without overflow.
"""

with open("paper.tex", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Simplify Eq 15 (CMI sum)
old_cmi = r"""\begin{equation}
\label{eq:cmi_sum}
\begin{aligned}
I(X; Y \mid Z) &= \sum_{z \in \mathcal{S}_Z} \frac{N(z)}{N} \sum_{x=0}^{B-1} \sum_{y=0}^{K-1} P(x, y \mid z) \\
&\quad \times \log_2 \frac{P(x, y \mid z)}{P(x \mid z) P(y \mid z)}
\end{aligned}
\end{equation}"""

new_cmi = r"""\begin{equation}
\label{eq:cmi_sum}
\begin{aligned}
I(X; Y \mid Z) &= \sum_{z \in \mathcal{S}_Z} \frac{N(z)}{N} \sum_{x,y} P(x, y \mid z) \\
&\quad \times \log_2 \left( \frac{P(x, y \mid z)}{P(x \mid z) P(y \mid z)} \right)
\end{aligned}
\end{equation}"""

text = text.replace(old_cmi, new_cmi)

# 2. Simplify Eq 17 (Focal loss)
old_focal = r"""\begin{equation}
\label{eq:focal_loss}
\begin{aligned}
\mathcal{L}_{\text{Focal}}(\theta) = - \sum_{i=1}^{N} &w_{y_i} \left( 1 - p(y_i \mid x_i) \right)^\gamma \\
&\times \log p(y_i \mid x_i)
\end{aligned}
\end{equation}"""

new_focal = r"""\begin{equation}
\label{eq:focal_loss}
\begin{aligned}
\mathcal{L}_{\text{Focal}}(\theta) = - \sum_{i=1}^{N} w_{y_i} (1 - p_i)^\gamma \log(p_i)
\end{aligned}
\end{equation}
where $p_i = p(y_i \mid x_i)$."""

text = text.replace(old_focal, new_focal)

# 3. Simplify Eq 18 (TreeSHAP)
old_shap = r"""\begin{equation}
\label{eq:treeshap}
\begin{aligned}
\phi_i(f, x) = \sum_{S \subseteq \mathcal{F} \setminus \{i\}} &\frac{|S|!(|\mathcal{F}| - |S| - 1)!}{|\mathcal{F}|!} \\
&\times \left( f(S \cup \{i\}) - f(S) \right)
\end{aligned}
\end{equation}"""

new_shap = r"""\begin{equation}
\label{eq:treeshap}
\begin{aligned}
\phi_i(f, x) = \sum_{S \subseteq \mathcal{F} \setminus \{i\}} \frac{|S|!(|\mathcal{F}| - |S| - 1)!}{|\mathcal{F}|!} \Delta_i(S)
\end{aligned}
\end{equation}
where $\Delta_i(S) = f(S \cup \{i\}) - f(S)$."""

text = text.replace(old_shap, new_shap)

# 4. Simplify Eq 28 (Streaming Quantile)
old_sq = r"""\begin{equation}
\label{eq:streaming_quantile}
\begin{aligned}
\Delta u_t &= Q_{0.85}(\mathcal{W}_t) - u_{t-1} \\
u_t &= u_{t-1} + \text{clip}\left( \Delta u_t, -\delta_{\text{max}} u_{t-1}, \delta_{\text{max}} u_{t-1} \right)
\end{aligned}
\end{equation}"""

new_sq = r"""\begin{equation}
\label{eq:streaming_quantile}
\begin{aligned}
\Delta u_t &= Q_{0.85}(\mathcal{W}_t) - u_{t-1} \\
u_t &= u_{t-1} + \text{clip}\left( \Delta u_t, -\delta_{\text{m}} u_{t-1}, \delta_{\text{m}} u_{t-1} \right)
\end{aligned}
\end{equation}"""

text = text.replace(old_sq, new_sq)

# 5. Simplify Eq 36 (separation condition)
old_sep = r"""\begin{equation}
\label{eq:separation_condition}
\begin{aligned}
\inf_{z \in \mathcal{Z}} \mathcal{D}_{\mathbf{\Sigma}}\left(x^*, \text{Decoder}_k(z)\right) \ge \delta^2, \quad \forall k
\end{aligned}
\end{equation}"""

new_sep = r"""\begin{equation}
\label{eq:separation_condition}
\begin{aligned}
\inf_{z \in \mathcal{Z}} \mathcal{D}_{\mathbf{\Sigma}}(x^*, \text{Decoder}_k(z)) \ge \delta^2, \quad \forall k
\end{aligned}
\end{equation}"""

text = text.replace(old_sep, new_sep)

# 6. Simplify Eq 38 & 39 (Exponential bound & sum bound in proof)
old_exp = r"""\begin{equation}
\label{eq:exp_bound}
\begin{aligned}
\exp\left( -\frac{1}{2} \mathcal{D}_{\mathbf{\Sigma}}\left(x^*, \hat{x}^{*(k)}\right) \right) \le \exp\left( -\frac{1}{2} \delta^2 \right)
\end{aligned}
\end{equation}"""

new_exp = r"""\begin{equation}
\label{eq:exp_bound}
\begin{aligned}
\exp\left( -\tfrac{1}{2} \mathcal{D}_{\mathbf{\Sigma}}(x^*, \hat{x}^{*(k)}) \right) \le e^{-\frac{1}{2} \delta^2}
\end{aligned}
\end{equation}"""

text = text.replace(old_exp, new_exp)

old_sum = r"""\begin{equation}
\label{eq:sum_bound}
\begin{aligned}
\sum_{k=0}^{K-1} &p(y = k \mid x^*) \exp\left( -\frac{1}{2} \mathcal{D}_{\mathbf{\Sigma}}\left(x^*, \hat{x}^{*(k)}\right) \right) \\
&\le \exp\left( -\frac{1}{2} \delta^2 \right) \sum_{k=0}^{K-1} p(y = k \mid x^*) \\
&= \exp\left( -\frac{1}{2} \delta^2 \right)
\end{aligned}
\end{equation}"""

new_sum = r"""\begin{equation}
\label{eq:sum_bound}
\begin{aligned}
\sum_{k=0}^{K-1} &p(y = k \mid x^*) \exp\left( -\tfrac{1}{2} \mathcal{D}_{\mathbf{\Sigma}} \right) \\
&\le e^{-\frac{1}{2}\delta^2} \sum_k p(y = k \mid x^*) = e^{-\frac{1}{2}\delta^2}
\end{aligned}
\end{equation}"""

text = text.replace(old_sum, new_sum)

with open("paper.tex", "w", encoding="utf-8") as f:
    f.write(text)

print("Applied compact mathematical notations successfully!")
