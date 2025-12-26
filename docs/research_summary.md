# Research Summary: NBL-Cospectral Switch Theorem

**Date:** December 2024 (updated December 21, 2024)  
**Status:** Completed

## Executive Summary

This research established conditions under which a 2-edge switch preserves the NBL (non-backtracking Laplacian) spectrum. At n=10 with min_degree ≥ 2:

| Category | Count |
|----------|-------|
| Total NBL-cospectral pairs | 78 |
| Explained by (C1)+(C2) switch theorem | **62** (79%) |
| Unexplained (different mechanism) | **16** (21%) |

## The Theorem

**Theorem (NBL-Cospectral 2-Edge Switch):** Let G be a graph with vertices v₁, v₂, w₁, w₂ such that v₁w₁, v₂w₂ ∈ E(G) and v₁w₂, v₂w₁ ∉ E(G). Define G' by removing {v₁w₁, v₂w₂} and adding {v₁w₂, v₂w₁}.

Then G and G' have the same NBL spectrum if:

**(C1)** deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)

**(C2)** |ext(v₁) ∩ ext(wⱼ)| = |ext(v₂) ∩ ext(wⱼ)| for j = 1, 2

where S = {v₁, v₂, w₁, w₂} and ext(x) = N(x) \ S.

## Key Findings

### Conditions are Minimal
From (C1) and (C2), we automatically derive:
- |unique₁| = |unique₂| (follows from degree equality)
- |ext(vᵢ) ∩ unique₁| = |ext(vᵢ) ∩ unique₂| (follows from pairwise cross equality)

### Proof Technique
The proof uses **aggregate weight matching**:
1. Partition boundary edges by type
2. Define swap σ: w₁ ↔ w₂ 
3. Show transition weights between type classes are σ-invariant
4. Conclude tr(T_G^k) = tr(T_{G'}^k) for all k

### What is NOT Required
- Parallel edges (v₁-v₂ or w₁-w₂)
- Specific shared/unique sizes
- Uniform degrees within unique sets

## The 16 Unexplained Pairs

These pairs are NBL-cospectral but NOT related by any single (C1)+(C2) switch:

```
I?qa`hidg,I?qa`iYXg
I?qa`xjfg,I?qa`yZZg
ICQbfZk{_,ICp`fjk{_
ICQrV`lmg,ICQrVaj^G
ICQvfZk^_,ICRdvY{^_
ICR`v_zzG,ICR`v`lmg
ICRbcz[[o,ICpberiho
ICRcrOxtO,ICdebQsrO
ICRcvZ[jg,ICXefTy\o
ICXevNw~?,ICpfbvk~?
ICZNLzyn_,IEhvFrylo
ICdbFHY^?,ICp`eqey_
ICdbFHY{_,ICp`eqet_
ICpbRd{mO,ICpbUrUho
ICpdbhZnG,ICpdbi\]g
ICrbTs}|_,ICrbfi]}_
```

## Cospectrality Overlap

All 78 NBL-cospectral pairs (min_deg ≥ 2) are also cospectral w.r.t.:
- Adjacency matrix
- Normalized Laplacian
- Non-backtracking (Hashimoto) matrix

This overlap does NOT hold for general NBL-cospectral pairs.

## Key Files

- `docs/complete_self_contained_proof.md` - Full formal proof of (C1)+(C2) theorem
- `docs/nbl_switching_theorem_verification.md` - Computational verification
- `docs/78_pairs.txt` - All 78 pairs (graph6 format)
- `scripts/check_c1c2.py` - Script to verify (C1)+(C2) conditions

## Open Questions

1. What mechanism explains the 16 unexplained pairs?
2. Are (C1)+(C2) necessary as well as sufficient?
3. Why does NBL-cospectrality imply adjacency-cospectrality for min_deg ≥ 2?
