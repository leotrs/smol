#!/usr/bin/env python3
"""
Rigorous computation of lumped transfer matrices Φ (S-internal) and Ω (S-external).

Goal: Understand exactly what symmetries hold and fix the proof.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations
from numpy.linalg import inv, matrix_power

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
    """Build full NBL transition matrix."""
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

def compute_boundary_types(G, v1, v2, w1, w2):
    """Compute boundary edge types."""
    S = {v1, v2, w1, w2}
    
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    
    # Entry edges by type
    entry_types = {
        'v1': [(x, v1) for x in ext_v1],
        'v2': [(x, v2) for x in ext_v2],
        'w1_s': [(x, w1) for x in shared],
        'w2_s': [(x, w2) for x in shared],
        'w1_u': [(x, w1) for x in unique_1],
        'w2_u': [(x, w2) for x in unique_2],
    }
    
    # Exit edges by type
    exit_types = {
        'v1': [(v1, x) for x in ext_v1],
        'v2': [(v2, x) for x in ext_v2],
        'w1_s': [(w1, x) for x in shared],
        'w2_s': [(w2, x) for x in shared],
        'w1_u': [(w1, x) for x in unique_1],
        'w2_u': [(w2, x) for x in unique_2],
    }
    
    return entry_types, exit_types, shared, unique_1, unique_2

def compute_internal_kernel(G, v1, v2, w1, w2, entry_types, exit_types, edge_to_idx):
    """
    Compute the S-internal transfer kernel Φ.
    
    Φ[τ, ρ] = sum over entry edges e of type τ, exit edges e' of type ρ,
              of the total weight of all S-internal paths from e to e'.
    
    This uses the resolvent (I - T_S)^{-1} restricted to S-internal transitions.
    """
    S = {v1, v2, w1, w2}
    
    # Build S-internal transition matrix
    # States: directed edges (u,v) where u,v ∈ S and uv ∈ E(G)
    S_edges = []
    for u in S:
        for v in S:
            if G.has_edge(u, v):
                S_edges.append((u, v))
    
    if not S_edges:
        # No internal edges - Φ is trivial
        type_names = ['v1', 'v2', 'w1_s', 'w2_s', 'w1_u', 'w2_u']
        return np.zeros((6, 6)), type_names
    
    S_edge_to_idx = {e: i for i, e in enumerate(S_edges)}
    n_S = len(S_edges)
    
    T_S = np.zeros((n_S, n_S))
    for i, (u, v) in enumerate(S_edges):
        deg_v = G.degree(v)
        if deg_v > 1:
            for w in G.neighbors(v):
                if w != u and (v, w) in S_edge_to_idx:
                    j = S_edge_to_idx[(v, w)]
                    T_S[i, j] = 1.0 / (deg_v - 1)
    
    # Resolvent: sum of T_S^k for k >= 0
    # = (I - T_S)^{-1} if spectral radius < 1
    I = np.eye(n_S)
    try:
        resolvent = inv(I - T_S)
    except:
        # Use power series
        resolvent = I.copy()
        Tk = T_S.copy()
        for _ in range(100):
            resolvent += Tk
            Tk = Tk @ T_S
            if np.max(np.abs(Tk)) < 1e-15:
                break
    
    # Now compute Φ[τ, ρ]
    # For entry edge (x, s) of type τ and exit edge (s', y) of type ρ:
    # The path enters at (x, s), then possibly bounces inside S, then exits at (s', y).
    # 
    # Direct exit: (x,s) -> (s,y) if s=s' and sy ∈ E, weight 1/(deg(s)-1)
    # Via internal: (x,s) -> (s,t) [internal] -> ... -> (s',y)
    
    type_names = ['v1', 'v2', 'w1_s', 'w2_s', 'w1_u', 'w2_u']
    Phi = np.zeros((6, 6))
    
    for i_tau, tau in enumerate(type_names):
        for i_rho, rho in enumerate(type_names):
            total = 0.0
            
            for e_in in entry_types[tau]:
                x, s = e_in
                
                for e_out in exit_types[rho]:
                    s_prime, y = e_out
                    
                    # Case 1: Direct exit (no internal edges traversed)
                    # From (x, s) go directly to (s, y)
                    if s == s_prime and G.has_edge(s, y) and y != x:
                        deg_s = G.degree(s)
                        total += 1.0 / (deg_s - 1)
                    
                    # Case 2: Via internal edges
                    # (x,s) -> (s,t) for some t ∈ S, then internal path, then exit
                    for t in S:
                        if t != x and G.has_edge(s, t):
                            # First step: (x,s) -> (s,t)
                            first_step_weight = 1.0 / (G.degree(s) - 1)
                            
                            e_first = (s, t)
                            if e_first not in S_edge_to_idx:
                                continue
                            
                            i_first = S_edge_to_idx[e_first]
                            
                            # Now we need paths from (s,t) that eventually exit at (s',y)
                            # The exit happens when we're at some (u, s') and take step to (s', y)
                            
                            for u in S:
                                if u != y and G.has_edge(u, s_prime) and G.has_edge(s_prime, y):
                                    e_last_internal = (u, s_prime)
                                    if e_last_internal not in S_edge_to_idx:
                                        continue
                                    
                                    i_last = S_edge_to_idx[e_last_internal]
                                    
                                    # Weight from (s,t) to (u,s') via internal paths
                                    internal_weight = resolvent[i_first, i_last]
                                    
                                    # Weight of final exit step (u,s') -> (s',y)
                                    exit_weight = 1.0 / (G.degree(s_prime) - 1)
                                    
                                    total += first_step_weight * internal_weight * exit_weight
            
            Phi[i_tau, i_rho] = total
    
    return Phi, type_names

def sigma_permutation_matrix():
    """
    The σ permutation on boundary types.
    σ: v1 ↔ v1, v2 ↔ v2, w1_s ↔ w2_s, w1_u ↔ w2_u
    """
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

# Main analysis
switches = get_switches()
P_sigma = sigma_permutation_matrix()

print("=" * 80)
print("RIGOROUS ANALYSIS OF LUMPED TRANSFER MATRICES")
print("=" * 80)
print()

print("Testing Step 5: Φ_G[τ,ρ] = Φ_{G'}[σ(τ),σ(ρ)]")
print("Equivalently: Φ_G = P_σ @ Φ_{G'} @ P_σ^T")
print("-" * 60)
print()

step5_results = []

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    entry1, exit1, shared1, u1_1, u2_1 = compute_boundary_types(G1, v1, v2, w1, w2)
    entry2, exit2, shared2, u1_2, u2_2 = compute_boundary_types(G2, v1, v2, w1, w2)
    
    Phi1, types = compute_internal_kernel(G1, v1, v2, w1, w2, entry1, exit1, e2i1)
    Phi2, _ = compute_internal_kernel(G2, v1, v2, w1, w2, entry2, exit2, e2i2)
    
    # Test: Φ_G = P_σ @ Φ_{G'} @ P_σ^T
    Phi2_transformed = P_sigma @ Phi2 @ P_sigma.T
    
    diff = np.abs(Phi1 - Phi2_transformed)
    max_diff = np.max(diff)
    
    step5_holds = max_diff < 1e-10
    step5_results.append(step5_holds)
    
    status = "✓" if step5_holds else "✗"
    print(f"Switch {idx}: max|Φ_G - P_σ Φ_{{G'}} P_σ^T| = {max_diff:.2e} {status}")
    
    if not step5_holds:
        print(f"  Φ_G:")
        print(Phi1)
        print(f"  P_σ Φ_{{G'}} P_σ^T:")
        print(Phi2_transformed)

print()
print(f"Step 5 holds for {sum(step5_results)}/{len(step5_results)} switches")
print()
