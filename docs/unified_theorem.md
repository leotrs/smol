# Unified Theorem: NBL-Cospectrality of 2-Edge Switches

## Main Result

**Theorem (Unified NBL-Cospectrality for 2-Edge Switches):**

Let $G$ be a graph and consider the 2-edge switch
$$\{v_1w_1, v_2w_2\} \to \{v_1w_2, v_2w_1\}$$
producing graph $G'$. Define:
- $S = \{v_1, v_2, w_1, w_2\}$ (switch region)
- $\text{shared} = N(w_1) \cap N(w_2) \setminus S$
- $\text{unique}_j = N(w_j) \setminus N(w_{3-j}) \setminus S$ for $j = 1,2$

If the following conditions hold:

1. **Degree equality:** $\deg(v_1) = \deg(v_2)$ and $\deg(w_1) = \deg(w_2)$

2. **Uniform cross-intersection:** $|N(v_i) \cap N(w_j) \setminus S| = c$ for all $i,j \in \{1,2\}$

3. **Equal unique sizes:** $|\text{unique}_1| = |\text{unique}_2|$

4. **Partial σ-symmetry:** The first-step external matrix $P$ is symmetric under at least one of:
   - (a) $v_1 \leftrightarrow v_2$ with $u_1, u_2, \text{shared}$ fixed, OR
   - (b) $u_1 \leftrightarrow u_2$ with $v_1, v_2, \text{shared}$ fixed

Then $G$ and $G'$ are NBL-cospectral.

---

## Classification of Mechanisms

| Symmetry Type | Name | Count | Description |
|--------------|------|-------|-------------|
| Both (a) and (b) | Mechanism A | 8 | Full σ-symmetry |
| Only (b) | Mechanism B (type a) | 2 | u1↔u2 only |
| Only (a) | Mechanism B (type b) | 1 | v1↔v2 only |

---

## Conditions Sufficient for Partial Symmetry

### Sufficient for v1↔v2 symmetry:
- $v_1$ and $v_2$ have isomorphic external connectivity
- Edges from shared/unique to $v_1$ match those to $v_2$

### Sufficient for u1↔u2 symmetry:
- Degree multisets: $\{\deg(x) : x \in \text{unique}_1\} = \{\deg(x) : x \in \text{unique}_2\}$
- Edge counts: $|E(\text{unique}_1)| = |E(\text{unique}_2)|$
- Shared connectivity: $|E(\text{unique}_1, \text{shared})| = |E(\text{unique}_2, \text{shared})|$

---

## Proof Outline

1. **Partition closed walks:** S-avoiding (identical in G and G') and S-touching

2. **For S-touching walks:** Characterize by boundary interaction sequence $(τ_1, ρ_1, \ldots, τ_m, ρ_m)$

3. **Weight factorization:**
   $$W_G(\text{walk}) = \prod_{i} \Phi_G[\tau_i, \rho_i] \cdot \prod_i \Omega[\rho_i, \tau_{i+1}]$$

4. **Symmetry argument:**
   - Under partial symmetry (a): walks through $v_1$ map to walks through $v_2$ with equal weight
   - Under partial symmetry (b): walks through $u_1$ map to walks through $u_2$ with equal weight

5. **Trace equality:** The bijection on walk patterns preserves total weight, so $\text{tr}(T_G^k) = \text{tr}(T_{G'}^k)$

---

## Verified Examples

All 11 NBL-cospectral 2-edge switches from the n=10 dataset satisfy the theorem:

| Graph6 | v1↔v2 | u1↔u2 | Both | Mechanism |
|--------|-------|-------|------|-----------|
| I?qadhik_ | ✓ | ✓ | ✓ | A |
| ICQbeZqz? | ✗ | ✓ | ✗ | B(a) |
| ICQfAxuv? | ✗ | ✓ | ✗ | B(a) |
| ICQubQxZ_ | ✓ | ✓ | ✓ | A |
| ICQubQxZg | ✓ | ✓ | ✓ | A |
| ICR`ujgMo | ✓ | ✓ | ✓ | A |
| ICR`vGy}? | ✓ | ✓ | ✓ | A |
| ICXmdritW | ✓ | ✓ | ✓ | A |
| ICXmeqsWw | ✓ | ✗ | ✗ | B(b) |
| ICZLfa{Xw | ✓ | ✓ | ✓ | A |
| ICpfdrdVo | ✓ | ✓ | ✓ | A |

---

## Original Mechanism A Conditions (Relaxed)

The original Mechanism A had 6 conditions:
1. Degree equality ✓ (kept)
2. Both parallel edges exist ✗ (NOT necessary)
3. |shared| = 2 ✗ (NOT necessary, relaxed to ≥1)
4. Uniform cross-intersection ✓ (kept)
5. |unique| = 2 each ✓ (kept)
6. Uniform unique degrees ✗ (NOT necessary)

**Key finding:** Conditions 2, 3, 6 are sufficient but not necessary. The true requirement is partial σ-symmetry of the first-step matrix P.
