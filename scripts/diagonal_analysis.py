#!/usr/bin/env python3
"""
Analyze the diagonal entries of T^k at ALL directed edges to understand
how the cospectrality works.

Key insight: The sum of diagonal entries at positions corresponding to
swapped edges must be equal between G1 and G2.
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

print("DIAGONAL ENTRY ANALYSIS FOR SWITCHED EDGES")
print("=" * 80)
print()

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    # Switched edges
    sw1 = [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]
    sw2 = [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]
    
    idx_sw1 = [e2i1[e] for e in sw1]
    idx_sw2 = [e2i2[e] for e in sw2]
    
    S = {v1, v2, w1, w2}
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    shared = ext_w1 & ext_w2
    has_v1v2 = G1.has_edge(v1, v2)
    has_w1w2 = G1.has_edge(w1, w2)
    
    print(f"Switch {idx}: |shared|={len(shared)}, parallel=(v1v2:{has_v1v2}, w1w2:{has_w1w2})")
    
    # Compute diagonal entries for k = 3..6
    Tk1 = T1 @ T1 @ T1
    Tk2 = T2 @ T2 @ T2
    
    for k in range(3, 7):
        diag1 = [Tk1[i, i] for i in idx_sw1]
        diag2 = [Tk2[i, i] for i in idx_sw2]
        
        # Check if diagonals match elementwise
        elem_match = all(abs(d1 - d2) < 1e-10 for d1, d2 in zip(diag1, diag2))
        
        # Check if sum matches
        sum1 = sum(diag1)
        sum2 = sum(diag2)
        sum_match = abs(sum1 - sum2) < 1e-10
        
        # Check if pairs match: (v1,w1)+(v2,w2) vs (v1,w2)+(v2,w1)
        pair1_sum1 = diag1[0] + diag1[2]  # (v1,w1) + (v2,w2)
        pair1_sum2 = diag2[0] + diag2[2]  # (v1,w2) + (v2,w1)
        pair2_sum1 = diag1[1] + diag1[3]  # (w1,v1) + (w2,v2)
        pair2_sum2 = diag2[1] + diag2[3]  # (w2,v1) + (w1,v2)
        
        pair_match = abs(pair1_sum1 - pair1_sum2) < 1e-10 and abs(pair2_sum1 - pair2_sum2) < 1e-10
        
        status = "elem✓" if elem_match else ("pair✓" if pair_match else ("sum✓" if sum_match else "✗"))
        print(f"  k={k}: {status}")
        if not elem_match and k <= 4:
            print(f"       G1: {[f'{d:.6f}' for d in diag1]}")
            print(f"       G2: {[f'{d:.6f}' for d in diag2]}")
        
        Tk1 = Tk1 @ T1
        Tk2 = Tk2 @ T2
    
    print()

# Now let's look at the FULL diagonal comparison
print("=" * 80)
print("FULL TRACE DECOMPOSITION")
print("=" * 80)
print()

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches[:3]):  # Just first 3
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    # Find common edges (not switched)
    common_edges = set(edges1) & set(edges2)
    only_G1 = set(edges1) - set(edges2)
    only_G2 = set(edges2) - set(edges1)
    
    print(f"Switch {idx}:")
    print(f"  Total directed edges: {len(edges1)}")
    print(f"  Common edges: {len(common_edges)}")
    print(f"  G1-only edges: {only_G1}")
    print(f"  G2-only edges: {only_G2}")
    
    # Compute traces decomposed by edge type
    Tk1 = T1 @ T1 @ T1
    Tk2 = T2 @ T2 @ T2
    
    for k in range(3, 6):
        tr1 = np.trace(Tk1)
        tr2 = np.trace(Tk2)
        
        # Trace from common edges
        tr1_common = sum(Tk1[e2i1[e], e2i1[e]] for e in common_edges)
        tr2_common = sum(Tk2[e2i2[e], e2i2[e]] for e in common_edges)
        
        # Trace from G1-only edges
        tr1_only = sum(Tk1[e2i1[e], e2i1[e]] for e in only_G1)
        
        # Trace from G2-only edges
        tr2_only = sum(Tk2[e2i2[e], e2i2[e]] for e in only_G2)
        
        print(f"  k={k}:")
        print(f"    tr(T1^k) = {tr1:.6f}, tr(T2^k) = {tr2:.6f}, diff = {abs(tr1-tr2):.2e}")
        print(f"    Common contribution: G1={tr1_common:.6f}, G2={tr2_common:.6f}, diff={abs(tr1_common-tr2_common):.2e}")
        print(f"    Switched contribution: G1={tr1_only:.6f}, G2={tr2_only:.6f}")
        
        Tk1 = Tk1 @ T1
        Tk2 = Tk2 @ T2
    
    print()

conn.close()
