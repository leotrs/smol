#!/usr/bin/env python3
"""
Compute the actual lumped kernels for all 11 switches and verify σ-invariance.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations

def build_nbl_matrix(G):
    """Build NBL transition matrix."""
    nodes = list(G.nodes())
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

def compute_lumped_kernel(G, v1, v2, w1, w2):
    """Compute the 6x6 lumped kernel matrix."""
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    T, edges, edge_to_idx = build_nbl_matrix(G)
    n = len(edges)
    
    # Compute (I - T)^{-1} - I = T + T^2 + T^3 + ...
    # This is the kernel: total weight of all paths of length >= 1
    I = np.eye(n)
    try:
        resolvent = np.linalg.inv(I - T) - I
    except np.linalg.LinAlgError:
        # Use power series approximation
        resolvent = np.zeros((n, n))
        Tk = T.copy()
        for _ in range(1000):
            resolvent += Tk
            Tk = Tk @ T
            if np.max(np.abs(Tk)) < 1e-15:
                break
    
    # Define boundary edge sets
    # Entry edges: (x, s) where x not in S, s in S
    # Exit edges: (s, x) where s in S, x not in S
    
    types = ['v1', 'v2', 'w1_s', 'w2_s', 'w1_u', 'w2_u']
    
    def get_entry_edges(type_name):
        if type_name == 'v1':
            return [(x, v1) for x in ext_v1]
        elif type_name == 'v2':
            return [(x, v2) for x in ext_v2]
        elif type_name == 'w1_s':
            return [(x, w1) for x in shared]
        elif type_name == 'w2_s':
            return [(x, w2) for x in shared]
        elif type_name == 'w1_u':
            return [(x, w1) for x in unique_1]
        elif type_name == 'w2_u':
            return [(x, w2) for x in unique_2]
    
    def get_exit_edges(type_name):
        if type_name == 'v1':
            return [(v1, x) for x in ext_v1]
        elif type_name == 'v2':
            return [(v2, x) for x in ext_v2]
        elif type_name == 'w1_s':
            return [(w1, x) for x in shared]
        elif type_name == 'w2_s':
            return [(w2, x) for x in shared]
        elif type_name == 'w1_u':
            return [(w1, x) for x in unique_1]
        elif type_name == 'w2_u':
            return [(w2, x) for x in unique_2]
    
    # Compute 6x6 kernel
    K = np.zeros((6, 6))
    for i, tau in enumerate(types):
        for j, rho in enumerate(types):
            entry_edges = get_entry_edges(tau)
            exit_edges = get_exit_edges(rho)
            total = 0.0
            for e_in in entry_edges:
                if e_in not in edge_to_idx:
                    continue
                idx_in = edge_to_idx[e_in]
                for e_out in exit_edges:
                    if e_out not in edge_to_idx:
                        continue
                    idx_out = edge_to_idx[e_out]
                    total += resolvent[idx_in, idx_out]
            K[i, j] = total
    
    return K, types

def sigma_permutation():
    """Return the σ permutation matrix."""
    # σ: v1 -> v1, v2 -> v2, w1_s -> w2_s, w2_s -> w1_s, w1_u -> w2_u, w2_u -> w1_u
    # Order: v1, v2, w1_s, w2_s, w1_u, w2_u
    P = np.array([
        [1, 0, 0, 0, 0, 0],  # v1 -> v1
        [0, 1, 0, 0, 0, 0],  # v2 -> v2
        [0, 0, 0, 1, 0, 0],  # w1_s -> w2_s
        [0, 0, 1, 0, 0, 0],  # w2_s -> w1_s
        [0, 0, 0, 0, 0, 1],  # w1_u -> w2_u
        [0, 0, 0, 0, 1, 0],  # w2_u -> w1_u
    ], dtype=float)
    return P

# Get switches
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

print("KERNEL EQUIVALENCE VERIFICATION")
print("=" * 80)
print()

P_sigma = sigma_permutation()

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    shared = ext_w1 & ext_w2
    
    has_v1v2 = G1.has_edge(v1, v2)
    has_w1w2 = G1.has_edge(w1, w2)
    
    print(f"Switch {idx}: {g6_1}")
    print(f"  |shared|={len(shared)}, parallel=(v1v2:{has_v1v2}, w1w2:{has_w1w2})")
    
    # Compute kernels
    K1, types = compute_lumped_kernel(G1, v1, v2, w1, w2)
    
    # For G2, the switch vertices map: w1 and w2 effectively swap roles
    # In G2: edges are v1-w2, v2-w1 instead of v1-w1, v2-w2
    # So we compute K2 with the same labeling, then compare
    K2, _ = compute_lumped_kernel(G2, v1, v2, w1, w2)
    
    # Check: K1 = P_sigma @ K2 @ P_sigma.T
    K2_conjugated = P_sigma @ K2 @ P_sigma.T
    
    diff = np.abs(K1 - K2_conjugated)
    max_diff = np.max(diff)
    
    if max_diff < 1e-10:
        print(f"  ✓ Kernel equivalence holds! (max diff: {max_diff:.2e})")
    else:
        print(f"  ✗ Kernel equivalence FAILS! (max diff: {max_diff:.2e})")
        print("  K1:")
        print(K1)
        print("  P_σ K2 P_σ^T:")
        print(K2_conjugated)
        print("  Difference:")
        print(K1 - K2_conjugated)
    print()

conn.close()
