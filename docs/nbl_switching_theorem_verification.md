# NBL Switching Theorem: Computational Verification

## Summary

At n=10 with min_degree ≥ 2, there are **78 NBL-cospectral pairs**.

| Category | Count |
|----------|-------|
| Related by single (C1)+(C2) switch | **62** (79%) |
| NOT related by single switch | **16** (21%) |

The (C1)+(C2) switching theorem explains 62/78 pairs. The remaining 16 require a different mechanism.

## Cospectrality with Other Matrices

All 78 NBL-cospectral pairs (min_deg ≥ 2) are also cospectral w.r.t.:

| Matrix | Cospectral |
|--------|------------|
| Adjacency | 78/78 ✓ |
| Normalized Laplacian | 78/78 ✓ |
| Non-backtracking (Hashimoto) | 78/78 ✓ |

Note: For general NBL-cospectral pairs (without min_degree ≥ 2 constraint), the overlap with adjacency/normalized Laplacian cospectrality is much smaller (~0.2%).

## The 62 Switch-Related Pairs

All satisfy conditions:
- **(C1)**: deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)
- **(C2)**: |ext(v₁) ∩ ext(wⱼ)| = |ext(v₂) ∩ ext(wⱼ)| for j = 1, 2

Run `python scripts/check_c1c2.py` to verify.

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

## Open Questions

1. What mechanism explains the 16 unexplained pairs?
2. Is there a generalization of (C1)+(C2) for k-edge switches (k > 2)?
3. Why are ALL 78 pairs also adjacency-cospectral?

## Technical Notes

### Graph6 Canonicalization
- The database stores graph6 strings from geng (nauty)
- These are NOT necessarily in canonical form (use `shortg -q` to canonicalize)
- However, each graph has a unique graph6 string in the DB
- `nx.is_isomorphic()` correctly identifies isomorphic graphs

### Verification Method
For each pair (G1, G2):
1. Find all valid (C1)+(C2) configurations in G1
2. Apply each switch to get G1'
3. Check if G1' ≅ G2 via `nx.is_isomorphic()`
4. Repeat with G2 → G1

A pair is "switch-related" if any configuration produces an isomorphic result.

See `scripts/check_c1c2.py` for implementation.
