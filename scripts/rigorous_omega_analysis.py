#!/usr/bin/env python3
"""
Analyze Step 6: External transfer matrix Ω.

Key question: Does Ω_G = P_σ @ Ω_G @ P_σ^T?
(Note: Ω is the same in G and G' since external graph is identical)

If not, what weaker property makes the traces match?
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations
from numpy.linalg import inv

def get_switches():
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
    conn.close()
    
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
    
    return switches

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

def compute_external_kernel(G, v1, v2, w1, w2, edge_to_idx):
    """
    Compute the S-external transfer kernel Ω.
    
    Ω[ρ, τ] = sum over exit edges e of type ρ, entry edges e' of type τ,
              of the total weight of all S-external paths from e to e'.
    """
    S = {v1, v2, w1, w2}
    n_total = len(edge_to_idx)
    
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    
    # Define exit and entry edge lists by type
    exit_edges = {
        'v1': [(v1, x) for x in ext_v1],
        'v2': [(v2, x) for x in ext_v2],
        'w1_s': [(w1, x) for x in shared],
        'w2_s': [(w2, x) for x in shared],
        'w1_u': [(w1, x) for x in unique_1],
        'w2_u': [(w2, x) for x in unique_2],
    }
    
    entry_edges = {
        'v1': [(x, v1) for x in ext_v1],
        'v2': [(x, v2) for x in ext_v2],
        'w1_s': [(x, w1) for x in shared],
        'w2_s': [(x, w2) for x in shared],
        'w1_u': [(x, w1) for x in unique_1],
        'w2_u': [(x, w2) for x in unique_2],
    }
    
    # Build external-only NBL submatrix
    # External edges: (u,v) where u ∉ S or v ∉ S (but not internal to S)
    ext_edge_list = []
    for e in edge_to_idx:
        u, v = e
        # Include if at least one endpoint is outside S
        # But exclude purely internal edges (both in S)
        if not (u in S and v in S):
            ext_edge_list.append(e)
    
    ext_edge_to_idx = {e: i for i, e in enumerate(ext_edge_list)}
    n_ext = len(ext_edge_list)
    
    T_ext = np.zeros((n_ext, n_ext))
    for i, (u, v) in enumerate(ext_edge_list):
        deg_v = G.degree(v)
        if deg_v > 1:
            for w in G.neighbors(v):
                if w != u:
                    e_next = (v, w)
                    if e_next in ext_edge_to_idx:
                        j = ext_edge_to_idx[e_next]
                        T_ext[i, j] = 1.0 / (deg_v - 1)
    
    # Resolvent for external paths
    I = np.eye(n_ext)
    try:
        resolvent = inv(I - T_ext)
    except:
        resolvent = I.copy()
        Tk = T_ext.copy()
        for _ in range(100):
            resolvent += Tk
            Tk = Tk @ T_ext
            if np.max(np.abs(Tk)) < 1e-15:
                break
    
    # Compute Ω[ρ, τ]
    type_names = ['v1', 'v2', 'w1_s', 'w2_s', 'w1_u', 'w2_u']
    Omega = np.zeros((6, 6))
    
    for i_rho, rho in enumerate(type_names):
        for i_tau, tau in enumerate(type_names):
            total = 0.0
            
            for e_out in exit_edges[rho]:
                if e_out not in ext_edge_to_idx:
                    continue
                i_out = ext_edge_to_idx[e_out]
                
                for e_in in entry_edges[tau]:
                    if e_in not in ext_edge_to_idx:
                        continue
                    i_in = ext_edge_to_idx[e_in]
                    
                    # Weight of all paths from e_out to e_in
                    total += resolvent[i_out, i_in]
            
            Omega[i_rho, i_tau] = total
    
    return Omega, type_names

def sigma_permutation_matrix():
    P = np.array([
        [1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 1, 0],
    ], dtype=float)
    return P

# Main analysis
switches = get_switches()
P_sigma = sigma_permutation_matrix()

print("=" * 80)
print("ANALYSIS OF EXTERNAL TRANSFER MATRIX Ω")
print("=" * 80)
print()

print("Testing: Is Ω σ-symmetric? i.e., Ω = P_σ @ Ω @ P_σ^T")
print("-" * 60)
print()

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    
    Omega, types = compute_external_kernel(G1, v1, v2, w1, w2, e2i1)
    
    # Test σ-symmetry
    Omega_transformed = P_sigma @ Omega @ P_sigma.T
    diff = Omega - Omega_transformed
    max_diff = np.max(np.abs(diff))
    
    is_symmetric = max_diff < 1e-10
    status = "✓ σ-SYMMETRIC" if is_symmetric else "✗ NOT σ-symmetric"
    
    print(f"Switch {idx}: max|Ω - P_σ Ω P_σ^T| = {max_diff:.2e} {status}")
    
    if not is_symmetric:
        print(f"  Ω:")
        for i, row_name in enumerate(types):
            row_str = " ".join(f"{Omega[i,j]:8.4f}" for j in range(6))
            print(f"    {row_name}: {row_str}")
        print(f"  P_σ Ω P_σ^T:")
        for i, row_name in enumerate(types):
            row_str = " ".join(f"{Omega_transformed[i,j]:8.4f}" for j in range(6))
            print(f"    {row_name}: {row_str}")
        print(f"  Difference (Ω - P_σ Ω P_σ^T):")
        for i, row_name in enumerate(types):
            row_str = " ".join(f"{diff[i,j]:8.4f}" for j in range(6))
            print(f"    {row_name}: {row_str}")
        print()
