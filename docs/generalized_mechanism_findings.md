# Generalized NBL-Cospectral Switch Theorem

## Summary of Findings

From analyzing all 11 known NBL-cospectral 2-edge switches (min_degree ≥ 2):

### Universal Conditions (hold for ALL 11 switches)

1. **Degree equality**: deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)
2. **Non-empty shared**: |shared| ≥ 1 where shared = ext(w₁) ∩ ext(w₂)
3. **Uniform cross-intersection**: |ext(vᵢ) ∩ ext(wⱼ)| = c for all i,j ∈ {1,2}
4. **Equal unique sizes**: |unique₁| = |unique₂| = 2 where uniqueⱼ = ext(wⱼ) \ ext(w₃₋ⱼ)
5. **Balanced v-edges**: |E(unique₁, {v₁,v₂})| = |E(unique₂, {v₁,v₂})|

### Non-Universal Conditions (from original Mechanism A)

- Both parallel edges exist: 5/11
- |shared| = 2: 5/11  
- Uniform unique degrees: 10/11

### Two Matching Modes

**Elementwise Matching** (10/11 switches): 
The diagonal entries T^k[e,e] at switched edges match one-to-one under the natural bijection σ that swaps w₁↔w₂.

**Pairwise Matching** (1/11 switches - Switch 0):
Individual diagonal entries don't match, but paired sums do:
- T^k[(v₁,w₁),(v₁,w₁)] + T^k[(v₂,w₂),(v₂,w₂)] = T^k[(v₁,w₂),(v₁,w₂)] + T^k[(v₂,w₁),(v₂,w₁)]
- T^k[(w₁,v₁),(w₁,v₁)] + T^k[(w₂,v₂),(w₂,v₂)] = T^k[(w₂,v₁),(w₂,v₁)] + T^k[(w₁,v₂),(w₁,v₂)]

### Key Distinguishing Property

Switch 0 has degs(unique₁) = [4,4] ≠ [5,5] = degs(unique₂).

All other switches have degs(unique₁) = degs(unique₂) as multisets.

## Trace Decomposition

For any k ≥ 1:
```
tr(T_G^k) = Σ_{e ∈ E(G)} T^k[e,e]
          = Σ_{e ∈ common} T^k[e,e] + Σ_{e ∈ switched} T^k[e,e]
```

The common edges contribute identically to both G₁ and G₂.

The switched edges contribute the same total in G₁ and G₂ (verified experimentally for all 11 switches).

## Hypothesis: Generalized Mechanism

**Conjecture**: A double-parallel 2-edge switch produces NBL-cospectral graphs if and only if:
1. deg(v₁) = deg(v₂) and deg(w₁) = deg(w₂)
2. |ext(vᵢ) ∩ ext(wⱼ)| is constant for all i,j
3. |unique₁| = |unique₂|
4. |E(unique₁, {v₁,v₂})| = |E(unique₂, {v₁,v₂})|

The original Mechanism A conditions (|shared|=2, both parallel edges, uniform unique degrees) are SUFFICIENT but not NECESSARY.
