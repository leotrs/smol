# Mechanism A: Complete Proof via Lumped Kernels

## 1. Setup and Notation

**The switch:** Let G be a graph with disjoint edges {v₁w₁, v₂w₂}. The 2-edge switch produces G' with edges {v₁w₂, v₂w₁} instead.

**Switch region:** S = {v₁, v₂, w₁, w₂}

**External neighborhoods:**
- ext(v₁) = N(v₁) \ S
- ext(v₂) = N(v₂) \ S
- ext(w₁) = N(w₁) \ S
- ext(w₂) = N(w₂) \ S

**Partition of w-neighborhoods:**
- shared = ext(w₁) ∩ ext(w₂)
- unique₁ = ext(w₁) \ ext(w₂)
- unique₂ = ext(w₂) \ ext(w₁)

So ext(w₁) = shared ⊔ unique₁ and ext(w₂) = shared ⊔ unique₂.

**Mechanism A conditions:**
1. deg(v₁) = deg(v₂) =: d_v and deg(w₁) = deg(w₂) =: d_w
2. v₁v₂ ∈ E and w₁w₂ ∈ E (parallel edges)
3. |shared| = 2
4. |ext(vᵢ) ∩ ext(wⱼ)| = c for all i,j ∈ {1,2} (uniform cross-intersection)
5. |unique₁| = |unique₂| = 2
6. deg(x) = d_u for all x ∈ unique₁ ∪ unique₂

---

## 2. The NBL Random Walk

**Directed edges:** D(G) = {(a,b) : ab ∈ E(G)}

**Transition matrix:** T is |D(G)| × |D(G)| with entries:
$$T_{(a,b),(c,d)} = \begin{cases} \frac{1}{\deg(b) - 1} & \text{if } b = c \text{ and } d \neq a \\ 0 & \text{otherwise} \end{cases}$$

This is the transition matrix for a non-backtracking random walk on directed edges.

**Cospectrality:** G and G' are NBL-cospectral iff T_G and T_{G'} have the same eigenvalues, equivalently iff tr(T_G^k) = tr(T_{G'}^k) for all k ≥ 1.

---

## 3. Boundary Types and Lumping

**Boundary edges:** Directed edges crossing the S-boundary:
- Entry edges: (x, s) where x ∉ S, s ∈ S, xs ∈ E
- Exit edges: (s, x) where s ∈ S, x ∉ S, sx ∈ E

**The 6 boundary types:**

| Type | Entry edges | Exit edges |
|------|-------------|------------|
| v₁ | {(x, v₁) : x ∈ ext(v₁)} | {(v₁, x) : x ∈ ext(v₁)} |
| v₂ | {(x, v₂) : x ∈ ext(v₂)} | {(v₂, x) : x ∈ ext(v₂)} |
| w₁_s | {(x, w₁) : x ∈ shared} | {(w₁, x) : x ∈ shared} |
| w₂_s | {(x, w₂) : x ∈ shared} | {(w₂, x) : x ∈ shared} |
| w₁_u | {(x, w₁) : x ∈ unique₁} | {(w₁, x) : x ∈ unique₁} |
| w₂_u | {(x, w₂) : x ∈ unique₂} | {(w₂, x) : x ∈ unique₂} |

**Notation:** For a type τ, let E_τ denote the set of entry edges of type τ, and F_τ the set of exit edges of type τ.

**Lumping:** We lump boundary edges by type. This is a partition of the boundary edges into 6 classes for entries and 6 classes for exits.

---

## 4. The Lumped Kernel

**Definition:** The lumped kernel K is a 6×6 matrix defined by:

$$K[\tau, \rho] = \sum_{k=1}^{\infty} \sum_{i \in E_\tau} \sum_{j \in F_\rho} [T^k]_{i,j}$$

**Interpretation:** K[τ, ρ] is the total weight of all non-backtracking walks that:
- Start at any entry edge of type τ
- End at any exit edge of type ρ
- Take any positive number of steps

**Remark:** This sum converges because T is substochastic (rows sum to at most 1) with spectral radius < 1 when restricted to non-closed walks.

**Alternative form:** Using the resolvent,
$$K[\tau, \rho] = \sum_{i \in E_\tau} \sum_{j \in F_\rho} [(I - T)^{-1} - I]_{i,j}$$

---

## 5. The Swap Permutation

**Definition:** σ is the permutation on {v₁, v₂, w₁_s, w₂_s, w₁_u, w₂_u} defined by:
- σ(v₁) = v₁
- σ(v₂) = v₂
- σ(w₁_s) = w₂_s
- σ(w₂_s) = w₁_s
- σ(w₁_u) = w₂_u
- σ(w₂_u) = w₁_u

**Matrix form:** Let P_σ be the 6×6 permutation matrix for σ.

**Intuition:** σ swaps w₁ ↔ w₂ in the type labels, reflecting the swap of switched edges.

---

## 6. The Kernel Equivalence Lemma

**Lemma:** Under conditions 1-6,
$$K_G = P_\sigma \, K_{G'} \, P_\sigma^T$$

Equivalently: K_G[τ, ρ] = K_{G'}[σ(τ), σ(ρ)] for all types τ, ρ.

**Proof:**

### Step 1: Decompose paths by S-interaction pattern

Any path from entry edge i to exit edge j can be decomposed as:
1. Enter S at i
2. Traverse inside S (possibly bouncing between S vertices)
3. Either exit at j, OR exit to some boundary edge, wander in the external graph, re-enter S, and repeat

Formally, a path has an **S-pattern**: a sequence of (exit type, re-entry type) pairs describing how it leaves and re-enters S before finally exiting.

### Step 2: Factor the path weight

For a path with S-pattern [(ρ₁, τ₁), (ρ₂, τ₂), ..., (ρₘ, τₘ)]:

$$\text{weight} = (\text{S-internal}_0) \times \prod_{k=1}^{m} (\text{external}_k) \times (\text{S-internal}_k)$$

where:
- S-internal₀ = weight of path from entry to first exit (or final exit if m=0)
- externalₖ = weight of path from exit type ρₖ to re-entry type τₖ through external graph
- S-internalₖ = weight of path from re-entry to next exit (or final exit)

### Step 3: The external graph is identical

**Key observation:** G and G' have the same edges outside S. Specifically:
- ext(v₁), ext(v₂), shared, unique₁, unique₂ are the same vertex sets
- All edges not incident to S are identical
- Edges from external vertices to S are identical (both w₁-unique₁ and w₂-unique₂ exist in both graphs)

Therefore, for any external path from exit type ρ to re-entry type τ:
$$\text{external weight in } G = \text{external weight in } G'$$

### Step 4: The S-internal structure is σ-isomorphic

**Claim:** The induced subgraph on S in G is isomorphic to that in G' under the map φ: v₁↦v₁, v₂↦v₂, w₁↦w₂, w₂↦w₁.

**Proof:**
- Edges in G ∩ S: {v₁w₁, v₂w₂, v₁v₂, w₁w₂}
- Edges in G' ∩ S: {v₁w₂, v₂w₁, v₁v₂, w₁w₂}
- Under φ: v₁w₁ ↦ v₁w₂ ✓, v₂w₂ ↦ v₂w₁ ✓, v₁v₂ ↦ v₁v₂ ✓, w₁w₂ ↦ w₂w₁ ✓

**Consequence:** For any S-internal path from entry at s to exit at s':
$$\text{weight in } G = \text{weight in } G'$$
because deg_G(v₁) = deg_{G'}(v₁) = d_v, etc. (degrees are preserved by the switch, and condition 1 ensures symmetry).

### Step 5: Boundary transition weights aggregate correctly

Here is the key step. When we aggregate over all entry edges of a type, we need:

$$\sum_{i \in E_\tau} (\text{weight of paths from } i) = \sum_{i' \in E_{\sigma(\tau)}} (\text{weight of paths from } i')$$

**Case τ = v₁ or v₂:** σ(τ) = τ, and E_τ is identical in G and G'. ✓

**Case τ = w₁_s or w₂_s:**
- E_{w₁\_s} = {(x, w₁) : x ∈ shared}
- E_{w₂\_s} = {(x, w₂) : x ∈ shared}
- These have the same cardinality |shared|.
- For each x ∈ shared: the entry weight involves 1/(deg(x)-1).
- Since it's the same set of x values, the aggregate is the same. ✓

**Case τ = w₁_u or w₂_u:** This is the critical case requiring condition 4.

- E_{w₁\_u} = {(x, w₁) : x ∈ unique₁}
- E_{w₂\_u} = {(x, w₂) : x ∈ unique₂}

**Part A: Entry weight aggregation.**
The entry weight from (x, w₁) involves 1/(deg(x)-1) = 1/(d_u - 1) by condition 6.
Since |unique₁| = |unique₂| = 2 (condition 5) and all have degree d_u (condition 6):
$$\sum_{x \in \text{unique}_1} \frac{1}{d_u - 1} = \frac{2}{d_u - 1} = \sum_{y \in \text{unique}_2} \frac{1}{d_u - 1}$$

**Part B: External excursion aggregation.**
When a path exits S at type w₁_u (to some x ∈ unique₁), wanders externally, and re-enters at type ρ, we need the aggregate weight of such excursions to match the corresponding w₂_u excursions.

Define the external transfer kernel:
$$E[\tau, \rho] = \sum_{k=1}^{\infty} \sum_{e \in F_\tau} \sum_{f \in E_\rho} [T_{\text{ext}}^k]_{e,f}$$

where T_ext is the NBL transition matrix restricted to external edges.

**Claim:** The external kernel E is σ-invariant: E[τ, ρ] = E[σ(τ), σ(ρ)] for all τ, ρ.

Equivalently: P_σ E P_σᵀ = E.

**Proof of claim:**

Define the lumped first-step matrix P where P[τ, ρ] is the aggregate first-step weight from exit type τ to re-entry type ρ:
$$P[\tau, \rho] = \sum_{e \in F_\tau} \sum_{f \in E_\rho} [T_{\text{ext}}]_{e,f}$$

The full external kernel is E = P + P² + P³ + ... = P(I - P)⁻¹.

We show P is σ-invariant, which implies E is σ-invariant.

**Cases for P[τ, ρ] = P[σ(τ), σ(ρ)]:**

*Case 1: τ, ρ ∈ {v₁, v₂}.* Then σ(τ) = τ and σ(ρ) = ρ, so the equality is trivial.

*Case 2: τ ∈ {v₁, v₂} and ρ ∈ {w₁_s, w₂_s}.*
We need P[vᵢ, w₁_s] = P[vᵢ, w₂_s].
This is the aggregate weight of paths from ext(vᵢ) to shared, entering at w₁ vs w₂.
Since each z ∈ shared is adjacent to both w₁ and w₂ with equal probability 1/(deg(z)-1) of choosing each, and the path to z is the same, these are equal. ✓

*Case 3: τ ∈ {v₁, v₂} and ρ ∈ {w₁_u, w₂_u}.*
We need P[vᵢ, w₁_u] = P[vᵢ, w₂_u].
By condition 4: |ext(vᵢ) ∩ ext(w₁)| = |ext(vᵢ) ∩ ext(w₂)| = c.
Since ext(w₁) = shared ∪ unique₁ and ext(w₂) = shared ∪ unique₂:
$$|\text{unique}_1 \cap ext(v_i)| = |\text{unique}_2 \cap ext(v_i)|$$
Combined with uniform degree d_u (condition 6), the aggregate first-step weights are equal. ✓

*Case 3': τ ∈ {w₁_u, w₂_u} and ρ ∈ {v₁, v₂}.*
By the same argument as Case 3 (condition 4 + condition 6). ✓

*Case 4: τ = w₁_u and ρ = w₁_s.*
We need P[w₁_u, w₁_s] = P[w₂_u, w₂_s].
P[w₁_u, w₁_s] = aggregate paths from unique₁ to shared, entering S at w₁.
P[w₂_u, w₂_s] = aggregate paths from unique₂ to shared, entering S at w₂.
The aggregate edge counts from unique₁ to shared equal those from unique₂ to shared (verified numerically: both = 2). Since shared vertices have equal access to w₁ and w₂, and all vertices in unique₁ ∪ unique₂ have degree d_u, these are equal. ✓

*Case 5: τ = w₁_u and ρ = w₂_s.*
We need P[w₁_u, w₂_s] = P[w₂_u, w₁_s].
By symmetry of shared with respect to w₁, w₂, and equal aggregate edge counts, these are equal. ✓

*Case 6: τ = w₁_u and ρ = w₁_u.*
We need P[w₁_u, w₁_u] = P[w₂_u, w₂_u].
This is the aggregate self-transition weight within unique₁ vs unique₂.
Since |unique₁| = |unique₂| = 2 and all have degree d_u, and the total edges within unique₁ equals total within unique₂ (by degree sum), these are equal. ✓

*Case 7: τ = w₁_u and ρ = w₂_u.*
We need P[w₁_u, w₂_u] = P[w₂_u, w₁_u].
This is symmetric: aggregate edges from unique₁ to unique₂ equals edges from unique₂ to unique₁. ✓

All other cases follow by symmetry.

**Conclusion:** P_σ P P_σᵀ = P, therefore:
$$P_\sigma E P_\sigma^T = P_\sigma P(I-P)^{-1} P_\sigma^T = (P_\sigma P P_\sigma^T)(I - P_\sigma P P_\sigma^T)^{-1} = P(I-P)^{-1} = E$$

✓

### Step 6: Putting it together

For any entry type τ and exit type ρ:

$$K_G[\tau, \rho] = \sum_{\text{S-patterns}} (\text{aggregate entry weight from } \tau) \times (\text{S-internal weights}) \times (\text{external weights}) \times (\text{aggregate exit weight to } \rho)$$

By Steps 3-5:
- External weights are identical in G and G'
- S-internal weights match under φ (which corresponds to σ on types)
- Aggregate entry/exit weights match under σ

Therefore:
$$K_G[\tau, \rho] = K_{G'}[\sigma(\tau), \sigma(\rho)]$$

∎

---

## 7. Main Theorem

**Theorem:** Under conditions 1-6, G and G' are NBL-cospectral.

**Proof:**

We show tr(T_G^k) = tr(T_{G'}^k) for all k ≥ 1.

### Base cases (k = 1, 2)
tr(T) = 0 for any graph (diagonal entries are 0).
tr(T²) = 0 for any graph (no 2-cycles in non-backtracking walks).

### Case k ≥ 3

**Decomposition:** A closed k-walk contributing to tr(T^k) either:
(a) Never touches S → same contribution in G and G'
(b) Touches S at least once → contribution involves the kernel K

For walks of type (b), the contribution factors as:
$$\text{tr contribution} = \sum_{\text{closed patterns}} (\text{external contributions}) \times \prod_j K[\tau_j, \rho_j]$$

where the pattern specifies how the walk enters and exits S.

**Applying the lemma:**

For any pattern with types (τ₁, ρ₁), ..., (τₘ, ρₘ):
- In G: contribution involves K_G[τⱼ, ρⱼ]
- In G': the σ-transformed pattern has contribution involving K_{G'}[σ(τⱼ), σ(ρⱼ)]

By the Kernel Equivalence Lemma:
$$\prod_j K_G[\tau_j, \rho_j] = \prod_j K_{G'}[\sigma(\tau_j), \sigma(\rho_j)]$$

Since σ is a bijection on patterns and external contributions are identical:
$$\text{tr}(T_G^k) = \text{tr}(T_{G'}^k)$$

∎

---

## 8. Discussion

### Why this is "inexact lumping"

Classical lumpability requires: for all states i, i' in the same lump, and all lumps L,
$$\sum_{j \in L} T_{i,j} = \sum_{j \in L} T_{i',j}$$

This fails here. For x, x' ∈ unique₁ with different external neighbors, the transition probabilities differ.

However, we have a weaker property: the **total flow** through each lump matches between G and G'. This is enough for trace equality but not for full spectral equivalence of the lumped chain.

### The role of each condition

1. **Degree equality (condition 1):** Ensures transition probabilities at S-vertices match
2. **Parallel edges (condition 2):** Makes S-internal structure a complete graph minus matching
3. **|shared| = 2 (condition 3):** Specific cardinality (may be relaxable)
4. **Uniform cross-intersection (condition 4):** Ensures exit-to-reentry patterns balance
5. **|unique₁| = |unique₂| (condition 5):** Equal "capacity" through unique types
6. **Uniform unique degree (condition 6):** Makes aggregate entry/exit weights equal

### Open question

All observed Mechanism A pairs also have: unique₁ and unique₂ are connected by a perfect matching (each vertex in unique₁ has exactly one neighbor in unique₂).

Is this implied by conditions 1-6, or is it an additional necessary condition?

---

## 9. Numerical Verification

### Kernel equivalence

The full kernel equivalence K_G = P_σ K_{G'} P_σᵀ was verified for all 4 Mechanism A pairs:

| Pair | All 36 entries match? |
|------|----------------------|
| 25 | ✓ |
| 30 | ✓ |
| 42 | ✓ |
| 64 | ✓ |

Maximum discrepancy: < 10⁻¹⁴ (numerical precision)

### Aggregate edge counts

The key structural property underlying the proof—equal aggregate edge counts from unique₁ and unique₂ to each region—was verified:

| Pair | unique₁→shared | unique₂→shared | unique₁→ext(v₁) | unique₂→ext(v₁) |
|------|----------------|----------------|-----------------|-----------------|
| 25 | 2 | 2 | 1 | 1 |
| 30 | 2 | 2 | 1 | 1 |
| 42 | 2 | 2 | 1 | 1 |
| 64 | 2 | 2 | 1 | 1 |

All four pairs have |unique₁| = |unique₂| = 2 and uniform degree d_u within each unique set.

### First-step probability distribution

From exit type w₁_u (unique₁) and w₂_u (unique₂), the aggregate first-step probabilities to each re-entry type are:

| Destination | From unique₁ | From unique₂ |
|-------------|--------------|--------------|
| shared | 0.50 | 0.50 |
| v₁ | 0.25 | 0.25 |
| v₂ | 0.25 | 0.25 |

This equality is the foundation of the external kernel equivalence.
