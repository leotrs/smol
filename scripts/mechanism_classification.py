#!/usr/bin/env python3
"""
Investigate what distinguishes elementwise vs pairwise diagonal matching.
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

print("MECHANISM CLASSIFICATION")
print("=" * 80)
print()

# Classify each switch
elem_match_switches = []
pair_match_switches = []

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    sw1 = [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]
    sw2 = [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]
    idx_sw1 = [e2i1[e] for e in sw1]
    idx_sw2 = [e2i2[e] for e in sw2]
    
    # Check at k=3
    Tk1 = T1 @ T1 @ T1
    Tk2 = T2 @ T2 @ T2
    
    diag1 = [Tk1[i, i] for i in idx_sw1]
    diag2 = [Tk2[i, i] for i in idx_sw2]
    
    elem_match = all(abs(d1 - d2) < 1e-10 for d1, d2 in zip(diag1, diag2))
    
    if elem_match:
        elem_match_switches.append(idx)
    else:
        pair_match_switches.append(idx)

print(f"Elementwise matching (at k=3): {elem_match_switches}")
print(f"Pair matching only: {pair_match_switches}")
print()

# Analyze what's special about pair-match-only switches
print("=" * 80)
print("ANALYSIS OF PAIR-MATCH-ONLY SWITCHES")
print("=" * 80)
print()

for idx in pair_match_switches:
    g6_1, g6_2, G1, G2, v1, v2, w1, w2 = switches[idx]
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    has_v1v2 = G1.has_edge(v1, v2)
    has_w1w2 = G1.has_edge(w1, w2)
    
    degs_u1 = sorted([G1.degree(x) for x in unique_1])
    degs_u2 = sorted([G1.degree(x) for x in unique_2])
    
    # Additional structure
    edges_u1_u2 = sum(1 for x in unique_1 for y in unique_2 if G1.has_edge(x, y))
    edges_in_u1 = sum(1 for x in unique_1 for y in unique_1 if x < y and G1.has_edge(x, y))
    edges_in_u2 = sum(1 for x in unique_2 for y in unique_2 if x < y and G1.has_edge(x, y))
    
    edges_u1_shared = sum(1 for x in unique_1 for z in shared if G1.has_edge(x, z))
    edges_u2_shared = sum(1 for y in unique_2 for z in shared if G1.has_edge(y, z))
    
    print(f"Switch {idx}: {g6_1}")
    print(f"  Parallel: v1v2={has_v1v2}, w1w2={has_w1w2}")
    print(f"  |shared|={len(shared)}")
    print(f"  Degrees: d_v={G1.degree(v1)}, d_w={G1.degree(w1)}")
    print(f"  degs_u1={degs_u1}, degs_u2={degs_u2}, EQUAL={degs_u1==degs_u2}")
    print(f"  edges_u1<->u2={edges_u1_u2}")
    print(f"  edges within: u1={edges_in_u1}, u2={edges_in_u2}, EQUAL={edges_in_u1==edges_in_u2}")
    print(f"  edges to shared: u1={edges_u1_shared}, u2={edges_u2_shared}, EQUAL={edges_u1_shared==edges_u2_shared}")
    print()

print("=" * 80)
print("ANALYSIS OF ELEMENTWISE MATCHING SWITCHES")
print("=" * 80)
print()

for idx in elem_match_switches:
    g6_1, g6_2, G1, G2, v1, v2, w1, w2 = switches[idx]
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    has_v1v2 = G1.has_edge(v1, v2)
    has_w1w2 = G1.has_edge(w1, w2)
    
    degs_u1 = sorted([G1.degree(x) for x in unique_1])
    degs_u2 = sorted([G1.degree(x) for x in unique_2])
    
    edges_u1_u2 = sum(1 for x in unique_1 for y in unique_2 if G1.has_edge(x, y))
    edges_in_u1 = sum(1 for x in unique_1 for y in unique_1 if x < y and G1.has_edge(x, y))
    edges_in_u2 = sum(1 for x in unique_2 for y in unique_2 if x < y and G1.has_edge(x, y))
    
    edges_u1_shared = sum(1 for x in unique_1 for z in shared if G1.has_edge(x, z))
    edges_u2_shared = sum(1 for y in unique_2 for z in shared if G1.has_edge(y, z))
    
    print(f"Switch {idx}: {g6_1}")
    print(f"  Parallel: v1v2={has_v1v2}, w1w2={has_w1w2}")
    print(f"  |shared|={len(shared)}")
    print(f"  Degrees: d_v={G1.degree(v1)}, d_w={G1.degree(w1)}")
    print(f"  degs_u1={degs_u1}, degs_u2={degs_u2}, EQUAL={degs_u1==degs_u2}")
    print(f"  edges_u1<->u2={edges_u1_u2}")
    print(f"  edges within: u1={edges_in_u1}, u2={edges_in_u2}, EQUAL={edges_in_u1==edges_in_u2}")
    print(f"  edges to shared: u1={edges_u1_shared}, u2={edges_u2_shared}, EQUAL={edges_u1_shared==edges_u2_shared}")
    print()

conn.close()
