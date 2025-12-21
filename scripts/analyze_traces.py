#!/usr/bin/env python3
"""
Analyze trace contributions to understand the mechanism behind NBL-cospectrality.
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

print("TRACE ANALYSIS FOR ALL 11 SWITCHES")
print("=" * 80)
print()

# Focus on a few switches with different characteristics
interesting_switches = [
    (0, "Both parallel, |shared|=1, degs unequal"),
    (1, "No parallel, |shared|=1"),
    (3, "MECHANISM A"),
    (8, "One parallel (v1v2), |shared|=2"),
]

for idx, desc in interesting_switches:
    g6_1, g6_2, G1, G2, v1, v2, w1, w2 = switches[idx]
    
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    print(f"Switch {idx}: {desc}")
    print(f"  G1: {g6_1}")
    print(f"  G2: {g6_2}")
    
    # Compute traces for k = 3 to 10
    traces1 = []
    traces2 = []
    Tk1 = T1.copy()
    Tk2 = T2.copy()
    for k in range(1, 11):
        tr1 = np.trace(Tk1)
        tr2 = np.trace(Tk2)
        traces1.append(tr1)
        traces2.append(tr2)
        Tk1 = Tk1 @ T1
        Tk2 = Tk2 @ T2
    
    print("  Traces (k=1..10):")
    for k in range(1, 11):
        tr1 = traces1[k-1]
        tr2 = traces2[k-1]
        diff = abs(tr1 - tr2)
        match = "✓" if diff < 1e-10 else "✗"
        print(f"    k={k}: tr(T1^k)={tr1:.6f}, tr(T2^k)={tr2:.6f}, diff={diff:.2e} {match}")
    
    # Analyze the switched edges contribution
    S = {v1, v2, w1, w2}
    switched_edges_G1 = [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]
    switched_edges_G2 = [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]
    
    # Get indices of switched edges
    idx_sw_G1 = [e2i1[e] for e in switched_edges_G1]
    idx_sw_G2 = [e2i2[e] for e in switched_edges_G2]
    
    print(f"  Switched edges in G1: {switched_edges_G1}")
    print(f"  Switched edges in G2: {switched_edges_G2}")
    
    # Look at diagonal entries (contribute to trace)
    print("  Diagonal entries at switched edge indices:")
    Tk1 = T1.copy()
    Tk2 = T2.copy()
    for k in range(1, 6):
        diag1 = [Tk1[i, i] for i in idx_sw_G1]
        diag2 = [Tk2[i, i] for i in idx_sw_G2]
        print(f"    k={k}: G1 diag={[f'{d:.4f}' for d in diag1]}, G2 diag={[f'{d:.4f}' for d in diag2]}")
        Tk1 = Tk1 @ T1
        Tk2 = Tk2 @ T2
    
    print()

# Now let's check: do the rows of T at switched edges have some symmetry?
print("=" * 80)
print("ROW/COLUMN STRUCTURE AT SWITCHED EDGES")
print("=" * 80)
print()

for idx, desc in interesting_switches:
    g6_1, g6_2, G1, G2, v1, v2, w1, w2 = switches[idx]
    
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    print(f"Switch {idx}: {desc}")
    
    # Row sums at switched edges
    sw1 = [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]
    sw2 = [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]
    
    print("  Row sums in G1 at switched edges:")
    for e in sw1:
        i = e2i1[e]
        print(f"    {e}: row sum = {T1[i].sum():.4f}")
    
    print("  Row sums in G2 at switched edges:")
    for e in sw2:
        i = e2i2[e]
        print(f"    {e}: row sum = {T2[i].sum():.4f}")
    
    # Compare specific entries
    print("  Entry analysis:")
    # In G1: (v1,w1) can go to (w1, x) for x in N(w1)\{v1}
    # In G2: (v1,w2) can go to (w2, x) for x in N(w2)\{v1}
    
    e_v1w1 = (v1, w1)
    e_v1w2 = (v1, w2)
    
    if e_v1w1 in e2i1 and e_v1w2 in e2i2:
        i1 = e2i1[e_v1w1]
        i2 = e2i2[e_v1w2]
        
        # Non-zero entries in these rows
        nz1 = [(edges1[j], T1[i1, j]) for j in range(len(edges1)) if T1[i1, j] > 0]
        nz2 = [(edges2[j], T2[i2, j]) for j in range(len(edges2)) if T2[i2, j] > 0]
        
        print(f"    From (v1,w1) in G1: {nz1}")
        print(f"    From (v1,w2) in G2: {nz2}")
    
    print()

conn.close()
