#!/usr/bin/env python3
"""
Definitive classification of all 11 switches into mechanisms.
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
    ORDER BY g1.graph6
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

print(f"Found {len(switches)} switches (ordered by graph6)")
print("=" * 80)

# Compute properties for each switch
results = []
for g6_1, g6_2, G1, G2, v1, v2, w1, w2 in switches:
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
    
    edges_in_u1 = sum(1 for x in unique_1 for y in unique_1 if x < y and G1.has_edge(x, y))
    edges_in_u2 = sum(1 for x in unique_2 for y in unique_2 if x < y and G1.has_edge(x, y))
    
    edges_u1_shared = sum(1 for x in unique_1 for z in shared if G1.has_edge(x, z))
    edges_u2_shared = sum(1 for y in unique_2 for z in shared if G1.has_edge(y, z))
    
    edges_u1_v1 = sum(1 for x in unique_1 if G1.has_edge(x, v1))
    edges_u1_v2 = sum(1 for x in unique_1 if G1.has_edge(x, v2))
    edges_u2_v1 = sum(1 for y in unique_2 if G1.has_edge(y, v1))
    edges_u2_v2 = sum(1 for y in unique_2 if G1.has_edge(y, v2))
    
    edges_shared_v1 = sum(1 for z in shared if G1.has_edge(z, v1))
    edges_shared_v2 = sum(1 for z in shared if G1.has_edge(z, v2))
    
    # Compute first-step matrix σ-symmetry
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    
    P = defaultdict(lambda: defaultdict(float))
    for s in S:
        ext_s = set(y for y in G1.neighbors(s) if y not in S)
        for x in ext_s:
            exit_edge = (s, x)
            if exit_edge not in e2i1:
                continue
            exit_idx = e2i1[exit_edge]
            
            if s == v1:
                exit_type = 'v1'
            elif s == v2:
                exit_type = 'v2'
            elif s == w1:
                exit_type = 'shared' if x in shared else 'u1'
            elif s == w2:
                exit_type = 'shared' if x in shared else 'u2'
            
            for entry_idx in range(len(edges1)):
                if T1[exit_idx, entry_idx] > 0:
                    entry_edge = edges1[entry_idx]
                    y, t = entry_edge
                    if t not in S:
                        continue
                    
                    if t == v1:
                        entry_type = 'v1'
                    elif t == v2:
                        entry_type = 'v2'
                    elif t == w1:
                        entry_type = 'shared' if y in shared else 'u1'
                    elif t == w2:
                        entry_type = 'shared' if y in shared else 'u2'
                    else:
                        continue
                    
                    P[exit_type][entry_type] += T1[exit_idx, entry_idx]
    
    def sigma(t):
        if t == 'v1': return 'v2'
        if t == 'v2': return 'v1'
        if t == 'shared': return 'shared'
        if t == 'u1': return 'u2'
        if t == 'u2': return 'u1'
    
    types = ['v1', 'v2', 'shared', 'u1', 'u2']
    is_sigma_symmetric = True
    for ft in types:
        for tt in types:
            if abs(P[ft][tt] - P[sigma(ft)][sigma(tt)]) > 1e-10:
                is_sigma_symmetric = False
                break
    
    results.append({
        'g6': g6_1,
        'has_v1v2': has_v1v2,
        'has_w1w2': has_w1w2,
        'shared_size': len(shared),
        'degs_u1': degs_u1,
        'degs_u2': degs_u2,
        'degs_uniform': degs_u1 == degs_u2,
        'edges_in_u_equal': edges_in_u1 == edges_in_u2,
        'edges_to_shared_equal': edges_u1_shared == edges_u2_shared,
        'edges_to_v_pattern': (edges_u1_v1, edges_u1_v2, edges_u2_v1, edges_u2_v2),
        'shared_to_v_equal': edges_shared_v1 == edges_shared_v2,
        'is_sigma_symmetric': is_sigma_symmetric,
    })

# Print classification
print()
print("CLASSIFICATION")
print("=" * 80)
print()

sigma_sym = [r for r in results if r['is_sigma_symmetric']]
non_sym = [r for r in results if not r['is_sigma_symmetric']]

print(f"σ-SYMMETRIC first-step matrix: {len(sigma_sym)} switches")
for r in sigma_sym:
    print(f"  {r['g6']}: |shared|={r['shared_size']}, parallel=({r['has_v1v2']},{r['has_w1w2']}), degs_uniform={r['degs_uniform']}")

print()
print(f"NON-σ-SYMMETRIC first-step matrix: {len(non_sym)} switches")
for r in non_sym:
    print(f"  {r['g6']}: |shared|={r['shared_size']}, parallel=({r['has_v1v2']},{r['has_w1w2']})")
    print(f"    degs: u1={r['degs_u1']}, u2={r['degs_u2']}, uniform={r['degs_uniform']}")
    print(f"    edges_in_u_equal={r['edges_in_u_equal']}, edges_to_shared_equal={r['edges_to_shared_equal']}")
    print(f"    edges_to_v={r['edges_to_v_pattern']}, shared_to_v_equal={r['shared_to_v_equal']}")

# Identify what distinguishes σ-symmetric from non-σ-symmetric
print()
print("=" * 80)
print("KEY DISTINGUISHING FEATURES")
print("=" * 80)
print()

# Check if degs_uniform + edges_in_u_equal + edges_to_shared_equal => σ-symmetric
for r in results:
    predicted_sym = r['degs_uniform'] and r['edges_in_u_equal'] and r['edges_to_shared_equal']
    actual_sym = r['is_sigma_symmetric']
    match = "✓" if predicted_sym == actual_sym else "✗"
    print(f"{r['g6']}: predicted={predicted_sym}, actual={actual_sym} {match}")

conn.close()
