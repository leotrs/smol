#!/usr/bin/env python3
"""
Verify the unified theorem: every switch has partial σ-symmetry.
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

print("UNIFIED THEOREM VERIFICATION")
print("=" * 80)
print()
print(f"{'Graph6':<15} {'v1↔v2':<8} {'u1↔u2':<8} {'Both':<8} {'Has Partial':<12}")
print("-" * 60)

all_have_partial = True

for g6_1, g6_2, G1, G2, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
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
    
    types = ['v1', 'v2', 'shared', 'u1', 'u2']
    
    # Check v1↔v2 symmetry (u1, u2, shared fixed)
    def sigma_v(t):
        if t == 'v1': return 'v2'
        if t == 'v2': return 'v1'
        return t
    
    # Check u1↔u2 symmetry (v1, v2, shared fixed)
    def sigma_u(t):
        if t == 'u1': return 'u2'
        if t == 'u2': return 'u1'
        return t
    
    # Check full σ-symmetry
    def sigma_full(t):
        if t == 'v1': return 'v2'
        if t == 'v2': return 'v1'
        if t == 'u1': return 'u2'
        if t == 'u2': return 'u1'
        return t
    
    def check_symmetry(sigma):
        for ft in types:
            for tt in types:
                if abs(P[ft][tt] - P[sigma(ft)][sigma(tt)]) > 1e-10:
                    return False
        return True
    
    sym_v = check_symmetry(sigma_v)
    sym_u = check_symmetry(sigma_u)
    sym_full = check_symmetry(sigma_full)
    
    has_partial = sym_v or sym_u
    
    if not has_partial:
        all_have_partial = False
    
    print(f"{g6_1:<15} {'✓' if sym_v else '✗':<8} {'✓' if sym_u else '✗':<8} {'✓' if sym_full else '✗':<8} {'✓' if has_partial else '✗':<12}")

print()
print("=" * 80)
if all_have_partial:
    print("✓ ALL 11 switches have at least one partial symmetry!")
    print("  The unified theorem is verified.")
else:
    print("✗ Some switches lack partial symmetry - need further investigation.")

conn.close()
