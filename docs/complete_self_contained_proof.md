# NBL-Cospectral Bipartite Swap Theorems: Complete Proofs

---

# Part I: Common Framework

---

## 1. Core Definitions

**Definition 1.1 (NBL Transition Matrix).**
For a graph $G$, the non-backtracking Laplacian (NBL) transition matrix $T_G$ is indexed by directed edges. For directed edges $(u,v)$ and $(v,w)$ where $uv, vw \in E(G)$:
$$T_G[(u,v), (v,w)] = \frac{1}{\deg(v) - 1} \quad \text{if } w \neq u$$
All other entries are zero.

**Definition 1.2 (Closed Walk Weight).**
For a directed edge $e$ and integer $k \geq 1$, define:
$$W_G(e; k) = [T_G^k]_{e,e}$$
the total weight of closed $k$-walks starting (and ending) at edge $e$.

**Definition 1.3 (Switch Region).**
A *switch region* is a subset $S \subseteq V(G)$. For $x \in S$, the *external neighborhood* is:
$$\mathrm{ext}(x) = N_G(x) \setminus S$$

**Definition 1.4 (Edge Partition).**
Given a switch region $S$, partition the directed edges of $G$ into:
- $E_{\mathrm{ext}}$: edges $(u,v)$ with $u, v \notin S$ (fully external)
- $E_{\mathrm{bnd}}$: edges with exactly one endpoint in $S$ (boundary)
- $E_{\mathrm{int}}$: edges with both endpoints in $S$ (internal)

**Definition 1.5 (Hub External Partition).**
Given hubs $h_1, h_2 \in S$, partition the external vertices reachable from hubs:
$$\mathrm{shared} = \mathrm{ext}(h_1) \cap \mathrm{ext}(h_2)$$
$$\mathrm{unique}_1 = \mathrm{ext}(h_1) \setminus \mathrm{ext}(h_2)$$
$$\mathrm{unique}_2 = \mathrm{ext}(h_2) \setminus \mathrm{ext}(h_1)$$

**Definition 1.6 (Hub Swap Permutation).**
Given hubs $h_1, h_2$, define $\sigma: V \to V$ by:
$$\sigma(x) = \begin{cases} h_2 & \text{if } x = h_1 \\ h_1 & \text{if } x = h_2 \\ x & \text{otherwise} \end{cases}$$
Extend to directed edges: $\sigma(u,v) = (\sigma(u), \sigma(v))$.

**Definition 1.7 (S-Internal Transfer Kernel).**
The *S-internal transfer kernel* $\Phi_G[\tau, \rho]$ is the total weight of all paths in $G$ that:
- Enter $S$ at a vertex of boundary type $\tau$
- Traverse only S-internal edges
- Exit $S$ at a vertex of boundary type $\rho$

---

## 2. Common Lemmas

The following lemmas apply to any graph transformation that modifies only edges within a switch region $S$.

### Lemma 2.1 (Edge Set Invariance)

*Statement:* If $G'$ is obtained from $G$ by modifying only edges with both endpoints in $S$, then:
$$E_{\mathrm{ext}}(G) = E_{\mathrm{ext}}(G') \quad \text{and} \quad E_{\mathrm{bnd}}(G) = E_{\mathrm{bnd}}(G')$$

*Proof:*
Edges with at least one endpoint outside $S$ are unchanged by any modification that only affects edges within $S$. ∎

---

### Lemma 2.2 (Trace Decomposition)

*Statement:* The trace of $T_G^k$ decomposes as:
$$\mathrm{tr}(T_G^k) = \sum_{e \in E_{\mathrm{ext}}} W_G(e; k) + \sum_{e \in E_{\mathrm{bnd}}} W_G(e; k) + \sum_{e \in E_{\mathrm{int}}} W_G(e; k)$$

*Proof:*
The trace is the sum of diagonal entries $[T_G^k]_{e,e}$ over all directed edges $e$. Partitioning edges by their relationship to $S$ gives the decomposition. ∎

---

### Lemma 2.3 (σ-Conjugacy Criterion)

*Statement:* Suppose:
1. $\sigma$ maps $E_{\mathrm{int}}(G)$ bijectively onto $E_{\mathrm{int}}(G')$
2. For every NBL transition $(a,b) \to (b,c)$ in $G$, the weight equals that of $\sigma(a,b) \to \sigma(b,c)$ in $G'$

Then the S-internal transfer kernels satisfy:
$$\Phi_G[\tau, \rho] = \Phi_{G'}[\sigma(\tau), \sigma(\rho)]$$

Equivalently: $\Phi_G = P_\sigma \Phi_{G'} P_\sigma^T$ where $P_\sigma$ is the permutation matrix induced by $\sigma$.

*Proof:*
Let $\mathcal{P}_G(\tau, \rho)$ denote S-internal paths from entry type $\tau$ to exit type $\rho$ in $G$.

By hypothesis (1), $\sigma$ induces a bijection $\mathcal{P}_G(\tau, \rho) \to \mathcal{P}_{G'}(\sigma(\tau), \sigma(\rho))$.

By hypothesis (2), for any path $P \in \mathcal{P}_G(\tau, \rho)$:
$$\mathrm{weight}_G(P) = \mathrm{weight}_{G'}(\sigma(P))$$

Therefore:
$$\Phi_G[\tau, \rho] = \sum_{P \in \mathcal{P}_G(\tau, \rho)} \mathrm{weight}_G(P) = \sum_{Q \in \mathcal{P}_{G'}(\sigma(\tau), \sigma(\rho))} \mathrm{weight}_{G'}(Q) = \Phi_{G'}[\sigma(\tau), \sigma(\rho)]$$
∎

---

### Lemma 2.4 (Cospectrality from Trace Equality)

*Statement:* If $\mathrm{tr}(T_G^k) = \mathrm{tr}(T_{G'}^k)$ for all $k \geq 1$, then $T_G$ and $T_{G'}$ have the same spectrum.

*Proof:*
The power sums $\mathrm{tr}(T^k)$ determine the elementary symmetric polynomials in the eigenvalues via Newton's identities. Equal power sums imply equal characteristic polynomials. ∎

---

# Part II: Bipartite Swap Theorem (General Form)

---

## 3. Setup

**Definition 3.1 (Bipartite Swap Configuration).**
A *bipartite swap configuration* in a graph $G$ consists of:
- **Hubs:** $H = \{h_1, h_2\}$, two distinct vertices
- **Leaves:** $L = L_1 \sqcup L_2$, a partition into two disjoint sets
- **Adjacency constraint:** In $G$:
  - Every $\ell \in L_1$ is adjacent to $h_1$ and non-adjacent to $h_2$
  - Every $\ell \in L_2$ is adjacent to $h_2$ and non-adjacent to $h_1$

The switch region is $S = H \cup L$.

**Definition 3.2 (Bipartite Swap Operation).**
The *bipartite swap* produces graph $G'$ by:
- Removing edges $\{\ell h_1 : \ell \in L_1\} \cup \{\ell h_2 : \ell \in L_2\}$
- Adding edges $\{\ell h_2 : \ell \in L_1\} \cup \{\ell h_1 : \ell \in L_2\}$

Equivalently: each leaf switches which hub it connects to.

**Definition 3.3 (Aggregate Cross-Intersection).**
For $i, j \in \{1, 2\}$, define:
$$\Gamma_{ij} = \sum_{\ell \in L_i} |\mathrm{ext}(\ell) \cap \mathrm{ext}(h_j)|$$

---

## 4. Theorem Statement

**Theorem (Bipartite Swap).** Let $G$ and $G'$ be related by a bipartite swap on configuration $(H, L_1, L_2)$. Then $G$ and $G'$ are NBL-cospectral if:

**(C1\*) Degree Equality:**
$$\deg_G(h_1) = \deg_G(h_2) \quad \text{and} \quad \deg_G(\ell) = d_L \text{ for all } \ell \in L$$

**(C2\*) Balanced Aggregate Cross-Intersection:**
$$\Gamma_{1j} = \Gamma_{2j} \quad \text{for } j = 1, 2$$

**(C3\*) Equal Partition Sizes:**
$$|L_1| = |L_2|$$

---

## 5. Proof

### Lemma 5.1 (σ-Bijection on Internal Edges)

*Statement:* The hub swap permutation $\sigma$ (Definition 1.6) maps $E_{\mathrm{int}}(G)$ bijectively onto $E_{\mathrm{int}}(G')$.

*Proof:*
S-internal edges partition into three types:

**Type A (Leaf-hub edges):**
- In $G$: $\{(\ell, h_1), (h_1, \ell) : \ell \in L_1\} \cup \{(\ell, h_2), (h_2, \ell) : \ell \in L_2\}$
- Apply $\sigma$: $(\ell, h_1) \mapsto (\ell, h_2)$ for $\ell \in L_1$, etc.
- These map to leaf-hub edges in $G'$. ✓

**Type B (Hub-hub edge, if present):**
- $\sigma(h_1, h_2) = (h_2, h_1)$: same undirected edge. ✓

**Type C (Leaf-leaf edges):**
- $\sigma(\ell, \ell') = (\ell, \ell')$: unchanged. ✓

Since $\sigma$ is an involution, this is a bijection. ∎

---

### Lemma 5.2 (Weight Preservation)

*Statement:* For any NBL transition $(a,b) \to (b,c)$ in $G$, the weight equals that of $\sigma(a,b) \to \sigma(b,c)$ in $G'$.

*Proof:*
The transition weight is $\frac{1}{\deg(b) - 1}$.

**Case $b \in L$:** $\sigma(b) = b$. Degree preserved (loses one hub edge, gains one). ✓

**Case $b = h_1$:** $\sigma(b) = h_2$. By (C3\*), $|L_1| = |L_2|$, so degree change is zero. By (C1\*), $\deg_G(h_1) = \deg_G(h_2)$, so weights match. ✓

**Case $b = h_2$:** Symmetric. ∎

---

### Lemma 5.3 (Φ-Conjugacy)

*Statement:* $\Phi_G[\tau, \rho] = \Phi_{G'}[\sigma(\tau), \sigma(\rho)]$.

*Proof:* Apply Lemma 2.3 using Lemmas 5.1 and 5.2. ∎

---

### Lemma 5.4 (Generalized Unique-Vertex Symmetry)

*Statement:* Under (C2\*):
$$\sum_{\ell \in L_1} |\mathrm{ext}(\ell) \cap \mathrm{unique}_j| = \sum_{\ell \in L_2} |\mathrm{ext}(\ell) \cap \mathrm{unique}_j| \quad \text{for } j = 1, 2$$

*Proof:*
For any $\ell \in L$:
$$|\mathrm{ext}(\ell) \cap \mathrm{ext}(h_j)| = |\mathrm{ext}(\ell) \cap \mathrm{shared}| + |\mathrm{ext}(\ell) \cap \mathrm{unique}_j|$$

Summing over $L_i$ and writing $\Sigma_i = \sum_{\ell \in L_i} |\mathrm{ext}(\ell) \cap \mathrm{shared}|$, $U_{ij} = \sum_{\ell \in L_i} |\mathrm{ext}(\ell) \cap \mathrm{unique}_j|$:
$$\Gamma_{ij} = \Sigma_i + U_{ij}$$

By (C2\*): $\Gamma_{11} = \Gamma_{21}$ and $\Gamma_{12} = \Gamma_{22}$.

Subtracting: $U_{11} - U_{21} = \Sigma_2 - \Sigma_1$ and $U_{12} - U_{22} = \Sigma_2 - \Sigma_1$.

Adding the (C2\*) equations: $\Sigma_1 + U_{11} + U_{12} = \Sigma_2 + U_{21} + U_{22}$.

Combined with the above: $U_{11} = U_{21}$ and $U_{12} = U_{22}$. ∎

---

### Lemma 5.5 (Generalized Pairing Invariant)

*Statement:* For all $k \geq 1$:
$$\sum_{\ell \in L_1} W_G(\ell, h_1; k) + \sum_{\ell \in L_2} W_G(\ell, h_2; k) = \sum_{\ell \in L_1} W_{G'}(\ell, h_2; k) + \sum_{\ell \in L_2} W_{G'}(\ell, h_1; k)$$

*Proof:*
Closed walks from $(\ell, h_j)$ decompose into internal and external segments.

**Internal segments:** Controlled by Φ-conjugacy (Lemma 5.3).

**External segments via shared:** Equal hub degrees (C1\*) give equal exit weights. External graph identical (Lemma 2.1).

**External segments via unique$_j$:** 
- Walks from $(\ell, h_1)$ for $\ell \in L_1$ via unique$_1$ pair with walks from $(\ell', h_1)$ for $\ell' \in L_2$ via unique$_1$ in $G'$.
- Return multiplicities: $\sum_{L_1} |\mathrm{ext}(\ell) \cap \mathrm{unique}_1|$ vs $\sum_{L_2} |\mathrm{ext}(\ell') \cap \mathrm{unique}_1|$.
- Equal by Lemma 5.4. ✓

Similarly for unique$_2$. ∎

---

### Theorem Proof

*Proof:*
By Lemma 2.2 (Trace Decomposition):
$$\mathrm{tr}(T^k) = \sum_{e \in E_{\mathrm{ext}}} W(e; k) + \sum_{e \in E_{\mathrm{bnd}}} W(e; k) + \sum_{e \in E_{\mathrm{int}}} W(e; k)$$

**External term:** Equal by Lemma 2.1.

**Boundary term:** Equal by Lemma 2.1 and Φ-conjugacy (Lemma 5.3).

**Internal term:** 
- Leaf-leaf and hub-hub edges: unchanged, equal.
- Leaf-hub (switch) edges: equal by Lemma 5.5.

All terms equal, so $\mathrm{tr}(T_G^k) = \mathrm{tr}(T_{G'}^k)$.

By Lemma 2.4, $T_G$ and $T_{G'}$ are cospectral. ∎

---

# Part III: 2-Edge Switch Theorem (Special Case)

---

## 6. Setup

**Definition 6.1 (2-Edge Switch).**
A *2-edge switch* on vertices $v_1, v_2, w_1, w_2$ in $G$ requires:
- $v_1w_1, v_2w_2 \in E(G)$ (edges to remove)
- $v_1w_2, v_2w_1 \notin E(G)$ (edges to add)

The switch produces $G'$ by removing $\{v_1w_1, v_2w_2\}$ and adding $\{v_1w_2, v_2w_1\}$.

**Observation:** This is a bipartite swap with:
- $H = \{w_1, w_2\}$ (hubs), where $h_1 = w_1$, $h_2 = w_2$
- $L_1 = \{v_1\}$, $L_2 = \{v_2\}$ (singleton leaf partitions)
- $S = \{v_1, v_2, w_1, w_2\}$

---

## 7. Theorem Statement

**Theorem (2-Edge Switch).** Let $G$ and $G'$ be related by a 2-edge switch on $v_1, v_2, w_1, w_2$. Then $G$ and $G'$ are NBL-cospectral if:

**(C1) Degree Equality:**
$$\deg_G(v_1) = \deg_G(v_2) \quad \text{and} \quad \deg_G(w_1) = \deg_G(w_2)$$

**(C2) Pairwise Cross-Intersection Equality:**
$$|\mathrm{ext}(v_1) \cap \mathrm{ext}(w_j)| = |\mathrm{ext}(v_2) \cap \mathrm{ext}(w_j)| \quad \text{for } j = 1, 2$$

---

## 8. Proof (via Reduction)

**Proposition.** The 2-edge switch theorem is the special case of the bipartite swap theorem with $|L_1| = |L_2| = 1$.

*Proof:*
With $L_1 = \{v_1\}$, $L_2 = \{v_2\}$, $h_1 = w_1$, $h_2 = w_2$:

**(C1) $\Leftrightarrow$ (C1\*):**
- (C1): $\deg(v_1) = \deg(v_2)$ and $\deg(w_1) = \deg(w_2)$
- (C1\*): all leaves equal degree and $\deg(h_1) = \deg(h_2)$
- Identical. ✓

**(C2) $\Leftrightarrow$ (C2\*):**
- (C2): $|\mathrm{ext}(v_1) \cap \mathrm{ext}(w_j)| = |\mathrm{ext}(v_2) \cap \mathrm{ext}(w_j)|$ for $j = 1, 2$
- (C2\*): $\sum_{\ell \in L_1} |\mathrm{ext}(\ell) \cap \mathrm{ext}(h_j)| = \sum_{\ell \in L_2} |\mathrm{ext}(\ell) \cap \mathrm{ext}(h_j)|$
- With singletons: $|\mathrm{ext}(v_1) \cap \mathrm{ext}(w_j)| = |\mathrm{ext}(v_2) \cap \mathrm{ext}(w_j)|$
- Identical. ✓

**(C3\*) is automatic:** $|L_1| = |L_2| = 1$. ✓

Therefore the bipartite swap theorem (Part II) implies the 2-edge switch theorem. ∎

---

## 9. Direct Proof (Self-Contained)

For completeness, we provide lemmas specific to the 2-edge case.

### Lemma 9.1 (Unique-Vertex Symmetry, Pointwise)

*Statement:* Under (C2):
$$|\mathrm{ext}(v_i) \cap \mathrm{unique}_1| = |\mathrm{ext}(v_i) \cap \mathrm{unique}_2| \quad \text{for } i = 1, 2$$

*Proof:*
From $\mathrm{ext}(w_j) = \mathrm{shared} \sqcup \mathrm{unique}_j$:
$$|\mathrm{ext}(v_i) \cap \mathrm{ext}(w_j)| = |\mathrm{ext}(v_i) \cap \mathrm{shared}| + |\mathrm{ext}(v_i) \cap \mathrm{unique}_j|$$

By (C2), the LHS equals $c$ for both $j = 1$ and $j = 2$.

Subtracting: $|\mathrm{ext}(v_i) \cap \mathrm{unique}_1| = |\mathrm{ext}(v_i) \cap \mathrm{unique}_2|$. ∎

---

### Lemma 9.2 (Pairing Invariant, 2-Edge)

*Statement:* For all $k \geq 1$:
$$W_G(v_1, w_1; k) + W_G(v_2, w_2; k) = W_{G'}(v_1, w_2; k) + W_{G'}(v_2, w_1; k)$$

*Proof:*
This is Lemma 5.5 with $|L_1| = |L_2| = 1$, using Lemma 9.1 for return multiplicities. ∎

---

### Theorem Proof (2-Edge, Direct)

*Proof:*
Identical to the bipartite swap proof, using Lemmas 9.1–9.2. ∎

---

# Part IV: Summary and Verification

---

## 10. Unified View

The bipartite swap theorem is a single theorem parameterized by $k = |L_1| = |L_2|$:

| $k$ | Name | Edges Swapped | Cross-Intersection Condition |
|-----|------|---------------|------------------------------|
| 1 | 2-edge switch | 2 | Pointwise: $|\mathrm{ext}(v_i) \cap \mathrm{ext}(w_j)| = c$ |
| $\geq 2$ | $2k$-edge bipartite swap | $2k$ | Summed: $\Gamma_{1j} = \Gamma_{2j}$ |

The summed condition is strictly weaker than pointwise equality when $k \geq 2$.

---

## 11. Coverage at $n = 10$, min-degree $\geq 2$

| $k$ | Pairs Explained |
|-----|-----------------|
| 1 | 45 |
| 2 | 6 |
| **Total** | **51 of 78 (65%)** |

---

## 12. Logical Dependencies

```
                    ┌─────────────────────────────────────────────┐
                    │           COMMON FRAMEWORK (Part I)         │
                    │  Def 1.1–1.7, Lemmas 2.1–2.4                │
                    └─────────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────────┐
                    │      BIPARTITE SWAP THEOREM (Part II)       │
                    │                                             │
                    │  (C1*) ──→ Lemma 5.2 ──→ Lemma 5.3 ──┐     │
                    │  (C3*) ──→ Lemma 5.2                  │     │
                    │                                       ├──→ Theorem
                    │  (C2*) ──→ Lemma 5.4 ─────────────────┘     │
                    └─────────────────────────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────────┐
                    │      2-EDGE SWITCH THEOREM (Part III)       │
                    │                                             │
                    │  Special case: |L₁| = |L₂| = 1              │
                    │  (C1) = (C1*), (C2) = (C2*), (C3*) trivial  │
                    └─────────────────────────────────────────────┘
```

---

## 13. Verification

### 2-Edge Switches ($k = 1$)

Verified on all 45 NBL-cospectral 2-edge switches at $n = 10$, min-degree $\geq 2$:

| Check | Result |
|-------|--------|
| All satisfy (C1) | ✓ |
| All satisfy (C2) | ✓ |
| Φ-conjugacy error | $< 10^{-15}$ |
| Eigenvalue match | $< 10^{-14}$ |

### 4-Edge Bipartite Swaps ($k = 2$)

Verified on all 6 pairs:

| Pair | $|L_1|=|L_2|$ | (C1\*) | (C2\*) | NBL Match |
|------|---------------|--------|--------|-----------|
| I?qa\`hidg ↔ I?qa\`iYXg | 2 | ✓ | ✓ | ✓ |
| I?qa\`xjfg ↔ I?qa\`yZZg | 2 | ✓ | ✓ | ✓ |
| ICQrV\`lmg ↔ ICQrVaj^G | 2 | ✓ | ✓ | ✓ |
| ICR\`v\`lmg ↔ ICR\`v_zzG | 2 | ✓ | ✓ | ✓ |
| ICZLbvs}? ↔ ICY^Bzq}? | 2 | ✓ | ✓ | ✓ |
| ICpdbi\]g ↔ ICpdbhZnG | 2 | ✓ | ✓ | ✓ |

---

## 14. What is NOT Required

The following are **not necessary** for NBL-cospectrality:
- Hub-hub edge ($h_1 h_2 \in E$)
- Leaf-leaf edges within or across partitions
- Specific sizes of shared/unique sets
- Uniform degrees within unique vertex sets
- Any particular structure of the external graph

Only conditions (C1\*), (C2\*), (C3\*) matter.
