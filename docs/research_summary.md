# Research Summary: Generalized NBL-Cospectral Switch Theorem

**Date:** December 2024  
**Status:** Completed

## Executive Summary

This research successfully generalized the Mechanism A proof for NBL-cospectral 2-edge switches. The key finding is that the original Mechanism A conditions were **sufficient but not necessary**. All 11 known NBL-cospectral 2-edge switches (in the n=10, min-degree≥2 dataset) are explained by a single unified theorem with simpler conditions.

## Original vs Generalized Conditions

### Original Mechanism A Conditions (Overly Restrictive)
1. Degree equality: $\deg(v_1) = \deg(v_2)$, $\deg(w_1) = \deg(w_2)$
2. Both parallel edges exist: $v_1v_2 \in E$ and $w_1w_2 \in E$
3. Shared size: $|\text{shared}| = 2$
4. Uniform cross-intersection: $|ext(v_i) \cap ext(w_j)| = c$ for all $i,j$
5. Unique size: $|\text{unique}_1| = |\text{unique}_2| = 2$
6. Uniform unique degrees: all vertices in unique$_1 \cup$ unique$_2$ have same degree

**Satisfied by:** 4 of 11 switches (indices 3, 4, 8, 10)

### Generalized Conditions (Minimal and Sufficient)
**(C1)** Degree equality: $\deg(v_1) = \deg(v_2)$ and $\deg(w_1) = \deg(w_2)$

**(C2)** Uniform cross-intersection: $|ext(v_i) \cap ext(w_j)| = c$ for all $i,j \in \{1,2\}$

**Satisfied by:** All 11 of 11 switches

## Key Theoretical Insights

### Lemma: Derived Conditions
From (C1) and (C2), we automatically get:
- $|\text{unique}_1| = |\text{unique}_2|$ (follows from degree equality)
- $|\text{ext}(v_i) \cap \text{unique}_1| = |\text{ext}(v_i) \cap \text{unique}_2|$ (follows from uniform cross)

### Proof Technique: Aggregate Weight Matching
The proof uses **aggregate weight matching** via lumped boundary types:
1. Partition boundary edges by type (v₁, v₂, w₁-shared, w₂-shared, w₁-unique, w₂-unique)
2. Define swap σ: w₁ ↔ w₂ on boundary types
3. Show that total transition weights between type classes are preserved under σ
4. Conclude trace equality: $\text{tr}(T_G^k) = \text{tr}(T_{G'}^k)$ for all $k$

### What is NOT Required
- Parallel edges (v₁-v₂ or w₁-w₂) - NOT necessary
- $|\text{shared}| = 2$ - NOT necessary (any value works)
- Uniform unique degrees - NOT necessary
- Specific edge structure within S - NOT necessary

## Experimental Verification

| Switch | $|\text{shared}|$ | Parallel | Orig. Mech A | Gen. Conds |
|--------|-------------------|----------|--------------|------------|
| 0 | 1 | Both | ✗ | ✓ |
| 1 | 1 | None | ✗ | ✓ |
| 2 | 1 | None | ✗ | ✓ |
| 3 | 2 | Both | ✓ | ✓ |
| 4 | 2 | Both | ✓ | ✓ |
| 5 | 1 | One | ✗ | ✓ |
| 6 | 1 | None | ✗ | ✓ |
| 7 | 2 | One | ✗ | ✓ |
| 8 | 2 | Both | ✓ | ✓ |
| 9 | 1 | None | ✗ | ✓ |
| 10 | 2 | Both | ✓ | ✓ |

## Conclusion: No Separate "Mechanism B"

The original investigation hypothesized that switches not satisfying Mechanism A might require a different "Mechanism B". This is **not the case**.

All 11 switches are explained by the single unified theorem with conditions (C1) + (C2). The 7 switches that don't satisfy original Mechanism A simply have:
- $|\text{shared}| = 1$ instead of 2, or
- Missing parallel edges, or
- Non-uniform unique degrees

But these differences don't affect NBL-cospectrality - only (C1) and (C2) matter.

## Files Created

1. `docs/generalized_switch_theorem.md` - Full formal proof
2. `scripts/check_mechanism_a.py` - Tests original conditions
3. `scripts/find_necessary_conditions.py` - Identifies universal conditions
4. `scripts/comprehensive_conditions.py` - Detailed boundary analysis
5. `scripts/lumped_trace_proof.py` - Verifies aggregate matching
6. `scripts/final_verification.py` - Confirms all switches satisfy (C1)+(C2)

## Future Work

1. **Necessity proof:** Show that (C1) and (C2) are not just sufficient but necessary
2. **Higher-order switches:** Extend to 3-edge, 4-edge switches
3. **Non-switch pairs:** Analyze the 67 non-switch pairs (different mechanism entirely)
