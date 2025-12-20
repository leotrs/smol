# Generalized NBL-Cospectrality Theorems for 2-Edge Switches

## Summary of Findings

From analysis of 11 NBL-cospectral 2-edge switches:

| Mechanism | Count | Key Condition |
|-----------|-------|---------------|
| Generalized Mechanism A | 8 | σ-symmetric first-step matrix P |
| Mechanism B | 3 | Non-σ-symmetric P, higher-order cancellation |

## Mechanism A (Generalized): σ-Symmetric External Dynamics

### Conditions (Relaxed from Original)

For a 2-edge switch on $\{v_1w_1, v_2w_2\} \to \{v_1w_2, v_2w_1\}$:

1. $\deg(v_1) = \deg(v_2)$ and $\deg(w_1) = \deg(w_2)$
2. ~~Both parallel edges~~ (NOT required)
3. ~~$|\text{shared}| = 2$~~ → Relaxed to: $|\text{shared}| \geq 1$
4. Uniform cross-intersection: $|N_{\text{ext}}(v_i) \cap N_{\text{ext}}(w_j)| = c$ for all $i,j$
5. $|\text{unique}_1| = |\text{unique}_2|$
6. ~~Uniform unique degrees~~ → Relaxed to: Degree multisets equal
7. **NEW**: $|E(\text{unique}_1, \text{shared})| = |E(\text{unique}_2, \text{shared})|$
8. **NEW**: $|E(\text{unique}_1)| = |E(\text{unique}_2)|$ (edges within each unique set)

### Key Insight

The critical property is **σ-symmetry of the first-step external matrix** $P$, where:
- $P[\tau, \rho]$ = total transition weight from exit type $\tau$ to entry type $\rho$
- Types: $v_1, v_2, \text{shared}, u_1, u_2$
- Permutation $\sigma$: $v_1 \leftrightarrow v_2$, $u_1 \leftrightarrow u_2$, shared fixed
- σ-symmetry: $P[\tau, \rho] = P[\sigma(\tau), \sigma(\rho)]$

### Switches Satisfying Generalized Mechanism A

| Graph6 | |shared| | Parallel | Degs Uniform |
|--------|---------|----------|--------------|
| I?qadhik_ | 1 | (F,F) | Yes |
| ICQubQxZ_ | 2 | (T,F) | Yes |
| ICQubQxZg | 2 | (T,T) | Yes |
| ICR`ujgMo | 1 | (F,T) | Yes |
| ICR`vGy}? | 1 | (F,F) | Yes |
| ICXmdritW | 2 | (T,T) | Yes |
| ICZLfa{Xw | 2 | (T,T) | Yes |
| ICpfdrdVo | 2 | (T,T) | Yes |

---

## Mechanism B: Non-σ-Symmetric with Higher-Order Cancellation

### The 3 Non-σ-Symmetric Switches

| Graph6 | |shared| | Why Not σ-Symmetric |
|--------|---------|----------------------|
| ICQbeZqz? | 1 | shared→v asymmetric, u→v asymmetric |
| ICQfAxuv? | 1 | shared→v asymmetric, u→v asymmetric |
| ICXmeqsWw | 1 | Degree non-uniform, internal edges differ |

### Analysis of Non-σ-Symmetric Cases

**ICQbeZqz? and ICQfAxuv?:**
- $N_{\text{ext}}(\text{shared}) \cap \{v_1, v_2\} = \{v_2\}$ (asymmetric)
- $N_{\text{ext}}(u_1) \cap \{v_1,v_2\} = N_{\text{ext}}(u_2) \cap \{v_1,v_2\} = \{v_1\}$
- The asymmetries balance: shared connects to v2, unique sets connect to v1

**ICXmeqsWw:**
- $\text{degs}(u_1) = [4,4]$, $\text{degs}(u_2) = [5,5]$
- $|E(\text{unique}_1)| = 0$, $|E(\text{unique}_2)| = 1$
- Both parallel edges exist
- The extra edge in $u_2$ compensates for degree difference

### Why They're Still Cospectral

Despite non-σ-symmetric P, trace analysis shows:
1. For $k \leq 5$: Internal, boundary, and external components match exactly
2. For $k \geq 6$: Small component differences that cancel in total

This suggests **second-order cancellation**: the asymmetry in the first-step matrix is compensated by structure in the external graph.

### Conjectured Mechanism B Conditions

For non-σ-symmetric switches, cospectrality may require:
1. The asymmetries in P are "balanced" (e.g., shared→v1 deficit compensated by u→v1 surplus)
2. The external structure has a specific symmetry that enables cancellation

---

## Universal Necessary Conditions

From all 11 switches:

1. $\deg(v_1) = \deg(v_2)$, $\deg(w_1) = \deg(w_2)$
2. $|\text{shared}| \geq 1$
3. Uniform cross-intersection
4. $|\text{unique}_1| = |\text{unique}_2| = 2$
5. $|E(\text{unique}_1, \{v_1,v_2\})| = |E(\text{unique}_2, \{v_1,v_2\})|$

---

## Next Steps

1. **Prove Generalized Mechanism A**: Adapt the original kernel proof to handle arbitrary |shared|
2. **Characterize Mechanism B**: Find precise conditions for when non-σ-symmetric P still yields cospectrality
3. **Unify**: Determine if there's a single framework encompassing both mechanisms
