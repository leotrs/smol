#!/usr/bin/env python3
"""
Deep analysis: What makes ALL 11 switches NBL-cospectral?

Key observation from trace analysis:
- All 11 have tr(T1^k) = tr(T2^k) for all k
- But diagonal entries at switched edges may differ

The trace counts closed walks. Let's decompose by whether walks touch S or not.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations
from collections import defaultdict

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

print("COMPREHENSIVE CONDITION ANALYSIS")
print("=" * 80)
print()

# For each switch, compute all potentially relevant conditions
all_conditions = []

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    G = G1  # Work with G1
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    d_v = G.degree(v1)
    d_w = G.degree(w1)
    
    has_v1v2 = G.has_edge(v1, v2)
    has_w1w2 = G.has_edge(w1, w2)
    
    # Cross intersections
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    
    # More detailed: how do unique_i partition by ext(v_j)?
    u1_v1 = unique_1 & ext_v1  # unique_1 vertices adjacent to v1
    u1_v2 = unique_1 & ext_v2  # unique_1 vertices adjacent to v2
    u1_neither = unique_1 - ext_v1 - ext_v2  # unique_1 vertices adjacent to neither
    u1_both = unique_1 & ext_v1 & ext_v2  # unique_1 vertices adjacent to both
    
    u2_v1 = unique_2 & ext_v1
    u2_v2 = unique_2 & ext_v2
    u2_neither = unique_2 - ext_v1 - ext_v2
    u2_both = unique_2 & ext_v1 & ext_v2
    
    # Degrees in unique sets
    degs_u1 = sorted([G.degree(x) for x in unique_1])
    degs_u2 = sorted([G.degree(x) for x in unique_2])
    
    # Edge structure within unique sets
    edges_in_u1 = sum(1 for x in unique_1 for y in unique_1 if x < y and G.has_edge(x, y))
    edges_in_u2 = sum(1 for x in unique_2 for y in unique_2 if x < y and G.has_edge(x, y))
    
    # Edge structure between unique and shared
    edges_u1_sh = sum(1 for x in unique_1 for z in shared if G.has_edge(x, z))
    edges_u2_sh = sum(1 for y in unique_2 for z in shared if G.has_edge(y, z))
    
    # Edge structure between unique sets
    edges_u1_u2 = sum(1 for x in unique_1 for y in unique_2 if G.has_edge(x, y))
    
    # Shared vertex structure
    sh_v1 = shared & ext_v1
    sh_v2 = shared & ext_v2
    sh_both = shared & ext_v1 & ext_v2
    sh_neither = shared - ext_v1 - ext_v2
    
    conds = {
        'idx': idx,
        'g6': g6_1,
        'd_v': d_v,
        'd_w': d_w,
        'has_v1v2': has_v1v2,
        'has_w1w2': has_w1w2,
        'shared_size': len(shared),
        'unique_size': len(unique_1),  # = len(unique_2) by condition 5
        'cross': (c11, c12, c21, c22),
        'uniform_cross': c11 == c12 == c21 == c22,
        
        # Unique partition by v-adjacency
        'u1_v1': len(u1_v1),
        'u1_v2': len(u1_v2),
        'u1_both': len(u1_both),
        'u1_neither': len(u1_neither),
        'u2_v1': len(u2_v1),
        'u2_v2': len(u2_v2),
        'u2_both': len(u2_both),
        'u2_neither': len(u2_neither),
        
        # Symmetry conditions
        'u_to_v_symmetric': (len(u1_v1) == len(u2_v1)) and (len(u1_v2) == len(u2_v2)),
        'u_to_v_twisted': (len(u1_v1) == len(u2_v2)) and (len(u1_v2) == len(u2_v1)),
        'u_both_equal': len(u1_both) == len(u2_both),
        'u_neither_equal': len(u1_neither) == len(u2_neither),
        
        # Degree multisets
        'degs_u1': degs_u1,
        'degs_u2': degs_u2,
        'degs_equal': degs_u1 == degs_u2,
        
        # Edge counts
        'edges_in_u1': edges_in_u1,
        'edges_in_u2': edges_in_u2,
        'edges_within_equal': edges_in_u1 == edges_in_u2,
        'edges_u1_sh': edges_u1_sh,
        'edges_u2_sh': edges_u2_sh,
        'edges_to_sh_equal': edges_u1_sh == edges_u2_sh,
        'edges_u1_u2': edges_u1_u2,
        
        # Shared structure
        'sh_v1': len(sh_v1),
        'sh_v2': len(sh_v2),
        'sh_both': len(sh_both),
        'sh_neither': len(sh_neither),
    }
    
    all_conditions.append(conds)

# Print summary
print("UNIQUE SET PARTITION BY V-ADJACENCY")
print("-" * 60)
print()
print("For each switch: (|u1∩ext(v1)|, |u1∩ext(v2)|, |u2∩ext(v1)|, |u2∩ext(v2)|)")
print()

for c in all_conditions:
    print(f"Switch {c['idx']}: u1->v=({c['u1_v1']},{c['u1_v2']}), u2->v=({c['u2_v1']},{c['u2_v2']}), "
          f"sym={c['u_to_v_symmetric']}, twist={c['u_to_v_twisted']}, "
          f"|shared|={c['shared_size']}, parallel=({c['has_v1v2']},{c['has_w1w2']})")

print()
print("=" * 80)
print("CHECKING SYMMETRY CONDITIONS")
print("=" * 80)
print()

# Find which conditions are universal
conditions_to_check = [
    ('uniform_cross', 'Uniform cross-intersection'),
    ('u_to_v_symmetric', 'u1->v matches u2->v (direct)'),
    ('u_to_v_twisted', 'u1->v matches u2->v (twisted)'),
    ('u_both_equal', '|u1∩both| = |u2∩both|'),
    ('u_neither_equal', '|u1∩neither| = |u2∩neither|'),
    ('degs_equal', 'Degree multisets equal'),
    ('edges_within_equal', 'Edges within unique equal'),
    ('edges_to_sh_equal', 'Edges to shared equal'),
]

for cond_key, cond_name in conditions_to_check:
    count = sum(1 for c in all_conditions if c[cond_key])
    universal = "✓ UNIVERSAL" if count == 11 else ""
    print(f"{cond_name}: {count}/11 {universal}")

# Check combined conditions
print()
print("Combined condition (symmetric OR twisted):")
count = sum(1 for c in all_conditions if c['u_to_v_symmetric'] or c['u_to_v_twisted'])
print(f"  Either symmetric or twisted: {count}/11")

print()
print("=" * 80)
print("SHARED VERTEX ANALYSIS")
print("=" * 80)
print()

for c in all_conditions:
    print(f"Switch {c['idx']}: |shared|={c['shared_size']}, "
          f"sh->v=({c['sh_v1']},{c['sh_v2']}), sh∩both={c['sh_both']}, sh∩neither={c['sh_neither']}")

conn.close()
