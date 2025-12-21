#!/usr/bin/env python3
"""
Develop the generalized proof for NBL-cospectral 2-edge switches.

THEOREM (Generalized): A double-parallel 2-edge switch {v1-w1, v2-w2} → {v1-w2, v2-w1} 
produces NBL-cospectral graphs if:
  (C1) deg(v1) = deg(v2) and deg(w1) = deg(w2)
  (C2) |ext(vi) ∩ ext(wj)| = c for all i,j ∈ {1,2} (uniform cross-intersection)

These two conditions are SUFFICIENT and appear to be the MINIMAL necessary conditions.

PROOF APPROACH:
We show tr(T_G^k) = tr(T_{G'}^k) for all k ≥ 1 by partitioning closed walks
into equivalence classes with matching total weights.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations

def build_nbl_matrix(G):
    edges = [(u, v) for u, v in G.edges()] + [(v, u) for u, v in G.edges()]
    edge_to_idx = {e: i for i, e in enumerate(edges)}
    n = len(edges)
    T = np.zeros((n, n))
    
    for i, (u, v) in enumerate(edges):
        deg_v = G.degree(v)
        if deg_v > 1:
            for w in G.neighbors(v):
                if w != u:
                    j = edge_to_idx[(v, w)]
                    T[i, j] = 1.0 / (deg_v - 1)
    
    return T, edges, edge_to_idx

conn = psycopg2.connect('dbname=smol')
cur = conn.cursor()
cur.execute('''
    SELECT g1.graph6, g2.graph6
    FROM cospectral_mates cm
    JOIN graphs g1 ON cm.graph1_id = g1.id
    JOIN graphs g2 ON cm.graph2_id = g2.id
    WHERE cm.matrix_type = 'nbl'
      AND g1.min_degree >= 2
      AND g2.min_degree >= 2
''')
pairs = cur.fetchall()

switches = []
for g6_1, g6_2 in pairs:
    G1 = nx.from_graph6_bytes(g6_1.encode())
    G2 = nx.from_graph6_bytes(g6_2.encode())
    E1 = set(frozenset(e) for e in G1.edges())
    E2 = set(frozenset(e) for e in G2.edges())
    only_in_G1 = E1 - E2
    only_in_G2 = E2 - E1
    
    if len(only_in_G1) != 2:
        continue
    
    verts = set()
    for e in only_in_G1 | only_in_G2:
        verts.update(e)
    
    if len(verts) != 4:
        continue
    
    for perm in permutations(verts):
        v1, v2, w1, w2 = perm
        e1 = frozenset([v1, w1])
        e2 = frozenset([v2, w2])
        new_e1 = frozenset([v1, w2])
        new_e2 = frozenset([v2, w1])
        
        if only_in_G1 == {e1, e2} and only_in_G2 == {new_e1, new_e2}:
            if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                switches.append((g6_1, g6_2, G1, G2, v1, v2, w1, w2))
                break

print("GENERALIZED NBL-COSPECTRAL SWITCH THEOREM")
print("=" * 80)
print()

# Define boundary types for the generalized case
# The key insight: we partition external neighbors by their relationship to v1, v2

def analyze_boundary_types(G, v1, v2, w1, w2):
    """
    Partition external vertices into types based on adjacency pattern.
    """
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # Further partition by v-adjacency
    # For unique_1 and unique_2:
    u1_in_v1 = unique_1 & ext_v1
    u1_in_v2 = unique_1 & ext_v2
    u1_both = unique_1 & ext_v1 & ext_v2
    u1_neither = unique_1 - ext_v1 - ext_v2
    
    u2_in_v1 = unique_2 & ext_v1
    u2_in_v2 = unique_2 & ext_v2
    u2_both = unique_2 & ext_v1 & ext_v2
    u2_neither = unique_2 - ext_v1 - ext_v2
    
    # For shared:
    sh_in_v1 = shared & ext_v1 - ext_v2
    sh_in_v2 = shared & ext_v2 - ext_v1
    sh_both = shared & ext_v1 & ext_v2
    sh_neither = shared - ext_v1 - ext_v2
    
    return {
        'shared': shared, 'unique_1': unique_1, 'unique_2': unique_2,
        'u1_in_v1': u1_in_v1, 'u1_in_v2': u1_in_v2, 'u1_both': u1_both, 'u1_neither': u1_neither,
        'u2_in_v1': u2_in_v1, 'u2_in_v2': u2_in_v2, 'u2_both': u2_both, 'u2_neither': u2_neither,
        'sh_in_v1': sh_in_v1, 'sh_in_v2': sh_in_v2, 'sh_both': sh_both, 'sh_neither': sh_neither,
    }

# Analyze all switches
print("BOUNDARY TYPE ANALYSIS")
print("-" * 60)
print()

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    bt = analyze_boundary_types(G1, v1, v2, w1, w2)
    
    # Cross-intersection value
    S = {v1, v2, w1, w2}
    c = len(set(x for x in G1.neighbors(v1) if x not in S) & 
            set(x for x in G1.neighbors(w1) if x not in S))
    
    # Verify uniform cross
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    
    uniform = (c11 == c12 == c21 == c22)
    
    print(f"Switch {idx}: cross=({c11},{c12},{c21},{c22}) uniform={uniform}")
    print(f"  |shared|={len(bt['shared'])}, |unique_1|={len(bt['unique_1'])}, |unique_2|={len(bt['unique_2'])}")
    print(f"  u1 partition: v1={len(bt['u1_in_v1'])}, v2={len(bt['u1_in_v2'])}, both={len(bt['u1_both'])}, neither={len(bt['u1_neither'])}")
    print(f"  u2 partition: v1={len(bt['u2_in_v1'])}, v2={len(bt['u2_in_v2'])}, both={len(bt['u2_both'])}, neither={len(bt['u2_neither'])}")
    
    # Key symmetry: |u1_in_v1| = |u2_in_v1| and |u1_in_v2| = |u2_in_v2| (from uniform cross)
    sym1 = len(bt['u1_in_v1']) == len(bt['u2_in_v1'])
    sym2 = len(bt['u1_in_v2']) == len(bt['u2_in_v2'])
    print(f"  Symmetry: |u1∩v1|=|u2∩v1|? {sym1}, |u1∩v2|=|u2∩v2|? {sym2}")
    print()

# Now let's define the swap operation on walks
print("=" * 80)
print("THE SWAP BIJECTION")
print("=" * 80)
print()

print("""
For a closed walk W in G1, define swap(W) as follows:

1. If W doesn't use any switched edges, W is unchanged in G2.

2. If W uses switched edges, we apply the transformation:
   - Replace (v1, w1) with (v1, w2)
   - Replace (w1, v1) with (w2, v1)
   - Replace (v2, w2) with (v2, w1)
   - Replace (w2, v2) with (w1, v2)

The key insight is that this transformation:
- Maps closed walks in G1 to closed walks in G2
- Preserves walk weight when uniform cross-intersection holds

WHY does weight preservation hold?

The weight of a walk step (u,v) → (v,w) is 1/(deg(v)-1).
- Steps not involving S have identical weights in G1 and G2.
- Steps at v1, v2 have the same weight (deg(v1) = deg(v2)).
- Steps at w1, w2 have the same weight (deg(w1) = deg(w2)).

The tricky part is the TRANSITION STRUCTURE:
- In G1: from (x, w1) we can go to (w1, v1), (w1, v2), or (w1, y) for y ∈ ext(w1) \\ {x}
- In G2: from (x, w2) we can go to (w2, v1), (w2, v2), or (w2, y) for y ∈ ext(w2) \\ {x}

For the swap to preserve closed walk counts, we need the SETS of possible next states
to be "isomorphic" under the swap.
""")

# Verify: do the transition structures match under swap?
print("=" * 80)
print("TRANSITION STRUCTURE VERIFICATION")
print("=" * 80)
print()

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    # Compare: row of (v1,w1) in G1 vs row of (v1,w2) in G2
    # These should have the same structure after relabeling
    
    e1_G1 = (v1, w1)
    e1_G2 = (v1, w2)  # The corresponding edge after switch
    
    i1 = e2i1[e1_G1]
    i2 = e2i2[e1_G2]
    
    # Get non-zero entries
    row1 = [(edges1[j], T1[i1, j]) for j in range(len(edges1)) if T1[i1, j] > 0]
    row2 = [(edges2[j], T2[i2, j]) for j in range(len(edges2)) if T2[i2, j] > 0]
    
    # The entries should be:
    # G1 from (v1,w1): to (w1, x) for x ∈ N(w1) \ {v1}
    # G2 from (v1,w2): to (w2, x) for x ∈ N(w2) \ {v1}
    
    # Extract targets
    targets1 = set(e[1] for e, w in row1)
    targets2 = set(e[1] for e, w in row2)
    
    S = {v1, v2, w1, w2}
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    
    # In G1, from (v1,w1) we go to targets in {v2} ∪ ext(w1) (if w1-w2 edge) ∪ more
    # In G2, from (v1,w2) we go to targets in {v2} ∪ ext(w2) (if w1-w2 edge) ∪ more
    
    print(f"Switch {idx}:")
    print(f"  From (v1,w1) in G1: targets = {targets1}")
    print(f"  From (v1,w2) in G2: targets = {targets2}")
    print(f"  ext(w1) = {ext_w1}")
    print(f"  ext(w2) = {ext_w2}")
    print(f"  |targets1| = {len(targets1)}, |targets2| = {len(targets2)}")
    print()

conn.close()
