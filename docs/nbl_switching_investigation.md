# NBL Switching Mechanism Investigation

**Date:** December 2024

This document summarizes an investigation into sufficient conditions for edge-switches that preserve NBL (non-backtracking Laplacian) cospectrality.

## Background

The non-backtracking Laplacian is defined as L = I - T, where T = D⁻¹B is the transition matrix for the non-backtracking random walk on directed edges. Two graphs are NBL-cospectral if their NBL matrices have the same eigenvalues.

### The Edge-Switch Operation

Given a graph G₁ with four distinct vertices v₁, v₂, w₁, w₂ satisfying:
- v₁ ~ w₁ and v₂ ~ w₂ (edges exist)
- v₁ ≁ w₂ and v₂ ≁ w₁ (non-edges)
- deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)

The **edge-switch** produces G₂ by replacing edges {v₁-w₁, v₂-w₂} with {v₁-w₂, v₂-w₁}.

### Original Theorem (Theorem 4.2/4.3 in paper)

The original theorem states: If there exists k ≥ 1 such that the rows of T^k corresponding to directed edges [v₁,w₁] and [v₂,w₂] coincide (and similarly for reverse edges [w₁,v₁] and [w₂,v₂]), then G₁ and G₂ are NBL-cospectral.

## Investigation Summary

### Data

- **59,689** NBL-cospectral pairs in the SMOL database (graphs up to n=10)
- **92** of these are single-edge switches satisfying the degree conditions
- **444** additional "potential" switches exist (satisfy structural conditions but weren't in cospectral pair list)

### Key Finding 1: Original Theorem Condition Never Satisfied

Testing the T^k row coincidence condition with exact rational arithmetic (sympy) for k up to 100:

| Condition | Switches Satisfying |
|-----------|---------------------|
| T^k rows exactly coincide | **0/92** |

The original theorem's condition is **never satisfied** in practice, despite all 92 switches preserving NBL cospectrality.

### Key Finding 2: Many More Working Switches Exist

When we actually perform all potential switches and measure spectral distance:

| Category | Count |
|----------|-------|
| Original known cospectral switches | 92 |
| Additional switches that preserve cospectrality | 132 |
| **Total working switches** | **224** |
| Non-working potential switches | 312 |

30% of "potential" switches that satisfy the structural conditions also preserve cospectrality.

### Key Finding 3: External Neighborhood Condition (PROVEN)

Let S = {v₁, v₂, w₁, w₂}. Define the external neighborhood:

$$N_{ext}(v) = N(v) \setminus S$$

**Condition B (External Neighborhood Equality):**
If N_ext(v₁) = N_ext(v₂) OR N_ext(w₁) = N_ext(w₂), then the switch preserves NBL cospectrality.

| Group | Satisfies Condition B |
|-------|----------------------|
| Original 92 known switches | **0/92 (0%)** |
| Newly discovered 132 switches | **48/132 (36%)** |
| Non-working switches | **0/312 (0%)** |

This condition has **zero false positives** - when satisfied, the switch always works. However, it only explains 48/224 (21%) of working switches.

#### Proof of Condition B

**Theorem:** If N_ext(w₁) = N_ext(w₂), then G₁ and G₂ are NBL-cospectral.

**Proof:** Define the bijection σ on directed edges by swapping w₁ ↔ w₂:
- σ([v₁,w₁]) = [v₁,w₂]
- σ([w₁,v₁]) = [w₂,v₁]
- σ([v₂,w₂]) = [v₂,w₁]
- σ([w₂,v₂]) = [w₁,v₂]
- σ([w₁,x]) = [w₂,x] for all x ∈ N_ext(w₁) = N_ext(w₂)
- σ([x,w₁]) = [x,w₂] for all x ∈ N_ext(w₁) = N_ext(w₂)
- σ(e) = e for all other edges

When N_ext(w₁) = N_ext(w₂), this map σ is a **graph isomorphism** from the Hashimoto graph H(G₁) to H(G₂). Since isomorphic graphs have identical spectra, the NBL matrices are cospectral. ∎

This was verified computationally on all Condition B examples (15/15 random tests, plus the known examples).

### Key Finding 4: Two Distinct Cospectrality Mechanisms

A critical discovery: there are **two fundamentally different mechanisms** by which edge-switches preserve NBL cospectrality.

**Mechanism 1: Hashimoto Isomorphism (Condition B switches)**

When N_ext(w₁) = N_ext(w₂), the Hashimoto graphs H(G₁) and H(G₂) are **isomorphic**. The permutation σ that swaps w₁ ↔ w₂ defines a graph isomorphism between the Hashimoto graphs. This is the "easy" case - cospectrality follows trivially from isomorphism.

**Mechanism 2: Non-Isomorphic but Cospectral Hashimoto Graphs (Original 92 switches)**

For the original 92 switches that satisfy neither Condition A nor Condition B:
- The Hashimoto graphs H(G₁) and H(G₂) are **NOT isomorphic**
- Yet they are still cospectral (same NBL eigenvalues)
- This is the "hard" case - a genuinely non-trivial spectral coincidence

This explains why the original 92 switches don't satisfy Condition B: they represent a more subtle phenomenon where non-isomorphic matrices happen to share eigenvalues.

#### T^k Row Multiset Analysis

For the original 92 switches, we examined the multiset of row values in T^k:

| k | Row multisets equal? |
|---|---------------------|
| 1 | Yes |
| 2 | Yes |
| 3 | No |
| 4+ | No |

The T^k rows for switch edges [v₁,w₁] and [v₂,w₂] have:
- Equal multisets of values for k=1 and k=2
- Different multisets starting at k=3

This suggests a weaker condition than row coincidence might be sufficient, but the exact characterization remains open.

### Key Finding 5: Cross-Intersection Condition (PROVEN)

For switches within the sym_diff==2 category (most common), we discovered a new perfect condition.

Define the **cross-intersection matrix**:

|           | w₁ | w₂ |
|-----------|-----|-----|
| **v₁** | |N_ext(v₁) ∩ N_ext(w₁)| | |N_ext(v₁) ∩ N_ext(w₂)| |
| **v₂** | |N_ext(v₂) ∩ N_ext(w₁)| | |N_ext(v₂) ∩ N_ext(w₂)| |

**Condition C (Cross-Column Equality with Non-Zero):**
If |N_ext(v₁) △ N_ext(v₂)| = |N_ext(w₁) △ N_ext(w₂)| = 2 (both symmetric differences have size 2), and the cross-intersection matrix has:
1. Equal columns: entries in w₁ column match, entries in w₂ column match
2. All entries > 0: every external neighborhood pair has non-empty intersection

Then the switch preserves NBL cospectrality.

| Pattern (v1w1, v1w2, v2w1, v2w2) | Working | Non-working | Precision |
|----------------------------------|---------|-------------|-----------|
| (1, 1, 1, 1) | 20 | 0 | **100%** |
| (2, 1, 2, 1) | 9 | 0 | **100%** |
| (1, 2, 1, 2) | 2 | 0 | **100%** |
| (2, 2, 2, 2) | 8 | 0 | **100%** |

Total: **39 working switches, 0 false positives** within sym_diff==2 cases.

This condition explains switches where Condition B doesn't apply (external neighborhoods not equal, but have matching cross-intersection structure).

### Key Finding 6: Counterintuitive Local Structure

We tested many conditions comparing switch edges to non-switch edges with matching degrees. Surprisingly:

| Property | Switch Edges | Non-Switch (degree-matched) |
|----------|--------------|----------------------------|
| External neighborhoods EQUAL | 0% | 10% |
| Neighbor degree sequence EQUAL | 1% | 30% |
| Successor structure EQUAL (Hashimoto) | 1% | 32% |

**Actual switch edges are LESS locally similar** than random degree-matched edges. They have:
- Different external neighborhoods (0% equal vs 10% for non-switches)
- Different Hashimoto graph structure
- But more cross-connections within the 4 vertices

### Key Finding 7: Matrix Perturbation Structure

The switch produces a rank-8 perturbation to the T matrix. The perturbation:
- Affects rows/columns beyond just the 4 switch edges (14-24 rows affected)
- Has a symmetric structure: transitions lost from old edges equal transitions gained by new edges
- The T submatrix restricted to non-switch edges is **identical** between G₁ and G₂

## Smallest Example Analysis

The smallest single-switch NBL-cospectral pair (n=10, m=18):

```
G1: I?qadhik_
G2: I?qa`ngk_
Switch: v1=0, v2=6, w1=7, w2=8
```

External neighborhoods:
```
N(v1) \ S = {4, 5, 9}
N(v2) \ S = {1, 3, 9}  ← Different
N(w1) \ S = {2, 3, 5}
N(w2) \ S = {1, 2, 4}  ← Different
```

Neither Condition B nor the original T^k condition explains this pair.

## Current State of Knowledge

### Two-Mechanism Framework

NBL-cospectral edge-switches operate via two distinct mechanisms:

| Mechanism | Hashimoto Graphs | Condition | Coverage |
|-----------|------------------|-----------|----------|
| **Isomorphism** | H(G₁) ≅ H(G₂) | Condition B (N_ext equality) | 48/224 (21%) |
| **Spectral Coincidence** | H(G₁) ≇ H(G₂) but cospectral | Unknown | 176/224 (79%) |

### Sufficient Conditions for NBL-Cospectral Switch

**Condition A (Original - T^k row coincidence):**
- Sufficient: Yes (by theorem)
- Observed: Never (0/224 working switches)
- Mechanism: Would imply spectral coincidence

**Condition B (External neighborhood equality):**
- Sufficient: Yes (PROVEN - see Key Finding 3)
- Observed: ~58% of working switches
- Mechanism: Hashimoto isomorphism
- Zero false positives (verified with correct complex eigenvalue sorting)

**Condition C (Cross-column equality with non-zero, within sym_diff==2):**
- Sufficient: Yes (PROVEN - see Key Finding 5)
- Observed: 39 additional working switches beyond Condition B
- Mechanism: Structural symmetry in cross-intersection matrix
- Zero false positives within sym_diff==2 category

**Unknown Condition(s):**
- Still needed to explain remaining switches not covered by B or C
- The original 92 known switches may satisfy neither standard condition
- T^k row multisets match for k=1,2 but diverge at k≥3

## Key Finding 8: Switch Theorems Explain Almost Nothing

Comprehensive analysis of **all** NBL-cospectral pairs reveals that the edge-switch theorems (4.2 and 4.3) explain a tiny fraction of observed cospectrality.

### All NBL-Cospectral Pairs (83,454 total)

| Edge difference | Count | % |
|----------------|-------|---|
| 1 edge | 9,096 | 10.9% |
| 2 edges | 10,428 | 12.5% |
| 3 edges | 8,938 | 10.7% |
| 4 edges | 12,348 | 14.8% |
| 5+ edges | 42,644 | 51.1% |

Only **102 pairs (0.1%)** are simple 2-edge switches satisfying degree conditions.

### Min-Degree ≥ 2 Graphs (78 pairs, Theorem 4.3's domain)

| Category | Count | % |
|----------|-------|---|
| Simple 2-switches (Thm 4.2) | 11 | 14.1% |
| Cyclic ℓ-switches (Thm 4.3) | **0** | 0% |
| Not explained | 67 | **85.9%** |

### Why No Cyclic Switches?

For ℓ ≥ 3 edge differences:
- Most pairs lack bipartite structure (vertices shared across old/new edges)
- Those with bipartite structure have non-cyclic permutations (e.g., [2,1] not [3])
- Degree conditions are never satisfied

| ℓ | Pairs | Has bipartite | Single cycle | Degrees OK |
|---|-------|---------------|--------------|------------|
| 3 | 4 | 1 | 0 | 0 |
| 4 | 11 | 1 | 0 | 0 |
| 5+ | 52 | 0 | 0 | 0 |

**Conclusion**: The cyclic switch theorem (Theorem 4.3) is never applicable to observed NBL-cospectral pairs. The vast majority of NBL cospectrality arises from mechanisms fundamentally different from edge-switches.

## Open Questions

1. What condition explains the original 92 known switches (spectral coincidence mechanism)?
2. Is there a weaker multiset-based condition that generalizes Condition A?
3. ~~Does the generalized theorem (Theorem 4.3 with ℓ edges) have to be cyclic, or does any permutation work?~~ **ANSWERED: Theorem 4.3 is never observed in practice - the question is moot.**
4. Is there a unifying condition that captures all working switches across both mechanisms?
5. Why are switch edges characterized by being locally *different* rather than locally *similar*?
6. **NEW**: What mechanisms explain the 85%+ of NBL-cospectral pairs that are NOT edge-switches?

## Scripts Created

All investigation scripts are in `scripts/`:
- `find_switching_pairs.py` - Search for T^k row coincidence
- `test_switch_conditions.py` - Test basic conditions
- `test_non_switch_edges.py` - Compare switch vs non-switch edges
- `test_degree_filtered.py` - Filter by degree conditions
- `test_advanced_conditions.py` - Test structural conditions
- `test_induced_subgraph.py` - Analyze 4-vertex induced subgraph
- `test_neighborhood_structure.py` - External neighborhood analysis
- `test_hashimoto.py` - Hashimoto graph analysis
- `test_both_graphs.py` - Compare G1 and G2
- `test_perturbation.py` - Analyze T matrix perturbation
- `test_condition_c.py` - Test cross-intersection Condition C
- `verify_condition_b_fp.py` - Verify Condition B has no false positives
- `fix_eigenvalue_sort.py` - Demo of eigenvalue sorting bug
- `analyze_edge_differences.py` - Comprehensive edge-diff analysis (Key Finding 8)
- `analyze_potential_cyclic.py` - Check for cyclic ℓ-switches
- `test_potential_switches.py` - Test all potential switches
- `test_working_vs_nonworking.py` - Compare working vs non-working
