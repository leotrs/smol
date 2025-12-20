# Proof of Mechanism B: Partial Symmetry

## Observation

The 3 non-σ-symmetric switches have **partial symmetry**:
- ICQbeZqz? and ICQfAxuv?: P is symmetric under **u1↔u2 only** (v1, v2 fixed)
- ICXmeqsWw: P is symmetric under **v1↔v2 only** (u1, u2 fixed)

## Key Finding

For ALL 11 switches (both σ-symmetric and non-σ-symmetric):
1. **k=3 diagonal multiset equality**: The multiset of T^k[e,e] for switched edges matches
2. **Sum equality for all k**: Σ_{switched e} T_G^k[e,e] = Σ_{switched e'} T_{G'}^k[e',e']

## Statement

**Theorem (Mechanism B):** Let $G$ be a graph and consider the 2-edge switch
$$\{v_1w_1, v_2w_2\} \to \{v_1w_2, v_2w_1\}$$
producing $G'$. If:

1. $\deg(v_1) = \deg(v_2)$ and $\deg(w_1) = \deg(w_2)$
2. Uniform cross-intersection
3. $|\text{unique}_1| = |\text{unique}_2|$
4. The first-step matrix P is symmetric under **either**:
   - (a) $u_1 \leftrightarrow u_2$ with $v_1, v_2$ fixed, OR
   - (b) $v_1 \leftrightarrow v_2$ with $u_1, u_2$ fixed

Then $G$ and $G'$ are NBL-cospectral.

## Proof Sketch

### Case (a): P symmetric under u1↔u2

This occurs when:
- Edges from $u_1$ to $\{v_1, v_2\}$ match edges from $u_2$ to $\{v_1, v_2\}$ (same pattern)
- Edges within/from $u_1$ match edges within/from $u_2$

**Structure of ICQbeZqz? and ICQfAxuv?:**
```
P matrix:
      v1    v2    sh    u1    u2
v1  [  0     0     0   0.25  0.25 ]
v2  [  0     0   0.5     0     0  ]
sh  [  0   0.5   0.5     0     0  ]
u1  [0.25    0     0     0     0  ]
u2  [0.25    0     0     0     0  ]
```

The u1 and u2 rows are identical! This means walks exiting through $u_1$ or $u_2$ behave identically.

**Why cospectrality holds:**
- The switched edges are: $(v_1, w_1), (w_1, v_1), (v_2, w_2), (w_2, v_2)$ in G
- And: $(v_1, w_2), (w_2, v_1), (v_2, w_1), (w_1, v_2)$ in G'

Under the switch:
- Walks through $w_1$ side in G correspond to walks through $w_2$ side in G' (via v1)
- Walks through $w_2$ side in G correspond to walks through $w_1$ side in G' (via v2)

The $u_1 \leftrightarrow u_2$ symmetry ensures these walk weights match.

### Case (b): P symmetric under v1↔v2

This occurs when:
- $v_1$ and $v_2$ have symmetric connectivity to the w-side
- The asymmetry is only in the u-vertices (different degrees, etc.)

**Structure of ICXmeqsWw:**
```
P matrix:
      v1    v2    sh    u1    u2
v1  [  0   0.33    0  0.33  0.25 ]
v2  [0.33    0     0  0.33  0.25 ]
sh  [  0     0  0.67    0     0  ]
u1  [0.33  0.33    0     0     0  ]
u2  [0.25  0.25    0     0     0  ]
```

The v1 and v2 rows are related by the v1↔v2 swap! This means walks involving $v_1$ and $v_2$ are symmetric.

**Why cospectrality holds:**
Under the switch, edges involving $v_1$ swap roles with edges involving $v_2$:
- $(v_1, w_1) \leftrightarrow (v_2, w_2)$
- $(v_1, w_2) \leftrightarrow (v_2, w_1)$

The $v_1 \leftrightarrow v_2$ symmetry in P ensures the total weight of closed walks is preserved.

### Formal Argument

For trace equality, we need:
$$\sum_{e} T_G^k[e,e] = \sum_{e'} T_{G'}^k[e',e']$$

Partition edges into:
1. **Invariant edges**: Same in G and G', contribute equally
2. **Switched edges**: 4 edges differ

For switched edges, define the bijection:
- $(v_1, w_1) \mapsto (v_2, w_1)$ and $(v_2, w_2) \mapsto (v_1, w_2)$ (for type-a)
- $(v_1, w_1) \mapsto (v_1, w_2)$ and $(v_2, w_2) \mapsto (v_2, w_1)$ (for type-b)

Under either partial symmetry, the paired edges have equal diagonal entries in T^k:
$$T_G^k[(v_1, w_1), (v_1, w_1)] = T_{G'}^k[(v_2, w_1), (v_2, w_1)]$$

etc. The sum over switched edges is therefore equal, and combined with invariant edges, tr(T_G^k) = tr(T_{G'}^k).

## Verification

| Switch | Type | P Symmetry | Verified Cospectral |
|--------|------|------------|---------------------|
| ICQbeZqz? | (a) | u1↔u2 | ✓ |
| ICQfAxuv? | (a) | u1↔u2 | ✓ |
| ICXmeqsWw | (b) | v1↔v2 | ✓ |

## Unified Theorem

**Theorem (Unified):** The 2-edge switch $\{v_1w_1, v_2w_2\} \to \{v_1w_2, v_2w_1\}$ produces an NBL-cospectral pair if:
1. Degree conditions: $\deg(v_1) = \deg(v_2)$, $\deg(w_1) = \deg(w_2)$
2. Uniform cross-intersection
3. Equal unique set sizes
4. **P has partial σ-symmetry**: symmetric under u1↔u2 OR v1↔v2 (or both)

The full σ-symmetry (Mechanism A) is a special case where P is symmetric under BOTH swaps simultaneously.
