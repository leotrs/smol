# NBL Cospectral Pairs Analysis (n=10, min_degree≥2)

**Date:** December 2024

This document tracks the ongoing investigation into the 78 NBL-cospectral pairs with n=10 and min_degree≥2.

## Research Problems

### Problem 1: Characterize Simple 2-Edge Switches (11 pairs)

There are 11 pairs that are simple 2-edge switches. Goal: find conditions X, Y, Z such that:

> **Theorem (Goal):** Under conditions X, Y, Z, a simple 2-edge switch produces an NBL-cospectral graph.

Known sufficient conditions from prior work:
- **Condition B** (N_ext(v₁) = N_ext(v₂) or N_ext(w₁) = N_ext(w₂)): Proven sufficient, but how many of the 11 satisfy it?
- **Condition C** (cross-column equality with sym_diff=2): Proven sufficient for specific cases

**TODO:** Test all 11 simple switches against Conditions B and C. Identify any that satisfy neither.

### Problem 2: Characterize Non-Switch Pairs (67 pairs)

There are 67 pairs that are NOT simple 2-edge switches and NOT cyclic ℓ-switches. Questions:

1. What is the edge-difference distribution? (3, 4, 5, ... edges different)
2. Do any have bipartite vertex structure (V, W partition)?
3. Are any non-cyclic permutation switches?
4. Is there a common structural pattern?

**TODO:** Classify all 67 by edge difference and permutation structure.

## The 78 Pairs

Each line contains two graph6 strings (tab-separated). The first graph is G₁, the second is G₂.

```
ICpdrnw^?	ICdffZk]_
ICXmeqsWw	ICXmeqe[W
I?qbcxwk_	I?ovDd[]?
ICpdlpyz?	ICZTepfy_
ICpdbi{V_	ICpbdh]n?
ICZVBx{xo	ICZJffUyg
ICR`uiwY_	ICdedhkY_
ICR`}rs]_	ICQvepmz?
ICpvTrsN_	ICZelrwN_
I?qabWueo	I?qa`m[Yg
ICZNLzyn_	IEhvFrylo
IEhvEtyZo	IEhuVfwnO
ICXmeqsho	ICXmeqe|?
ICpfRg}fO	ICpfJo|f_
ICXetrcfG	ICZTdXwSw
ICRcvZ[jg	ICXefTy\o
I?otQxefG	I?otQyUZG
ICR`vGy}?	ICR`thi}?
ICZTfZemW	ICZJfpytW
ICQbeZqz?	ICQbUjqz?
ICR`vJWN_	ICR`tjWYo
ICpdbzs]_	ICXedymv?
ICR`vGyu?	ICR`tjWY_
ICrbvh{n_	ICxvFh]n_
ICpvfq{Z_	ICxvFjYN_
ICpfdrdVo	ICpfczd]o
ICp`eqey_	ICdbFHY^?
ICpbtqsx_	ICZbeiYy_
ICZVDX{[o	ICZJerqho
ICp`eqet_	ICdbFHY{_
ICZLfa{Xw	ICZLf_|xg
ICpvRq{xO	ICZbmrwf_
ICXetrSxO	ICZTdXq^?
ICpbew}V_	ICXed^[r_
ICRczrs]_	ICQvfP]z?
ICrbdt{n?	ICY^Fpu^?
ICpbayq]_	ICXedT[r_
I?otQlkcw	I?otQm[Ww
ICpdeWy^?	ICpbUoul_
ICRdvY{^_	ICQvfZk^_
I?qadhik_	I?qa`ngk_
ICR`ujgMo	ICR`tjgUo
ICQubQxZg	ICQubQj^G
ICQbfZk{_	ICp`fjk{_
ICZbvj[n_	IEhvC~i~?
ICrRRc{{O	ICXfUi[{_
ICQrV`lmg	ICQrVaj^G
ICQtepkZ_	ICQrVJWMo
ICpddXY^?	ICXedT[n?
I?qa`xjfg	I?qa`yZZg
ICZnezw[w	ICvfRvs|_
ICQrUZoMo	ICXe`^Wn?
ICpvfZwN_	ICY^Nrw\_
I?qabWydo	I?qa`yUYg
ICQubQxZ_	ICQubQj^?
ICrbfi]}_	ICrbTs}|_
ICpvTrs[o	ICZelrw\O
ICperg{{G	ICXmczoWw
ICZLbvs}?	ICY^Bzq}?
ICRcrOxt?	ICdbFHYN?
ICZJvbsLo	ICY^fbkXo
ICRbcz[[o	ICpberiho
ICQfAxuv?	ICQeRhuv?
ICpfbg}v?	ICrbcx{{_
ICXmdritW	ICXmdrbvG
ICpdbi\]g	ICpdbhZnG
ICpbUrUho	ICpbRd{mO
ICxvBt{ug	IEhuVfwlg
I?qa`hidg	I?qa`iYXg
ICR`v`lmg	ICR`v_zzG
ICpdbj[N_	ICXedrMn?
ICQfAZ[\_	ICQeRHuv?
ICZVBzk\g	ICZJffYxg
ICrbdxy^?	ICZLfpu|?
ICpdew}^?	ICXedzMn?
ICpdvPu^?	ICZJfRqdo
ICRcrOxtO	ICdebQsrO
ICpfbvk~?	ICXevNw~?
```

## Classification Results

### Edge Difference Distribution

| Edge diff | Count | % of 78 |
|-----------|-------|---------|
| 2 | 11 | 14.1% |
| 3 | 4 | 5.1% |
| 4 | 11 | 14.1% |
| 5 | 7 | 9.0% |
| 6 | 15 | 19.2% |
| 7 | 13 | 16.7% |
| 8 | 10 | 12.8% |
| 9 | 5 | 6.4% |
| 10 | 2 | 2.6% |

### Simple 2-Edge Switches (11 pairs)

| # | G₁ | G₂ | Condition B? | Condition C? | Notes |
|---|----|----|--------------|--------------|-------|
| | | | | | |

*(TODO: Test all 11 against conditions B and C)*

### Non-Switch Pairs (67 pairs) - Permutation Analysis

**Key Finding: Non-cyclic permutations explain almost nothing.**

| Category | Count | % of 67 |
|----------|-------|---------|
| Has V-W bipartite structure | 12 | 17.9% |
| — Cyclic (single cycle) | 9 | 13.4% |
| — Non-cyclic (multiple cycles) | 3 | 4.5% |
| **NO V-W bipartite structure** | **55** | **82.1%** |

Cycle type distribution among the 12 with structure:
- `[2]` (transposition): 9 cases (all with 4-edge diff)
- `[2+1]`: 2 cases
- `[3+1]`: 1 case

**Conclusion:** The 55 pairs (82%) with no V-W bipartite structure cannot be explained by ANY permutation-based switch theorem. Their edge differences involve vertices that share edges in a non-bipartite pattern.

#### Detailed breakdown by edge difference:

| Edge diff | Total | Has V-W structure | No structure |
|-----------|-------|-------------------|--------------|
| 3 | 4 | 0 | 4 |
| 4 | 11 | 10 | 1 |
| 5 | 7 | 2 | 5 |
| 6 | 15 | 0 | 15 |
| 7 | 13 | 0 | 13 |
| 8 | 10 | 0 | 10 |
| 9 | 5 | 0 | 5 |
| 10 | 2 | 0 | 2 |

## Key Finding: Hashimoto-Preserving Directed Edge Permutations

### The Question

Instead of thinking about permutations on vertices (V-W bipartite structure), consider permutations on **directed edges** in the Hashimoto graph.

For NBL-cospectral pairs G₁, G₂:
- Let DE₁, DE₂ be the directed edge sets
- Let only₁ = DE₁ - DE₂, only₂ = DE₂ - DE₁ (differing directed edges)
- Is there a bijection σ: only₁ → only₂ that preserves Hashimoto adjacency?

### Results

| Edge diff | Pairs | Has Hashimoto-preserving σ |
|-----------|-------|---------------------------|
| 2 | 11 | **11 (100%)** |
| 3 | 4 | 0 |
| 4 | 11 | 0 |
| 5+ | 52 | not checked (too large) |

**All 11 two-edge switches have a Hashimoto-preserving permutation.**

**None of the 3-edge or 4-edge cases have such a permutation.**

### Structure of the Permutation (2-edge case)

For a 2-edge switch {v₁-w₁, v₂-w₂} → {v₁-w₂, v₂-w₁}, the permutation σ swaps:
- (v₁, w₁) ↔ (v₂, w₁)
- (v₁, w₂) ↔ (v₂, w₂)
- (w₁, v₁) ↔ (w₁, v₂)
- (w₂, v₁) ↔ (w₂, v₂)

This is equivalent to swapping v₁ ↔ v₂ as sources/targets among the differing edges.

### Key Discovery: Spectral Coincidence, NOT Isomorphism

**Theorem (Empirical):** For all 11 two-edge switch pairs:
1. The Hashimoto graphs H(G₁) and H(G₂) are **NOT isomorphic**
2. Yet the NBL matrices are **cospectral**

This is verified by:
- Running NetworkX digraph isomorphism check: all 11 return False
- Computing NBL eigenvalues: all 11 match to machine precision

**Conclusion:** Two-edge switches achieve NBL-cospectrality via **spectral coincidence** (non-isomorphic matrices with same spectrum), NOT via Hashimoto isomorphism.

This is fundamentally different from "Condition B" (external neighborhood equality), which produces Hashimoto isomorphism.

### Two Mechanisms for NBL-Cospectrality

| Mechanism | Hashimoto graphs | Example |
|-----------|------------------|---------|
| **Condition B** (N_ext equality) | H(G₁) ≅ H(G₂) | Isomorphism implies cospectrality |
| **Spectral Coincidence** | H(G₁) ≇ H(G₂) | Non-isomorphic but same eigenvalues |

All 11 two-edge switches in our dataset use the **spectral coincidence** mechanism.

### The Open Question

What algebraic condition on a 2-edge switch guarantees spectral coincidence?

We know:
- deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂) (necessary for same edge count)
- External neighborhoods are preserved (switching doesn't change N_ext)
- Condition B is NOT satisfied (N_ext(v₁) ≠ N_ext(v₂) and N_ext(w₁) ≠ N_ext(w₂))
- Yet cospectrality still holds

### Proof Attempt

The NBL transition matrix T acts on directed edges. Under a 2-edge switch:
- 4 directed edges are removed: (v₁,w₁), (w₁,v₁), (v₂,w₂), (w₂,v₂)
- 4 directed edges are added: (v₁,w₂), (w₂,v₁), (v₂,w₁), (w₁,v₂)

The perturbation ΔT = T₂ - T₁ is a sparse matrix affecting only rows/columns related to these edges.

**Key observation from earlier work:** The T^k rows for switch edges have equal multisets for k=1,2 but diverge at k≥3.

*(Further analysis needed)*

## The 11 Two-Edge Switch Pairs

```
Pair 1:  ICpdrnw^?    ICdffZk]_
Pair 2:  ICXmeqsWw    ICXmeqe[W
Pair 3:  I?qbcxwk_    I?ovDd[]?
Pair 4:  ICpdlpyz?    ICZTepfy_
Pair 5:  ICpdbi{V_    ICpbdh]n?
Pair 6:  ICZVBx{xo    ICZJffUyg
Pair 7:  ICR`uiwY_    ICdedhkY_
Pair 8:  ICR`}rs]_    ICQvepmz?
Pair 9:  ICpvTrsN_    ICZelrwN_
Pair 10: I?qabWueo    I?qa`m[Yg
Pair 11: ICZNLzyn_    IEhvFrylo
```

*(Need to verify these are the actual 2-edge pairs)*

## Notes

*(Running notes as investigation proceeds)*
