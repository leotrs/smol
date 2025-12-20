#!/usr/bin/env python3
"""
Verify NBL cospectrality directly by comparing eigenvalues.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations

def build_nbl_matrix(G):
    """Build NBL transition matrix."""
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

print("DIRECT EIGENVALUE VERIFICATION")
print("=" * 80)
print()

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    T1, _, _ = build_nbl_matrix(G1)
    T2, _, _ = build_nbl_matrix(G2)
    
    eig1 = np.linalg.eigvals(T1)
    eig2 = np.linalg.eigvals(T2)
    
    # Sort by (real, imag) for comparison
    eig1_sorted = sorted(eig1, key=lambda x: (x.real, x.imag))
    eig2_sorted = sorted(eig2, key=lambda x: (x.real, x.imag))
    
    max_diff = max(abs(e1 - e2) for e1, e2 in zip(eig1_sorted, eig2_sorted))
    
    S = {v1, v2, w1, w2}
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    shared = ext_w1 & ext_w2
    has_v1v2 = G1.has_edge(v1, v2)
    has_w1w2 = G1.has_edge(w1, w2)
    
    status = "✓ COSPECTRAL" if max_diff < 1e-10 else "✗ NOT COSPECTRAL"
    print(f"Switch {idx}: {g6_1}")
    print(f"  |shared|={len(shared)}, parallel=(v1v2:{has_v1v2}, w1w2:{has_w1w2})")
    print(f"  Max eigenvalue diff: {max_diff:.2e}")
    print(f"  {status}")
    print()

conn.close()
