#!/usr/bin/env python3
"""
Analyze the perturbation matrix ΔT = T_{G'} - T_G for Mechanism B switches.
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

# Focus on Mechanism B switches
mech_b_g6 = ['ICQbeZqz?', 'ICQfAxuv?', 'ICXmeqsWw']

print("PERTURBATION ANALYSIS")
print("=" * 80)
print()

for g6_1, g6_2, G1, G2, v1, v2, w1, w2 in switches:
    if g6_1 not in mech_b_g6:
        continue
    
    print(f"Switch: {g6_1}")
    
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    # Both graphs have same directed edges in same order (only undirected edges differ)
    # But the edge ordering might be different... let me check
    
    # The edges that change:
    # G1: v1-w1, v2-w2 (directed: (v1,w1), (w1,v1), (v2,w2), (w2,v2))
    # G2: v1-w2, v2-w1 (directed: (v1,w2), (w2,v1), (v2,w1), (w1,v2))
    
    switched_G1 = [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]
    switched_G2 = [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]
    
    print(f"  Switched edges G1: {switched_G1}")
    print(f"  Switched edges G2: {switched_G2}")
    
    # Find where entries differ in T
    # T1 and T2 have the same size since both graphs have same number of edges
    
    # But the edges are different! G1 has (v1,w1) and (v2,w2), G2 has (v1,w2) and (v2,w1)
    # So the matrices are indexed over different edge sets
    
    # Let's compare using a common indexing
    # The edges that are the same: all edges except the 4 switched ones
    
    common_edges = set(edges1) - set(switched_G1)
    
    print(f"  Number of common edges: {len(common_edges)}")
    print(f"  Total edges in G1: {len(edges1)}")
    
    # For the eigenvalue analysis, let's just verify cospectrality
    eig1 = sorted(np.linalg.eigvals(T1), key=lambda x: (x.real, x.imag))
    eig2 = sorted(np.linalg.eigvals(T2), key=lambda x: (x.real, x.imag))
    
    max_diff = max(abs(e1 - e2) for e1, e2 in zip(eig1, eig2))
    print(f"  Max eigenvalue difference: {max_diff:.2e}")
    
    # Analyze the structure of the transition perturbation
    # Instead of direct matrix comparison, let's look at the effect on closed walks
    
    # Count closed NB walks of length 3 through each edge
    print("\n  Length-3 closed walk analysis:")
    
    # For edges involved in the switch
    for e in switched_G1:
        if e in e2i1:
            idx = e2i1[e]
            T1_cubed = np.linalg.matrix_power(T1, 3)
            print(f"    T1^3[{e}, {e}] = {T1_cubed[idx, idx]:.4f}")
    
    for e in switched_G2:
        if e in e2i2:
            idx = e2i2[e]
            T2_cubed = np.linalg.matrix_power(T2, 3)
            print(f"    T2^3[{e}, {e}] = {T2_cubed[idx, idx]:.4f}")
    
    # Key insight: check if there's a pairing between G1 switched edges and G2 switched edges
    # such that the diagonal entries match
    print("\n  Checking diagonal pairing:")
    T1_cubed = np.linalg.matrix_power(T1, 3)
    T2_cubed = np.linalg.matrix_power(T2, 3)
    
    diag1 = []
    for e in switched_G1:
        if e in e2i1:
            diag1.append(T1_cubed[e2i1[e], e2i1[e]])
    
    diag2 = []
    for e in switched_G2:
        if e in e2i2:
            diag2.append(T2_cubed[e2i2[e], e2i2[e]])
    
    print(f"    G1 switched diagonals: {[f'{d:.4f}' for d in sorted(diag1)]}")
    print(f"    G2 switched diagonals: {[f'{d:.4f}' for d in sorted(diag2)]}")
    print(f"    Multiset equal: {sorted(diag1) == sorted(diag2) if len(diag1) == len(diag2) else 'sizes differ'}")
    
    # Check higher powers
    for k in [4, 5, 6]:
        T1_k = np.linalg.matrix_power(T1, k)
        T2_k = np.linalg.matrix_power(T2, k)
        
        diag1 = [T1_k[e2i1[e], e2i1[e]] for e in switched_G1 if e in e2i1]
        diag2 = [T2_k[e2i2[e], e2i2[e]] for e in switched_G2 if e in e2i2]
        
        match = sorted(diag1) == sorted(diag2) if len(diag1) == len(diag2) else False
        sum_match = abs(sum(diag1) - sum(diag2)) < 1e-10
        
        print(f"    k={k}: diag multiset equal: {match}, sum equal: {sum_match}")
    
    print()

# Now compare with a σ-symmetric switch
print("=" * 80)
print("COMPARISON WITH σ-SYMMETRIC SWITCH")
print("=" * 80)
print()

# Pick I?qadhik_ as an example σ-symmetric switch with |shared|=1
for g6_1, g6_2, G1, G2, v1, v2, w1, w2 in switches:
    if g6_1 == 'I?qadhik_':
        print(f"Switch: {g6_1} (σ-symmetric)")
        
        T1, edges1, e2i1 = build_nbl_matrix(G1)
        T2, edges2, e2i2 = build_nbl_matrix(G2)
        
        switched_G1 = [(v1, w1), (w1, v1), (v2, w2), (w2, v2)]
        switched_G2 = [(v1, w2), (w2, v1), (v2, w1), (w1, v2)]
        
        for k in [3, 4, 5, 6]:
            T1_k = np.linalg.matrix_power(T1, k)
            T2_k = np.linalg.matrix_power(T2, k)
            
            diag1 = [T1_k[e2i1[e], e2i1[e]] for e in switched_G1 if e in e2i1]
            diag2 = [T2_k[e2i2[e], e2i2[e]] for e in switched_G2 if e in e2i2]
            
            match = sorted(diag1) == sorted(diag2) if len(diag1) == len(diag2) else False
            sum_match = abs(sum(diag1) - sum(diag2)) < 1e-10
            
            print(f"    k={k}: diag multiset equal: {match}, sum equal: {sum_match}")
            print(f"           G1: {[f'{d:.4f}' for d in diag1]}")
            print(f"           G2: {[f'{d:.4f}' for d in diag2]}")

conn.close()
