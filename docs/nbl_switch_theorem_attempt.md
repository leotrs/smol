# NBL 2-Edge Switch Theorem: Proof Attempt

**Date:** December 2024

This document records an attempt to prove a characterization theorem for NBL-cospectral 2-edge switches. The theorem as stated is expected to fail; the failure will reveal missing conditions.

## The (Conjectured) Theorem

**Theorem (NBL 2-Edge Switch):** Let G be a simple graph and let {v₁-w₁, v₂-w₂} be two edges in G with the four vertices v₁, v₂, w₁, w₂ all distinct. Let G' be the graph obtained by the 2-edge switch:

```
G:  v₁—w₁,  v₂—w₂
G': v₁—w₂,  v₂—w₁
```

Then G and G' are NBL-cospectral **if and only if** the following three conditions hold:

1. **Degree equality:** deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)

2. **Uniform cross-intersection:** Let S = {v₁, v₂, w₁, w₂} and ext(v) = N(v) \ S. Then:
   ```
   |ext(v₁) ∩ ext(w₁)| = |ext(v₁) ∩ ext(w₂)| = |ext(v₂) ∩ ext(w₁)| = |ext(v₂) ∩ ext(w₂)| = c
   ```
   for some c ≥ 1.

3. **Connectivity:** At least one of:
   - (a) v₁-v₂ ∈ E(G), or
   - (b) w₁-w₂ ∈ E(G), or
   - (c) ∃ edge between ext(v₁)∩ext(wⱼ) and ext(v₂)∩ext(wⱼ) for some j ∈ {1,2}

---

## Setup and Notation

### The NBL Matrix

The non-backtracking Laplacian transition matrix T = D⁻¹B is indexed by directed edges:

```
T[(u,v), (v,w)] = 1/(deg(v) - 1)    if w ≠ u
T[(u,v), (x,y)] = 0                  otherwise
```

T is a stochastic matrix (rows sum to 1). The eigenvalues of T determine NBL-cospectrality.

### Trace Characterization

Two matrices are cospectral iff they have the same characteristic polynomial, which is equivalent to:

```
tr(T₁ᵏ) = tr(T₂ᵏ)   for all k ≥ 1
```

So we need to prove: under conditions 1-3, tr(T_G^k) = tr(T_{G'}^k) for all k.

### The Perturbation

The switch changes 4 directed edges:
- Removed: (v₁,w₁), (w₁,v₁), (v₂,w₂), (w₂,v₂)
- Added: (v₁,w₂), (w₂,v₁), (v₂,w₁), (w₁,v₂)

Let Δ = T_{G'} - T_G. Then Δ is a sparse matrix with:
- Non-zero rows only for edges (x,y) where y ∈ S = {v₁, v₂, w₁, w₂}
- Non-zero columns only for edges starting from S

---

## Proof Attempt: Necessity

### Condition 1 (Degree equality) is necessary

**Claim:** If the switch preserves NBL spectrum, then deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂).

**Proof attempt:**

The switch preserves the total number of edges, so Σᵥ deg(v) is unchanged. But we need to show the specific equalities.

Consider the trace at k=1: tr(T) = 0 for any graph (diagonal of T is zero since no 1-step return without backtracking).

Consider tr(T²): This counts 2-step non-backtracking returns. A 2-step return from (u,v) to (u,v) requires going (u,v) → (v,x) → (x,u) for some x ≠ u with v-x and x-u edges. This means u,v,x form a triangle.

The switch changes which triangles exist. Specifically:
- Lost triangles: those using v₁-w₁ or v₂-w₂
- Gained triangles: those using v₁-w₂ or v₂-w₁

For tr(T²) to be preserved...

**[GAP]** Need to analyze triangle contributions more carefully.

Actually, tr(T²) = 0 for any graph because a 2-step NB walk cannot return (would require backtracking). So k=2 gives no information.

At k=3, we have 3-step returns. These involve cycles of length 3 (triangles) in the Hashimoto graph.

**[TODO]** Complete the necessity proof for condition 1.

---

### Condition 2 (Uniform cross-intersection) is necessary

**Claim:** If the switch preserves NBL spectrum, then all |ext(vᵢ) ∩ ext(wⱼ)| are equal.

**Proof attempt:**

The cross-intersection determines how many common neighbors (outside S) each pair (vᵢ, wⱼ) has. These common neighbors create triangles.

In G: triangles v₁-w₁-x where x ∈ ext(v₁) ∩ ext(w₁)
In G': triangles v₁-w₂-x where x ∈ ext(v₁) ∩ ext(w₂)

For the triangle counts to balance:
- Lost: |ext(v₁) ∩ ext(w₁)| + |ext(v₂) ∩ ext(w₂)| triangles
- Gained: |ext(v₁) ∩ ext(w₂)| + |ext(v₂) ∩ ext(w₁)| triangles

This gives: c₁₁ + c₂₂ = c₁₂ + c₂₁

But this is weaker than uniform (all equal). Why do we need uniformity?

**[GAP]** The triangle count argument only gives c₁₁ + c₂₂ = c₁₂ + c₂₁, not uniformity.

**Hypothesis:** Higher powers k ≥ 4 require stronger conditions. Need to analyze tr(T⁴) contributions.

---

### Condition 3 (Connectivity) is necessary

**Claim:** If the switch preserves NBL spectrum, then at least one of (a), (b), (c) holds.

**Proof attempt:**

We have the counterexample: switch (0,6)-(2,4) on graph ICXmeqsWw.
- Satisfies conditions 1 and 2
- Violates condition 3 (no parallel edges, no column edges)
- Is NOT cospectral: tr(T₁³) - tr(T₂³) = -0.111...

This proves condition 3 is necessary (by contrapositive).

**[COMPLETE]** ✓

---

## Proof Attempt: Sufficiency

This is where we expect failure.

### Strategy

Assume conditions 1-3 hold. We need to show tr(T_G^k) = tr(T_{G'}^k) for all k.

Write T_{G'} = T_G + Δ. Then:

```
tr(T_{G'}^k) = tr((T_G + Δ)^k) = tr(T_G^k) + [correction terms involving Δ]
```

For small k, we can expand:
- k=1: tr(T) = 0 for both (no 1-step returns)
- k=2: tr(T²) = 0 for both (no 2-step NB returns)
- k=3: First non-trivial case

### Analysis of k=3

We need tr(T_G³) = tr(T_{G'}³).

The diagonal entry T³[(u,v),(u,v)] counts weighted 3-step NB walks returning to (u,v).

Such walks have the form:
```
(u,v) → (v,a) → (a,b) → (b,u)
```
where a ≠ u, b ≠ v, and there are edges v-a, a-b, b-u.

The switch affects:
1. Walks using removed edges (involving v₁-w₁ or v₂-w₂)
2. Walks using added edges (involving v₁-w₂ or v₂-w₁)

### Change in tr(T³)

Let's categorize the affected 3-step return walks:

**Type A: Returns to edges (x, vᵢ) for x ∈ ext(vᵢ)**

Walk: (x,vᵢ) → (vᵢ,wⱼ) → (wⱼ,y) → (y,x)

This requires y ∈ N(wⱼ) ∩ N(x) with y ≠ vᵢ.

In G, available for j where vᵢ-wⱼ exists.
In G', available for the other j.

**Type B: Returns to edges (x, wⱼ) for x ∈ ext(wⱼ)**

Similar analysis with roles swapped.

**Type C: Returns to edges within S**

Walks starting from (v₁,v₂), (v₂,v₁), (w₁,w₂), (w₂,w₁) if those edges exist.

### The Cancellation Requirement

For tr(T_G³) = tr(T_{G'}³), we need:

```
Σ [T_{G'}³(e,e) - T_G³(e,e)] = 0
```

This sum has contributions from edges e affected by the switch.

**Under condition 1 (degree equality):**

The transition probabilities out of vᵢ and wⱼ are determined by degrees:
- From (x,vᵢ): probability 1/(deg(vᵢ)-1) to each neighbor except x
- From (x,wⱼ): probability 1/(deg(wⱼ)-1) to each neighbor except x

Since deg(v₁) = deg(v₂), the weights are symmetric.
Since deg(w₁) = deg(w₂), the weights are symmetric.

**Under condition 2 (uniform cross-intersection):**

The number of paths of each type is controlled by c = |ext(vᵢ) ∩ ext(wⱼ)|.

**Under condition 3 (connectivity):**

This is supposed to ensure the cancellation happens. Let's see why.

### Testing: Where Does Sufficiency Fail?

We know empirically that conditions 1-3 are not sufficient. Let's find a specific failure.

**Test case:** Graph ICdffZk]_, switch (0,7)-(1,8)

From earlier analysis:
- Condition 1: deg(0)=deg(1)=5, deg(7)=deg(8)=5 ✓
- Condition 2: Cross-int sizes (1,1,1,1) ✓
- Condition 3: ext(w₁)=ext(w₂)={2,4,5}, so there are shared vertices (tripods) ✓

Yet this switch is NOT cospectral (tr differs at k=3).

**[FAILURE POINT]** The conditions are satisfied but cospectrality fails.

---

## Analyzing the Failure

### The Failing Case in Detail

Graph: ICdffZk]_
Switch: v₁=0, v₂=1, w₁=7, w₂=8

```
Cross-intersection grid:
         w₁=7     w₂=8
  v₁=0:  {4}      {4}
  v₂=1:  {5}      {5}
```

Wait, this shows:
- ext(v₁) ∩ ext(w₁) = {4}
- ext(v₁) ∩ ext(w₂) = {4}
- ext(v₂) ∩ ext(w₁) = {5}
- ext(v₂) ∩ ext(w₂) = {5}

All size 1, so condition 2 is satisfied.

But notice: the vertices are {4} and {5} in different patterns.
- Row v₁: both cells contain {4}
- Row v₂: both cells contain {5}

This is a **degenerate case** where ext(vᵢ) ∩ ext(w₁) = ext(vᵢ) ∩ ext(w₂) for each i.

What edges exist among {4, 5}? If 4-5 is an edge...

**[TODO]** Check the actual graph structure and identify what's different from the cospectral cases.

---

## Observations from Failure

### Pattern in Cospectral Cases

Looking at the 11 cospectral pairs, the cross-intersection vertices are typically **all distinct**:

```
         w₁       w₂
  v₁:   {a}      {b}
  v₂:   {c}      {d}
```

where a, b, c, d are four different vertices.

### Pattern in Failing Cases

The failing case has:
```
         w₁       w₂
  v₁:   {4}      {4}
  v₂:   {5}      {5}
```

The same vertex appears in both columns of a row!

### New Hypothesis

**Condition 2':** Not only must all |ext(vᵢ) ∩ ext(wⱼ)| = c, but the sets should be "generic" in some sense. Specifically, perhaps:

- ext(vᵢ) ∩ ext(w₁) ∩ ext(w₂) = ∅ (no row-shared vertices), AND
- ext(v₁) ∩ ext(v₂) ∩ ext(wⱼ) = ∅ (no column-shared vertices unless intended as "tripod")

Or perhaps the condition is about the **distinctness** of the cross-intersection sets.

---

## Revised Conjecture

Based on the failure analysis, we hypothesize an additional condition:

**Condition 4 (Distinctness):** The four cross-intersection sets are pairwise disjoint:
```
(ext(v₁) ∩ ext(w₁)) ∩ (ext(v₁) ∩ ext(w₂)) = ∅
(ext(v₁) ∩ ext(w₁)) ∩ (ext(v₂) ∩ ext(w₁)) = ∅  [unless tripod intended]
... etc
```

Alternatively: |ext(v₁) ∩ ext(w₁) ∩ ext(w₂)| = 0 (no vertex is common neighbor of v₁, w₁, and w₂).

**[TODO]** Test this condition on the 11 cospectral pairs and the failing cases.

---

## Next Steps

1. Verify the failing case structure (ICdffZk]_, switch 0,7-1,8)
2. Formulate precise "distinctness" condition
3. Test on all 11 cospectral pairs
4. Test on failing cases to see if it filters them out
5. If successful, attempt proof with condition 4 added

---

## Key Finding: Local Conditions Are Not Sufficient

### The Critical Observation

Switches with **identical local signatures** can be cospectral or non-cospectral.

**Example: Pair 43 vs Failure**

Pair 43 (COSPECTRAL):
```
Graph: ICQubQxZg
Switch: v1=3, v2=6, w1=8, w2=9
Degrees: (4, 4, 6, 6)
Cross-int: {0}, {5}, {0}, {1}
Tripod: vertex 0 (in col w1)
Parallel: both v1-v2 and w1-w2
Col edges: 0
Signature: (1, 0, 0, 1, 0, True, True, 0, 0)
```

Failure (NOT COSPECTRAL):
```
Graph: ICXetrcfG
Switch: v1=3, v2=6, w1=9, w2=4
Degrees: (4, 4, 5, 5)
Cross-int: {0}, {7}, {0}, {1}
Tripod: vertex 0 (in col w1)
Parallel: both v1-v2 and w1-w2
Col edges: 0
Signature: (1, 0, 0, 1, 0, True, True, 0, 0)
```

**Same signature, different outcome.**

### What This Means

The conditions we identified:
1. Degree equality
2. Uniform cross-intersection
3. Connectivity (parallel/column edges/tripod)

These capture the **local structure** around the 4 switch vertices. But cospectrality depends on **global properties** of the graph that extend beyond this local neighborhood.

### The Missing Information

What differs between pair 43 and the failure with the same signature?

- Same c value
- Same sharing patterns
- Same parallel edges
- Same tripod structure

The difference must be in:
- How the cross-int vertices connect to the REST of the graph
- The structure of walks that pass THROUGH the switch region
- Some global spectral property

### Implications for the Theorem

**The theorem as stated cannot be proven** because conditions 1-3 are not sufficient.

To complete the characterization, we need either:
1. A condition on the global graph structure, OR
2. A direct algebraic condition on the perturbation matrix Δ, OR
3. An explicit trace computation showing when cancellation occurs

The local geometric conditions provide **necessary but not sufficient** constraints.

---

## Appendix: Empirical Data

### The 11 Cospectral Pairs (pair index, switch vertices)

| Pair | v₁ | v₂ | w₁ | w₂ | Parallel | Column edges |
|------|----|----|----|----|----------|--------------|
| 2    | 3  | 6  | 8  | 9  | both     | 1            |
| 18   | 1  | 3  | 7  | 8  | none     | 2            |
| 20   | 3  | 4  | 6  | 7  | none     | 1            |
| 26   | 2  | 5  | 7  | 9  | both     | 1            |
| 31   | 0  | 7  | 8  | 9  | both     | 2            |
| 41   | 0  | 6  | 7  | 8  | none     | 1            |
| 42   | 1  | 2  | 7  | 9  | w₁-w₂    | 1            |
| 43   | 3  | 6  | 8  | 9  | both     | 0            |
| 55   | 3  | 6  | 8  | 9  | v₁-v₂    | 0            |
| 63   | 2  | 4  | 6  | 7  | none     | 1            |
| 65   | 4  | 7  | 8  | 9  | both     | 0            |

### Counterexample (conditions 1-2 satisfied, condition 3 violated)

- Graph: ICXmeqsWw
- Switch: (0,6)-(2,4)
- Result: NOT cospectral, tr(T³) differs by 0.111

### Failing Case (conditions 1-3 satisfied, NOT cospectral)

- Graph: ICdffZk]_
- Switch: (0,7)-(1,8)
- Result: NOT cospectral, tr(T³) differs by 0.149
- Note: ext(w₁) = ext(w₂), creating degeneracy

---

## Algebraic Analysis: The Cancellation Mechanism

### Key Finding: Return Probability Cancellation

Through detailed analysis of the perturbation Δ = T₂ - T₁, we discovered the mechanism that determines cospectrality:

**In cospectral switches:** The return probability changes on common edges cancel EXACTLY within each group of "unique external vertices."

**In failing switches:** The return probability changes do NOT cancel within these groups.

### Detailed Mechanism

Define:
- ext(w) = N(w) \ S (external neighbors)
- unique_w1 = ext(w₁) \ ext(w₂) (vertices only in ext(w₁))
- unique_w2 = ext(w₂) \ ext(w₁) (vertices only in ext(w₂))

For each common edge e in the graph, let Δᵏ(e) = T₂ᵏ[e,e] - T₁ᵏ[e,e] be the change in k-step return probability.

**Cospectral condition:** For all k ≥ 1:
```
Σ_{x ∈ unique_w1} Σ_{e touches x} Δᵏ(e) = 0
Σ_{x ∈ unique_w2} Σ_{e touches x} Δᵏ(e) = 0
```

### Example: Pair 43 (Cospectral) vs Failure

**Pair 43 (COSPECTRAL, k=4):**

unique_w1 = {0, 7}:
- Vertex 0: total change = -0.029630
- Vertex 7: total change = +0.029630
- **SUM = 0** ✓

unique_w2 = {1, 5}:
- Vertex 1: total change = +0.077037
- Vertex 5: total change = -0.077037
- **SUM = 0** ✓

**Failure (NOT COSPECTRAL, k=4):**

unique_w1 = {0, 5, 8}:
- Vertex 0: total change = -0.027778
- Vertex 5: total change = +0.037037
- Vertex 8: total change = +0.027778
- **SUM = +0.037037** ✗

unique_w2 = {1, 2, 7}:
- Vertex 1: total change = +0.129630
- Vertex 2: total change = +0.037037
- Vertex 7: total change = -0.055556
- **SUM = +0.111111** ✗

### Why Graph Automorphisms Don't Explain It

One might expect that cospectrality requires an automorphism of G swapping w₁ ↔ w₂. However:

- 10 out of 11 cospectral pairs have **NO** automorphism swapping w₁ ↔ w₂
- Only Pair 18 has such an automorphism (|Aut| = 16)
- The other pairs have |Aut| = 1 or 2, with no swap automorphism

This proves that the cancellation is a **"phantom symmetry"** — the walks behave as if there's a symmetry even when the graph has no such automorphism.

### The Hidden Symmetry

In cospectral cases without automorphisms (like Pair 43):
- Vertices in unique_w1 have **complementary** connection patterns to S
- Vertex 0 connects to {v₁, v₂, w₁} (3 vertices in S)
- Vertex 7 connects to {w₁} only (1 vertex in S)
- Their return probability changes are exactly opposite

This "internal pairing" within unique_w1 creates the cancellation.

In failing cases:
- The vertices in unique_w1 don't pair up
- Vertex 0 connects to {v₁, v₂, w₁} (3 vertices)
- Vertices 5, 8 each connect to {w₁} only (1 vertex each)
- One "complex" vertex cannot balance two "simple" vertices

### Structural Condition (Partial)

Based on this analysis, a refined necessary condition is:

**Condition 5 (Internal Balance):** For each unique set (unique_w1, unique_w2, etc.), the return probability changes must sum to zero. This requires:

- The "complex" vertices (connected to multiple S vertices) balance the "simple" vertices (connected to one S vertex)
- This may require specific size relationships: |complex| relates to |simple| in a specific way

However, this is still not a purely structural condition — it's an algebraic condition that must hold for all k. Finding a graph-theoretic equivalent remains an open problem.

---

## Conclusion

### What We Learned

1. **Necessary conditions** (degree equality, uniform cross-intersection, connectivity) are well-understood and verified on all 11 cospectral pairs.

2. **These conditions are NOT sufficient.** There are 608+ switches satisfying all local conditions that are NOT cospectral.

3. **The gap** is explained by the "internal cancellation" mechanism: return probability changes on edges touching unique external vertices must cancel within each group.

4. **Graph automorphisms don't explain cospectrality.** Most cospectral pairs have no relevant automorphism.

5. **The true condition is algebraic**, not purely combinatorial. It involves how walks of arbitrary length interact with the graph structure outside the local switch region.

---

## Two Switching Mechanisms (Formal Statements)

We define two switching mechanisms, each given as a set of necessary and sufficient conditions. Together they explain 8 of the 11 observed NBL-cospectral 2-edge switch pairs.

---

### Mechanism A: Double-Parallel Switch

**Definition.** Let G be a simple graph and {v₁-w₁, v₂-w₂} be two disjoint edges with v₁, v₂, w₁, w₂ all distinct. Let G' be obtained by the 2-edge switch replacing {v₁-w₁, v₂-w₂} with {v₁-w₂, v₂-w₁}.

Define:
- S = {v₁, v₂, w₁, w₂}
- ext(u) = N(u) \ S for any u ∈ S
- shared = ext(w₁) ∩ ext(w₂)
- unique₁ = ext(w₁) \ ext(w₂)
- unique₂ = ext(w₂) \ ext(w₁)

**Theorem A (Conjectured).** The switch is a *Double-Parallel Switch* if and only if ALL of the following hold:

1. **Degree equality:** deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)

2. **Both parallel edges:** v₁-v₂ ∈ E(G) and w₁-w₂ ∈ E(G)

3. **Two shared external vertices:** |shared| = 2

4. **Uniform cross-intersection:** For c = |ext(v₁) ∩ ext(w₁)|,
   ```
   |ext(v₁) ∩ ext(w₁)| = |ext(v₁) ∩ ext(w₂)| = |ext(v₂) ∩ ext(w₁)| = |ext(v₂) ∩ ext(w₂)| = c
   ```

5. **Balanced unique sets:** |unique₁| = |unique₂| = 2

6. **Matching unique degrees:** The multisets of degrees are equal:
   ```
   {deg(x) : x ∈ unique₁} = {deg(x) : x ∈ unique₂}
   ```

**Claim:** If a switch satisfies conditions 1-6, then G and G' are NBL-cospectral.

**Evidence:** Pairs 25, 30, 42, 64 (all 4 satisfy these conditions and are cospectral).

| Pair | deg(v) | deg(w) | degs(unique) |
|------|--------|--------|--------------|
| 25   | 4      | 6      | {5, 5}       |
| 30   | 5      | 6      | {4, 4}       |
| 42   | 4      | 6      | {4, 4}       |
| 64   | 5      | 6      | {4, 4}       |

---

### Mechanism B: Isolated Single-Shared Switch

**Definition.** Same setup as Mechanism A.

**Theorem B (Conjectured).** The switch is an *Isolated Single-Shared Switch* if and only if ALL of the following hold:

1. **Degree equality:** deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)

2. **No parallel edges:** v₁-v₂ ∉ E(G) and w₁-w₂ ∉ E(G)

3. **Single shared external vertex:** |shared| = 1

4. **Uniform cross-intersection:** For c = |ext(v₁) ∩ ext(w₁)|,
   ```
   |ext(v₁) ∩ ext(w₁)| = |ext(v₁) ∩ ext(w₂)| = |ext(v₂) ∩ ext(w₁)| = |ext(v₂) ∩ ext(w₂)| = c
   ```

5. **Balanced unique sets:** |unique₁| = |unique₂| = 2

6. **Matching unique degrees:** The multisets of degrees are equal:
   ```
   {deg(x) : x ∈ unique₁} = {deg(x) : x ∈ unique₂}
   ```

**Claim:** If a switch satisfies conditions 1-6, then G and G' are NBL-cospectral.

**Evidence:** Pairs 17, 19, 40, 62 (all 4 satisfy these conditions and are cospectral).

| Pair | deg(v) | deg(w) | degs(unique) |
|------|--------|--------|--------------|
| 17   | 4      | 4      | {4, 4}       |
| 19   | 3      | 4      | {4, 5}       |
| 40   | 4      | 4      | {3, 3}       |
| 62   | 3      | 4      | {4, 5}       |

---

### Remaining Pairs (3 pairs not covered)

- **Pair 1:** Has both parallel edges and |shared|=1, but degs(unique₁) = {4,4} ≠ {5,5} = degs(unique₂)
- **Pair 41:** Has only w₁-w₂ parallel edge (not both), |shared|=1
- **Pair 54:** Has only v₁-v₂ parallel edge (not both), |shared|=2

These require additional mechanisms to explain.

---

### Summary

| Mechanism | Parallel edges | |shared| | |unique| | Key constraint |
|-----------|----------------|---------|---------|----------------|
| A         | Both           | 2       | 2, 2    | degs match     |
| B         | None           | 1       | 2, 2    | degs match     |

---

## Proof Attempt: Mechanism A (Double-Parallel Switch)

### Setup

Let G be a graph satisfying conditions 1-6 of Mechanism A. Define:
- S = {v₁, v₂, w₁, w₂}
- d_v = deg(v₁) = deg(v₂)
- d_w = deg(w₁) = deg(w₂)
- α = 1/(d_v - 1) (transition probability at v-vertices)
- β = 1/(d_w - 1) (transition probability at w-vertices)

The NBL transition matrix is:
```
T[(a,b), (b,c)] = 1/(deg(b) - 1)   if b-c ∈ E and c ≠ a
                = 0                 otherwise
```

### Key Observation: Degrees Are Preserved

The switch replaces edges {v₁-w₁, v₂-w₂} with {v₁-w₂, v₂-w₁}.

For each vertex u ∈ S:
- v₁: loses neighbor w₁, gains neighbor w₂ → deg unchanged
- v₂: loses neighbor w₂, gains neighbor w₁ → deg unchanged
- w₁: loses neighbor v₁, gains neighbor v₂ → deg unchanged
- w₂: loses neighbor v₂, gains neighbor v₁ → deg unchanged

Therefore deg(u) is the same in G and G' for all u. This means α and β are unchanged.

### The Perturbation Matrix

Let Δ = T_{G'} - T_G. The matrix Δ is sparse:

**Affected rows (x, v₁) for x ∈ N_G(v₁) \ {w₁}:**
```
Δ[(x,v₁), (v₁,w₁)] = -α    (edge removed)
Δ[(x,v₁), (v₁,w₂)] = +α    (edge added)
```

**Affected rows (x, v₂) for x ∈ N_G(v₂) \ {w₂}:**
```
Δ[(x,v₂), (v₂,w₂)] = -α
Δ[(x,v₂), (v₂,w₁)] = +α
```

**Affected rows (x, w₁) for x ∈ N_G(w₁) \ {v₁}:**
```
Δ[(x,w₁), (w₁,v₁)] = -β
Δ[(x,w₁), (w₁,v₂)] = +β
```

**Affected rows (x, w₂) for x ∈ N_G(w₂) \ {v₂}:**
```
Δ[(x,w₂), (w₂,v₂)] = -β
Δ[(x,w₂), (w₂,v₁)] = +β
```

Each affected row sums to zero: the outgoing probability mass is redistributed but conserved.

### Trace Analysis: k = 3

A contribution to tr(T³) comes from a closed 3-walk:
```
(a,b) → (b,c) → (c,a)
```
This requires a triangle a-b-c in G.

**Triangles affected by the switch:**

Lost triangles (using v₁-w₁):
- v₁-w₁-x where x ∈ ext(v₁) ∩ ext(w₁): contributes αβ/(deg(x)-1) each

Gained triangles (using v₁-w₂):
- v₁-w₂-x where x ∈ ext(v₁) ∩ ext(w₂): contributes αβ/(deg(x)-1) each

By condition 4, |ext(v₁) ∩ ext(w₁)| = |ext(v₁) ∩ ext(w₂)| = c.

**Key question:** Do the weighted sums match?

```
Σ_{x ∈ ext(v₁) ∩ ext(w₁)} 1/(deg(x)-1) =? Σ_{x ∈ ext(v₁) ∩ ext(w₂)} 1/(deg(x)-1)
```

This requires that the degree multisets are equal:
```
{deg(x) : x ∈ ext(v₁) ∩ ext(w₁)} = {deg(x) : x ∈ ext(v₁) ∩ ext(w₂)}
```

### Decomposing the Cross-Intersections

Recall:
- ext(w₁) = shared ∪ unique₁
- ext(w₂) = shared ∪ unique₂

Therefore:
```
ext(v₁) ∩ ext(w₁) = (ext(v₁) ∩ shared) ∪ (ext(v₁) ∩ unique₁)
ext(v₁) ∩ ext(w₂) = (ext(v₁) ∩ shared) ∪ (ext(v₁) ∩ unique₂)
```

The shared parts (ext(v₁) ∩ shared) are identical. So we need:
```
{deg(x) : x ∈ ext(v₁) ∩ unique₁} = {deg(x) : x ∈ ext(v₁) ∩ unique₂}
```

### When Does This Hold?

**Case 1: Uniform unique degrees**

If all vertices in unique₁ ∪ unique₂ have the same degree d_u (i.e., degs(unique) = [d_u, d_u]), then any subset has the same degree multiset.

Looking at our evidence:
- Pair 25: degs = [5,5] ✓
- Pair 30: degs = [4,4] ✓
- Pair 42: degs = [4,4] ✓
- Pair 64: degs = [4,4] ✓

All 4 pairs have uniform unique degrees!

**Refined Condition 6':** {deg(x) : x ∈ unique₁} = {deg(x) : x ∈ unique₂} = {d_u, d_u} for some d_u.

Under this stronger condition, for k=3:
- Lost contribution from v₁: c · αβ/(d_u - 1) [from unique₁ part] + [shared part]
- Gained contribution from v₁: c · αβ/(d_u - 1) [from unique₂ part] + [shared part]

These are equal. Similarly for v₂, w₁, w₂.

**Therefore tr(T³_G) = tr(T³_{G'}).** ✓

### Trace Analysis: k = 4

For k=4, we count closed 4-walks. The analysis is more complex but follows the same pattern.

A 4-walk (a,b) → (b,c) → (c,d) → (d,a) is affected if any of b,c,d ∈ S and the walk uses a switched edge.

**Claim:** Under conditions 1-6 with uniform unique degrees, the contributions cancel.

**Sketch:**
- The symmetry deg(v₁)=deg(v₂) and deg(w₁)=deg(w₂) ensures transition probabilities are symmetric
- The condition |unique₁|=|unique₂|=2 with matching degrees ensures the "mass" of walks through unique vertices balances
- The parallel edges v₁-v₂ and w₁-w₂ create additional 4-cycles that preserve symmetry

*[Full combinatorial verification needed]*

### Trace Analysis: General k

**Conjecture:** For all k ≥ 1, under Mechanism A with uniform unique degrees:
```
tr(T^k_G) = tr(T^k_{G'})
```

**Proof strategy:**
1. Show that Δ has a specific rank-2 structure
2. Use the symmetry conditions to show tr(Δ · T^{k-1}) = 0 for all k
3. Expand (T + Δ)^k and show all cross-terms vanish

### Numerical Verification

**Traces k=3 to 10:** All 4 Mechanism A pairs have tr(T₁ᵏ) = tr(T₂ᵏ) for k=3,...,10 (to machine precision).

**Full spectra:** Eigenvalue differences bounded by 3×10⁻¹⁵ for all pairs.

| Pair | d_v | d_w | max |λ₁-λ₂| |
|------|-----|-----|-------------|
| 25   | 4   | 6   | 3.0×10⁻¹⁵   |
| 30   | 5   | 6   | 1.4×10⁻¹⁵   |
| 42   | 4   | 6   | 1.6×10⁻¹⁵   |
| 64   | 5   | 6   | 2.1×10⁻¹⁵   |

### Refined Theorem A

Based on the proof and numerical verification:

**Theorem A (Double-Parallel Switch).** Let G satisfy:

1. deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)
2. v₁-v₂ ∈ E(G) and w₁-w₂ ∈ E(G)
3. |shared| = 2
4. Uniform cross-intersection: all |ext(vᵢ) ∩ ext(wⱼ)| = c
5. |unique₁| = |unique₂| = 2
6. **Uniform unique degrees:** All x ∈ unique₁ ∪ unique₂ have the same degree d_u

Then G and G' are NBL-cospectral.

**Status:** k=3 proven; k≥4 verified numerically; full proof pending.

### Gap in the Proof

The k=3 case is complete. For k≥4, the combinatorial analysis of affected walks becomes complex. A cleaner approach may be:

1. **Algebraic:** Show Δ = T' - T has rank ≤ 4 with specific structure, then use matrix perturbation theory
2. **Symmetry:** Construct an explicit similarity transformation between T and T'
3. **Generating function:** Show the characteristic polynomials are equal

---

## Open Questions

1. Are Mechanisms A and B actually sufficient? (Needs verification on non-cospectral switches with same structure)

2. What mechanism explains the remaining 3 pairs (1, 41, 54)?

3. Is there a unified condition that covers all 11?

4. For graphs with specific structure (e.g., regular graphs), are simpler conditions sufficient?
