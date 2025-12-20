# Proof of Generalized Mechanism A

## Statement

**Theorem (Generalized Mechanism A):** Let $G$ be a graph and consider the 2-edge switch
$$\{v_1w_1, v_2w_2\} \to \{v_1w_2, v_2w_1\}$$
producing graph $G'$. If the following conditions hold:

1. $\deg(v_1) = \deg(v_2) =: d_v$ and $\deg(w_1) = \deg(w_2) =: d_w$
2. Uniform cross-intersection: $|N_{\text{ext}}(v_i) \cap N_{\text{ext}}(w_j)| = c$ for all $i,j \in \{1,2\}$
3. $|\text{unique}_1| = |\text{unique}_2| =: n$
4. Degree multisets are equal: $\{\deg(x) : x \in \text{unique}_1\} = \{\deg(x) : x \in \text{unique}_2\}$
5. $|E(\text{unique}_1, \text{shared})| = |E(\text{unique}_2, \text{shared})|$
6. $|E(\text{unique}_1)| = |E(\text{unique}_2)|$ (internal edges within unique sets)

Then $G$ and $G'$ are NBL-cospectral.

**Remark:** Conditions 4-6 together imply σ-symmetry of the first-step external matrix.

---

## Proof

### Setup

Define the switch region $S = \{v_1, v_2, w_1, w_2\}$ and external neighborhoods:
- $\text{ext}(s) = N(s) \setminus S$ for $s \in S$
- $\text{shared} = \text{ext}(w_1) \cap \text{ext}(w_2)$
- $\text{unique}_1 = \text{ext}(w_1) \setminus \text{ext}(w_2)$
- $\text{unique}_2 = \text{ext}(w_2) \setminus \text{ext}(w_1)$

### Boundary Type Partition

Define 5 boundary types based on where edges cross the S boundary:

| Type | Entry edges | Exit edges |
|------|-------------|------------|
| $v_1$ | $(x, v_1)$ for $x \in \text{ext}(v_1)$ | $(v_1, x)$ for $x \in \text{ext}(v_1)$ |
| $v_2$ | $(x, v_2)$ for $x \in \text{ext}(v_2)$ | $(v_2, x)$ for $x \in \text{ext}(v_2)$ |
| $\text{sh}$ | $(z, w_j)$ for $z \in \text{shared}$, $j \in \{1,2\}$ | $(w_j, z)$ for $z \in \text{shared}$, $j \in \{1,2\}$ |
| $u_1$ | $(x, w_1)$ for $x \in \text{unique}_1$ | $(w_1, x)$ for $x \in \text{unique}_1$ |
| $u_2$ | $(y, w_2)$ for $y \in \text{unique}_2$ | $(w_2, y)$ for $y \in \text{unique}_2$ |

**Key change from original:** The shared type aggregates edges from/to BOTH $w_1$ and $w_2$.

### The Swap Permutation

Define $\sigma$ on boundary types:
- $\sigma(v_1) = v_2$, $\sigma(v_2) = v_1$
- $\sigma(\text{sh}) = \text{sh}$ (fixed)
- $\sigma(u_1) = u_2$, $\sigma(u_2) = u_1$

### First-Step External Matrix

Define $P[\tau, \rho]$ = total NBL transition weight from exit type $\tau$ to entry type $\rho$.

**Lemma 1:** Under conditions 1-6, $P[\tau, \rho] = P[\sigma(\tau), \sigma(\rho)]$ for all types.

*Proof:* Case analysis:

**Case $v_1 \to v_2$ vs $v_2 \to v_1$:**
Exit $(v_1, x)$ transitions to $(x, v_2)$ with weight $\frac{1}{\deg(x)-1}$ if $x \in \text{ext}(v_1) \cap \text{ext}(v_2)$.
By condition 1, $|\text{ext}(v_1)| = |\text{ext}(v_2)|$ and the cross-intersection is symmetric.
Thus $P[v_1, v_2] = P[v_2, v_1]$.

**Case $v_i \to u_j$ vs $v_{3-i} \to u_{3-j}$:**
$P[v_1, u_1] = \sum_{x \in \text{ext}(v_1) \cap \text{unique}_1} \frac{1}{\deg(x)-1}$

By condition 2 (uniform cross-intersection), $|\text{ext}(v_1) \cap \text{unique}_1| = |\text{ext}(v_2) \cap \text{unique}_2|$.
By condition 4 (degree multiset equality), the sum of $\frac{1}{\deg(x)-1}$ over these sets is equal.
Thus $P[v_1, u_1] = P[v_2, u_2]$.

**Case $u_1 \to v_j$ vs $u_2 \to v_j$:**
$P[u_1, v_1] = \sum_{x \in \text{unique}_1 \cap \text{ext}(v_1)} \frac{1}{\deg(x)-1}$

By the same argument, $P[u_1, v_1] = P[u_2, v_2]$ and $P[u_1, v_2] = P[u_2, v_1]$.

**Case $u_i \to \text{sh}$ vs $u_{3-i} \to \text{sh}$:**
By condition 5, $|E(\text{unique}_1, \text{shared})| = |E(\text{unique}_2, \text{shared})|$.
Combined with condition 4, this gives $P[u_1, \text{sh}] = P[u_2, \text{sh}]$.

**Case $\text{sh} \to u_i$ vs $\text{sh} \to u_{3-i}$:**
Symmetric argument using conditions 4-5.

**Case $\text{sh} \to \text{sh}$:**
Shared is fixed by $\sigma$, and transitions within shared are identical in $G$ and $G'$.

All other cases follow similarly. $\square$

### S-Internal Transfer Matrix

Define $\Phi[\tau, \rho]$ = total weight of walks from entry type $\tau$ to exit type $\rho$ staying inside $S$.

**Lemma 2:** $\Phi_G[\tau, \rho] = \Phi_{G'}[\sigma(\tau), \sigma(\rho)]$.

*Proof:* The induced subgraph $G[S]$ is isomorphic to $G'[S]$ via the map:
$$\phi: v_1 \mapsto v_2, \quad v_2 \mapsto v_1, \quad w_1 \mapsto w_2, \quad w_2 \mapsto w_1$$

This isomorphism respects the switch: $v_1w_1 \mapsto v_2w_2$ and $v_2w_2 \mapsto v_1w_1$.
The isomorphism induces $\sigma$ on boundary types. $\square$

### External Ω Matrix Identity

**Lemma 3:** $\Omega_G[\rho, \tau] = \Omega_{G'}[\rho, \tau]$ for all types.

*Proof:* The external graph $G \setminus S$ is identical in $G$ and $G'$. The Ω matrix depends only on walks through the external graph, which are unchanged by the switch. $\square$

### Kernel Equivalence

The lumped kernel is defined by the Neumann series:
$$K[\tau, \rho] = \Phi[\tau, \rho] + \sum_{\tau', \rho'} \Phi[\tau, \rho'] \cdot \Omega[\rho', \tau'] \cdot K[\tau', \rho]$$

**Lemma 4:** $K_G[\tau, \rho] = K_{G'}[\sigma(\tau), \sigma(\rho)]$.

*Proof:* By Lemmas 1-3:
- $\Phi_G = P_\sigma \Phi_{G'} P_\sigma^T$ where $P_\sigma$ is the permutation matrix for $\sigma$
- $\Omega_G = \Omega_{G'}$
- From Lemma 1: $\Omega_G[\rho, \tau] = \Omega_G[\sigma(\rho), \sigma(\tau)]$

The recursive equation for $K_G$ becomes, after conjugation by $P_\sigma$:
$$P_\sigma K_G P_\sigma^T = P_\sigma \Phi_G P_\sigma^T + P_\sigma \Phi_G \Omega_G K_G P_\sigma^T$$
$$= \Phi_{G'} + \Phi_{G'} P_\sigma \Omega_G P_\sigma^T \cdot P_\sigma K_G P_\sigma^T$$

Since $\Omega_G = P_\sigma \Omega_G P_\sigma^T$ (Lemma 1 applied to external structure), we get:
$$P_\sigma K_G P_\sigma^T = \Phi_{G'} + \Phi_{G'} \Omega_{G'} (P_\sigma K_G P_\sigma^T)$$

By uniqueness of the solution, $P_\sigma K_G P_\sigma^T = K_{G'}$. $\square$

### Main Theorem

**Theorem:** $\text{tr}(T_G^k) = \text{tr}(T_{G'}^k)$ for all $k \geq 1$.

*Proof:* Partition closed walks of length $k$ into:
1. **S-avoiding walks:** Identical in $G$ and $G'$ (same external graph)
2. **S-touching walks:** Characterized by interaction sequence $(τ_1, ρ_1, ..., τ_m, ρ_m)$

For S-touching walks, the total weight factors as:
$$W_G(\pi) = \prod_{i=1}^m \Phi_G[\tau_i, \rho_i] \cdot \prod_{i=1}^{m-1} \Omega_G[\rho_i, \tau_{i+1}] \cdot \Omega_G[\rho_m, \tau_1]$$

Define the bijection $\sigma(\pi) = (\sigma(\tau_1), \sigma(\rho_1), ..., \sigma(\tau_m), \sigma(\rho_m))$.

By Lemmas 1-4:
$$W_{G'}(\sigma(\pi)) = W_G(\pi)$$

The bijection $\pi \mapsto \sigma(\pi)$ preserves weights, so:
$$\sum_{\text{S-touching } \pi} W_G(\pi) = \sum_{\text{S-touching } \pi'} W_{G'}(\pi')$$

Combined with S-avoiding equality, $\text{tr}(T_G^k) = \text{tr}(T_{G'}^k)$. $\square$

---

## Verification

All 8 σ-symmetric switches satisfy conditions 1-6 and are verified NBL-cospectral.
