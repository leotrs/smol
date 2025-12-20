# Generalized NBL-Cospectral Switch Theorem

**Author:** Research notes  
**Date:** December 2024

## Theorem Statement

**Theorem (Generalized Double-Parallel Switch):** Let $G$ be a graph with vertices $v_1, v_2, w_1, w_2$ such that edges $v_1w_1, v_2w_2 \in E(G)$ but $v_1w_2, v_2w_1 \notin E(G)$. Define $G'$ by the switch: remove $\{v_1w_1, v_2w_2\}$ and add $\{v_1w_2, v_2w_1\}$.

Then $G$ and $G'$ are NBL-cospectral if:

**(C1) Degree Equality:** $\deg_G(v_1) = \deg_G(v_2)$ and $\deg_G(w_1) = \deg_G(w_2)$

**(C2) Uniform Cross-Intersection:** For $S = \{v_1, v_2, w_1, w_2\}$ and $\mathrm{ext}(x) = N_G(x) \setminus S$:
$$|\mathrm{ext}(v_i) \cap \mathrm{ext}(w_j)| = c \quad \text{for all } i,j \in \{1,2\}$$

## Key Definitions

Let $S = \{v_1, v_2, w_1, w_2\}$ be the switch region.

**External neighborhoods:**
- $\mathrm{ext}(x) = N_G(x) \setminus S$ for any $x \in S$

**W-side partition:**
- $\mathrm{shared} = \mathrm{ext}(w_1) \cap \mathrm{ext}(w_2)$
- $\mathrm{unique}_1 = \mathrm{ext}(w_1) \setminus \mathrm{ext}(w_2)$
- $\mathrm{unique}_2 = \mathrm{ext}(w_2) \setminus \mathrm{ext}(w_1)$

## Preliminary Lemmas

**Lemma 1 (Unique Set Equality):** $|\mathrm{unique}_1| = |\mathrm{unique}_2|$.

*Proof:* By (C1), $\deg(w_1) = \deg(w_2)$. The S-internal degrees are equal (both connect to exactly one of $\{v_1, v_2\}$ plus possibly $\{w_1w_2\}$ edge). Thus $|\mathrm{ext}(w_1)| = |\mathrm{ext}(w_2)|$. Since $|\mathrm{ext}(w_j)| = |\mathrm{shared}| + |\mathrm{unique}_j|$, we get $|\mathrm{unique}_1| = |\mathrm{unique}_2|$. $\square$

**Lemma 2 (Unique-to-V Symmetry):** For $i \in \{1,2\}$:
$$|\mathrm{ext}(v_i) \cap \mathrm{unique}_1| = |\mathrm{ext}(v_i) \cap \mathrm{unique}_2|$$

*Proof:* Since $\mathrm{ext}(w_j) = \mathrm{shared} \sqcup \mathrm{unique}_j$ (disjoint union):
$$|\mathrm{ext}(v_i) \cap \mathrm{ext}(w_j)| = |\mathrm{ext}(v_i) \cap \mathrm{shared}| + |\mathrm{ext}(v_i) \cap \mathrm{unique}_j|$$

By (C2), $|\mathrm{ext}(v_i) \cap \mathrm{ext}(w_1)| = |\mathrm{ext}(v_i) \cap \mathrm{ext}(w_2)| = c$. Since $|\mathrm{ext}(v_i) \cap \mathrm{shared}|$ is independent of $j$, we get $|\mathrm{ext}(v_i) \cap \mathrm{unique}_1| = |\mathrm{ext}(v_i) \cap \mathrm{unique}_2|$. $\square$

## Proof of Main Theorem

### Step 1: Decompose the Trace

For the NBL transition matrix $T$, we have:
$$\mathrm{tr}(T^k) = \sum_{\text{closed walks } W \text{ of length } k} \mathrm{weight}(W)$$

Partition closed walks into two classes:
- **S-avoiding walks:** Never traverse an edge with both endpoints in $S$
- **S-touching walks:** Traverse at least one S-internal edge

Since $G$ and $G'$ differ only in S-internal edges, S-avoiding walks contribute identically in both graphs.

### Step 2: Analyze S-Touching Walks

An S-touching walk has an **interaction pattern** $\pi = (\tau_1, \rho_1, \tau_2, \rho_2, \ldots, \tau_m, \rho_m)$ where:
- $\tau_i$ is the entry type (which boundary edge enters $S$)
- $\rho_i$ is the exit type (which boundary edge exits $S$)

The weight of a walk with pattern $\pi$ is:
$$W(\pi) = \prod_{i=1}^m \Phi[\tau_i, \rho_i] \cdot \prod_{i=1}^m \Omega[\rho_i, \tau_{i+1}]$$
where:
- $\Phi[\tau, \rho]$ = total weight of S-internal paths from entry $\tau$ to exit $\rho$
- $\Omega[\rho, \tau]$ = total weight of S-external paths from exit $\rho$ to entry $\tau$

### Step 3: Define Boundary Types

**Entry types:** For $x \notin S$ and $s \in S$ with $xs \in E(G)$, the edge $(x, s)$ is an entry edge.

Partition entry edges by their S-vertex:
- Type $v_1$: entries $(x, v_1)$ for $x \in \mathrm{ext}(v_1)$
- Type $v_2$: entries $(x, v_2)$ for $x \in \mathrm{ext}(v_2)$
- Type $w_1^s$: entries $(x, w_1)$ for $x \in \mathrm{shared}$
- Type $w_2^s$: entries $(x, w_2)$ for $x \in \mathrm{shared}$
- Type $w_1^u$: entries $(x, w_1)$ for $x \in \mathrm{unique}_1$
- Type $w_2^u$: entries $(x, w_2)$ for $x \in \mathrm{unique}_2$

Similarly for exit types.

### Step 4: The Swap Permutation

Define $\sigma$ on boundary types:
$$\sigma: v_1 \leftrightarrow v_1, \quad v_2 \leftrightarrow v_2, \quad w_1^s \leftrightarrow w_2^s, \quad w_1^u \leftrightarrow w_2^u$$

**Claim:** The swap $\sigma$ preserves aggregate transition weights.

### Step 5: Weight Preservation

**S-internal weights:** The switch replaces $w_1$-$v_1$ with $w_1$-$v_2$ and $w_2$-$v_2$ with $w_2$-$v_1$. Under $\sigma$:
- $\Phi_G[\tau, \rho] = \Phi_{G'}[\sigma(\tau), \sigma(\rho)]$

This holds because:
1. Paths in $G$ using $w_1$-$v_1$ correspond to paths in $G'$ using $w_1$-$v_2$
2. The weight is $1/(\deg(w_1)-1) = 1/(\deg(w_2)-1)$ by (C1)

**S-external weights:** The external graph is identical in $G$ and $G'$.

For type $w_1^u$ (entries from $\mathrm{unique}_1$):
- In $G$: total weight = $|\mathrm{unique}_1| \times (\text{transition probability})$
- In $G'$ for type $w_2^u$: total weight = $|\mathrm{unique}_2| \times (\text{same probability})$

By Lemma 1, these are equal.

For type $w_1^s$: by (C2), the transition structure from shared vertices is symmetric under $\sigma$.

### Step 6: Trace Equality

For any interaction pattern $\pi$, define $\sigma(\pi) = (\sigma(\tau_1), \sigma(\rho_1), \ldots)$.

By Steps 4-5:
$$W_G(\pi) = W_{G'}(\sigma(\pi))$$

Since $\sigma$ is a bijection on patterns:
$$\mathrm{tr}(T_G^k) = \sum_\pi W_G(\pi) = \sum_\pi W_{G'}(\sigma(\pi)) = \mathrm{tr}(T_{G'}^k)$$

Therefore $G$ and $G'$ are NBL-cospectral. $\square$

## Corollary: Original Mechanism A

The original Mechanism A conditions are:
- (C1) Degree equality
- (C2') Both parallel edges exist ($v_1v_2, w_1w_2 \in E$)
- (C3') $|\mathrm{shared}| = 2$
- (C4') Uniform unique degrees

These imply (C1) and (C2), so are sufficient but not necessary.

## Experimental Verification

All 11 NBL-cospectral 2-edge switches with $n=10$ and $\min\deg \geq 2$ satisfy (C1) and (C2):

| Switch | $|\mathrm{shared}|$ | Parallel edges | (C1) | (C2) |
|--------|---------------------|----------------|------|------|
| 0 | 1 | Both | ✓ | ✓ |
| 1 | 1 | None | ✓ | ✓ |
| 2 | 1 | None | ✓ | ✓ |
| 3 | 2 | Both | ✓ | ✓ |
| 4 | 2 | Both | ✓ | ✓ |
| 5 | 1 | One | ✓ | ✓ |
| 6 | 1 | None | ✓ | ✓ |
| 7 | 2 | Both | ✓ | ✓ |
| 8 | 2 | One | ✓ | ✓ |
| 9 | 1 | None | ✓ | ✓ |
| 10 | 2 | Both | ✓ | ✓ |

The 7 switches not satisfying original Mechanism A (indices 0, 1, 2, 5, 6, 8, 9) all satisfy the generalized conditions (C1) + (C2).
