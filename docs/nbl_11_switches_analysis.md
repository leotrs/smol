# NBL Two-Edge Switch Analysis

**Date:** December 2024

This document focuses on the 11 NBL-cospectral pairs (n=10, min_degree≥2) that are simple 2-edge switches.

## Summary of Findings

### The 78 pairs break down as:
- **11 pairs**: 2-edge switches
- **67 pairs**: NOT 2-edge switches (3-10 edge differences)

### For the 67 non-switch pairs:
- 12 have V-W bipartite permutation structure
- **55 have NO permutation structure at all** (82%)
- These need a completely different explanation (not covered here)

### For the 11 two-edge switches:

**Key finding**: The cospectrality is achieved via **genuine spectral coincidence**, NOT via matrix similarity.

| Property | Status |
|----------|--------|
| Hashimoto graphs H(G₁) ≅ H(G₂)? | **NO** (verified for all 11) |
| NBL matrices permutation-similar? | **NO** (T₂ ≠ P·T₁·Pᵀ for any P) |
| NBL matrices cospectral? | **YES** (eigenvalues match to 10⁻¹⁵) |

### Structure of the perturbation Δ = T₂ - T₁:
- rank(Δ) = 4
- All row sums of Δ = 0
- All column sums of Δ = 0
- tr(T₁ᵏ) = tr(T₂ᵏ) for all k (verified up to k=14)

### Open question:
What algebraic condition on a 2-edge switch guarantees trace equality for all powers?

## The 11 Pairs

```
ICXmeqsWw       ICXmeqe[W
ICR`vGy}?       ICR`thi}?
ICQbeZqz?       ICQbUjqz?
ICpfdrdVo       ICpfczd]o
ICZLfa{Xw       ICZLf_|xg
I?qadhik_       I?qa`ngk_
ICR`ujgMo       ICR`tjgUo
ICQubQxZg       ICQubQj^G
ICQubQxZ_       ICQubQj^?
ICQfAxuv?       ICQeRhuv?
ICXmdritW       ICXmdrbvG
```

## Interpretation of T and its powers

**The NBL transition matrix T = D⁻¹B**:
- T[(u,v), (v,w)] = 1/(deg(v) - 1) if w ≠ u
- T is a stochastic matrix (rows sum to 1)
- T^k[e,f] = probability of reaching f from e in k steps of NB random walk

**Diagonal entries and trace**:
- T^k[e,e] = probability of returning to edge e after exactly k steps
- tr(T^k) = Σₑ T^k[e,e] = sum of all return probabilities
- tr(T^k) = Σᵢ λᵢᵏ (sum of k-th powers of eigenvalues)

## Key Discovery: Uniform Cross-Intersection

### The Cross-Intersection Matrix

For a 2-edge switch with vertices S = {v₁, v₂, w₁, w₂}, define:

```
        w₁                      w₂
v₁   |ext(v₁) ∩ ext(w₁)|    |ext(v₁) ∩ ext(w₂)|
v₂   |ext(v₂) ∩ ext(w₁)|    |ext(v₂) ∩ ext(w₂)|
```

where ext(v) = N(v) \ S (neighbors outside the switch vertices).

### Empirical Finding

**All 11 two-edge switch pairs have UNIFORM cross-intersection:**

| Pair | c₁₁ | c₁₂ | c₂₁ | c₂₂ | Pattern |
|------|-----|-----|-----|-----|---------|
| 1-9  |  1  |  1  |  1  |  1  | uniform |
| 10   |  2  |  2  |  2  |  2  | uniform |
| 11   |  2  |  2  |  2  |  2  | uniform |

### Cancellation Structure

The diagonal entries of T₁^k and T₂^k are NOT permutations of each other.
Individual return probabilities differ, but the differences cancel in the sum.

For k=3 in the first pair:
- Sum of positive differences: +0.1458
- Sum of negative differences: -0.1458
- Total: 0 (exact cancellation)

The cancellation occurs because:
1. Edges paired under the full swap (v₁↔v₂, w₁↔w₂) cancel exactly
2. Unpaired edges involve vertices in ext(vᵢ) ∩ ext(wⱼ)
3. Uniform cross-intersection ensures these unpaired contributions balance

## Main Conjecture (Refined)

**Important:** Uniform cross-intersection alone is NOT sufficient. A counterexample exists.

### Counterexample

On graph `ICXmeqsWw`, the switch (0,6)-(2,4) has:
- Degree equality: all four vertices have degree 4 ✓
- Uniform cross-intersection: all cᵢⱼ = 1 ✓
- Yet tr(T₁³) ≠ tr(T₂³), so NOT cospectral ✗

```
Switch vertices: v₁=0, v₂=2, w₁=6, w₂=4

Cross-intersection grid:
         w₁=6    w₂=4
  v₁=0:  {3}     {7}
  v₂=2:  {9}     {5}

Edges among cross-int vertices: 3-7 (row), 7-9 (diagonal)
No column edges, no parallel edges → NOT cospectral
```

### The Missing Condition: Column Edges

A **column edge** connects two cross-intersection vertices in the same column:
- Column w₁: edge between some x ∈ ext(v₁)∩ext(w₁) and y ∈ ext(v₂)∩ext(w₁)
- Column w₂: edge between some x ∈ ext(v₁)∩ext(w₂) and y ∈ ext(v₂)∩ext(w₂)

### Refined Conjecture

**Theorem (NBL 2-Edge Switch):** A 2-edge switch {v₁-w₁, v₂-w₂} → {v₁-w₂, v₂-w₁} preserves NBL spectrum if and only if:

1. **Degree equality**: deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)

2. **Uniform cross-intersection**: all cᵢⱼ = |ext(vᵢ) ∩ ext(wⱼ)| are equal

3. **Connectivity condition** (at least one of):
   - (a) **Parallel edge**: v₁-v₂ or w₁-w₂ exists in G, OR
   - (b) **Column edge**: edge between ext(v₁)∩ext(wⱼ) and ext(v₂)∩ext(wⱼ) for some j

### Verification on the 11 Pairs

| Pair | Deg eq | Uniform | Parallel | Column | Predicted | Actual |
|------|--------|---------|----------|--------|-----------|--------|
| 1    | ✓      | ✓       | ✓        | ✓      | ✓         | ✓      |
| 2    | ✓      | ✓       | ✗        | ✓      | ✓         | ✓      |
| 3    | ✓      | ✓       | ✗        | ✓      | ✓         | ✓      |
| 4    | ✓      | ✓       | ✓        | ✓      | ✓         | ✓      |
| 5    | ✓      | ✓       | ✓        | ✓      | ✓         | ✓      |
| 6    | ✓      | ✓       | ✗        | ✓      | ✓         | ✓      |
| 7    | ✓      | ✓       | ✓        | ✓      | ✓         | ✓      |
| 8    | ✓      | ✓       | ✓        | ✗      | ✓         | ✓      |
| 9    | ✓      | ✓       | ✓        | ✗      | ✓         | ✓      |
| 10   | ✓      | ✓       | ✗        | ✓      | ✓         | ✓      |
| 11   | ✓      | ✓       | ✓        | ✗      | ✓         | ✓      |

All 11 pairs satisfy the conjecture. Pairs 2, 3, 6, 10 have no parallel edges but DO have column edges.

### Why Column Edges Matter

A column edge creates a path between ext(v₁) and ext(v₂) that goes through a common neighbor of wⱼ. This creates additional symmetry that enables trace cancellation.

Geometrically:
- A parallel edge (v₁-v₂ or w₁-w₂) provides direct coupling between the two "sides" of the switch
- A column edge provides indirect coupling through the cross-intersection structure

Without either type of coupling, the return probabilities don't balance, and traces diverge at k=3.

## Proof Sketch

**Theorem:** Under conditions 1-3, tr(T₁^k) = tr(T₂^k) for all k ≥ 1.

**Proof idea:**

The perturbation Δ = T₂ - T₁ affects return probabilities for edges incident to S = {v₁, v₂, w₁, w₂}.

For trace equality, we need:
∑ₑ [T₂^k(e,e) - T₁^k(e,e)] = 0

The cancellation occurs in two parts:

1. **Parallel edge contribution**: When v₁-v₂ or w₁-w₂ exists, edges like (v₁,v₂) and (v₂,v₁) have symmetric perturbations that cancel.

2. **Column edge contribution**: When x ∈ ext(v₁)∩ext(wⱼ) and y ∈ ext(v₂)∩ext(wⱼ) are adjacent, the edges (x,v₁), (y,v₂) have return probability changes that cancel due to the uniform cross-intersection combined with the x-y connection providing a "balance path."

Without either mechanism, the trace differences at k=3 involve 3-cycles through the switch that don't have compensating terms.

**Open question:** Prove this rigorously by computing the explicit trace contributions.

## Extension to k-Edge Bipartite Switches

The 67 non-2-edge pairs include 12 that have a **bipartite permutation structure**: edges differ between vertex sets V and W. We analyzed whether the 2-edge switch conjecture extends.

### Setup

A **k-edge bipartite switch** between V and W:
- G₁ has k edges between V and W
- G₂ replaces them with a different set of k edges between V and W
- The switch graph (union of differing edges) is bipartite with parts V, W

### Cross-Intersection Matrix for k-Edge Switches

For V = {v₁, ..., vₘ} and W = {w₁, ..., wₙ}, define the m×n matrix:

```
C[i,j] = |ext(vᵢ) ∩ ext(wⱼ)|
```

where ext(v) = N(v) \ (V ∪ W).

### Findings on the 12 Bipartite Switches

| Pair | |V| | |W| | Row sums equal | Col sums equal | Uniform |
|------|-----|-----|----------------|----------------|---------|
| 13   | 4   | 2   | ✗              | ✓              | ✗       |
| 16   | 2   | 4   | ✓              | ✗              | ✗       |
| 22   | 3   | 5   | ✗              | ✗              | ✗       |
| 23   | 4   | 3   | ✗              | ✗              | ✗       |
| 37   | 2   | 4   | ✓              | ✓              | ✓       |
| 46   | 2   | 4   | ✓              | ✗              | ✗       |
| 48   | 5   | 4   | ✗              | ✗              | ✗       |
| 49   | 2   | 4   | ✓              | ✗              | ✗       |
| 58   | 4   | 2   | ✗              | ✓              | ✗       |
| 65   | 2   | 4   | ✓              | ✗              | ✗       |
| 68   | 2   | 4   | ✓              | ✗              | ✗       |
| 69   | 2   | 4   | ✓              | ✗              | ✗       |

### Pattern

**When |V| = 2:** All 7 cases have equal row sums (pairs 16, 37, 46, 49, 65, 68, 69)

**When |W| = 2:** All 2 cases have equal column sums (pairs 13, 58)

**When both |V| > 2 and |W| > 2:** Neither condition holds (pairs 22, 23, 48) — different mechanism

### Extended Conjecture

**Conjecture (k-Edge Bipartite Switch with |V|=2):**

A k-edge bipartite switch between V = {v₁, v₂} and W = {w₁, ..., wₖ} preserves NBL spectrum if:

1. **Degree equality in V**: deg(v₁) = deg(v₂)

2. **Equal row sums**: Σⱼ |ext(v₁) ∩ ext(wⱼ)| = Σⱼ |ext(v₂) ∩ ext(wⱼ)|

3. **Connectivity condition**: v₁-v₂ edge exists, or column edges exist

The symmetric statement holds when |W| = 2 (equal column sums required).

### Open Questions

1. What mechanism explains pairs 22, 23, 48 where neither |V|=2 nor |W|=2?

2. What explains the 55 pairs with no bipartite structure at all?

3. Can the connectivity condition be made precise for k > 2?

## Summary of Conjectures

### Conjecture 1: NBL 2-Edge Switch (NECESSARY but NOT SUFFICIENT)

**Status:** Proof attempt revealed conditions are necessary but not sufficient.

A 2-edge switch {v₁-w₁, v₂-w₂} → {v₁-w₂, v₂-w₁} CAN preserve NBL spectrum only if:

1. **Degree equality**: deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)
2. **Uniform cross-intersection**: |ext(vᵢ) ∩ ext(wⱼ)| = c for all i,j, with c ≥ 1
3. **External degree equality**: |ext(v₁)| = |ext(v₂)| and |ext(w₁)| = |ext(w₂)|
4. **Connectivity**: at least one of:
   - v₁-v₂ or w₁-w₂ exists (parallel edge), OR
   - Edge between ext(v₁)∩ext(wⱼ) and ext(v₂)∩ext(wⱼ) for some j (column edge)

**Verification:**
- All 11 known cospectral pairs satisfy conditions 1-4 ✓
- Counterexample (0,6)-(2,4) on ICXmeqsWw violates condition 4 and is NOT cospectral ✓
- Many switches satisfy 1-4 but are NOT cospectral (conditions not sufficient)

**Gap in proof:** There exist additional algebraic constraints beyond 1-4 that distinguish
cospectral from non-cospectral switches. The trace cancellation mechanism requires specific
global structure that the geometric conditions do not fully capture.

**Additional observations:**
- Condition B (ext(w₁) = ext(w₂)) is NOT sufficient for NBL cospectrality
- Cross-int edge patterns (row/col/diag edges between cells) vary among the 11 pairs
- Trace divergence typically occurs at k=3 when conditions fail

### Conjecture 2: k-Edge Bipartite Switch with |V|=2 (Observed on 7 pairs)

A k-edge switch between V = {v₁, v₂} and W preserves NBL spectrum if:

1. deg(v₁) = deg(v₂)
2. Row sums of cross-intersection matrix are equal
3. Some connectivity condition (parallel edge in V or column edges)

## Open Problems

1. **Find missing condition(s):** What additional constraints make 1-4 sufficient?
2. **Algebraic characterization:** What property of Δ = T₂ - T₁ guarantees tr(Δ·T₁^k) = 0 for all k?
3. **Role of connectivity:** Why do parallel/column edges enable trace cancellation?
4. **Extension:** Characterize k-edge switches for k > 2
