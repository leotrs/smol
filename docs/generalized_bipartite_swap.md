# Generalized Bipartite Swap Theorem

## Summary

We discovered a generalization of the (C1)+(C2) 2-edge switch theorem that may explain some of the unexplained NBL-cospectral pairs.

| Mechanism | Count |
|-----------|-------|
| 2-edge (C1)+(C2) switch | 62 |
| Unexplained | 16 |

## The Bipartite Swap Theorem

**Definition (Bipartite Swap):** Let G have vertices partitioned as:
- H = {h₁, h₂} (hubs)
- L = L₁ ∪ L₂ (leaves)

where in G:
- All l ∈ L₁ are adjacent to h₁ (and not h₂)
- All l ∈ L₂ are adjacent to h₂ (and not h₁)

The *bipartite swap* produces G' by:
- Removing all edges L₁-h₁ and L₂-h₂
- Adding all edges L₁-h₂ and L₂-h₁

**Theorem:** G and G' are NBL-cospectral if:

**(C1')** deg(h₁) = deg(h₂) and all leaves have equal degree

**(C2')** Σ_{l∈L₁} |ext(l) ∩ ext(hⱼ)| = Σ_{l∈L₂} |ext(l) ∩ ext(hⱼ)| for j = 1, 2

**(C3')** |L₁| = |L₂|

where S = L ∪ H and ext(x) = N(x) \ S.

## Relationship to 2-Edge Theorem

The 2-edge (C1)+(C2) theorem is the special case where |L| = 2 and |L₁| = |L₂| = 1:
- L₁ = {v₁}, L₂ = {v₂}, H = {w₁, w₂}
- (C2') becomes: |ext(v₁) ∩ ext(wⱼ)| = |ext(v₂) ∩ ext(wⱼ)| for j = 1, 2

This is exactly condition (C2)!

## Candidate Bipartite Swap Pairs

The following unexplained pairs exhibit a bipartite swap pattern:

| G1 | G2 |
|----|----| 
| I?qa`hidg | I?qa`iYXg |
| I?qa`xjfg | I?qa`yZZg |
| ICQrV`lmg | ICQrVaj^G |
| ICR`v_zzG | ICR`v`lmg |
| ICpdbhZnG | ICpdbi\]g |

These are 4-edge swaps with |L₁| = |L₂| = 2.

## Open Questions

1. Can the bipartite swap theorem be proven rigorously (extending the (C1)+(C2) proof)?
2. Is there a further generalization for k hubs?
3. What explains the remaining unexplained pairs?
