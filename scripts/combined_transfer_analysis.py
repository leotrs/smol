#!/usr/bin/env python3
"""
The key insight: Ω alone isn't σ-symmetric, but the COMBINED transfer matrix
Φ @ Ω (or the full interaction pattern) must have matching traces.

Actually, for trace equality, we need: tr((Ω @ Φ)^m) to be the same for all m.

Let's check what property ACTUALLY holds.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations
from numpy.linalg import inv, eigvals

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

def compute_phi_omega(G, v1, v2, w1, w2, edge_to_idx):
    """Compute both Φ and Ω matrices."""
    S = {v1, v2, w1, w2}
    n_total = len(edge_to_idx)
    
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    
    entry_edges = {
        'v1': [(x, v1) for x in ext_v1],
        'v2': [(x, v2) for x in ext_v2],
        'w1_s': [(x, w1) for x in shared],
        'w2_s': [(x, w2) for x in shared],
        'w1_u': [(x, w1) for x in unique_1],
        'w2_u': [(x, w2) for x in unique_2],
    }
    
    exit_edges = {
        'v1': [(v1, x) for x in ext_v1],
        'v2': [(v2, x) for x in ext_v2],
        'w1_s': [(w1, x) for x in shared],
        'w2_s': [(w2, x) for x in shared],
        'w1_u': [(w1, x) for x in unique_1],
        'w2_u': [(w2, x) for x in unique_2],
    }
    
    type_names = ['v1', 'v2', 'w1_s', 'w2_s', 'w1_u', 'w2_u']
    
    # Build full NBL matrix
    all_edges = list(edge_to_idx.keys())
    n = len(all_edges)
    T = np.zeros((n, n))
    for i, (u, v) in enumerate(all_edges):
        deg_v = G.degree(v)
        if deg_v > 1:
            for w in G.neighbors(v):
                if w != u:
                    e_next = (v, w)
                    if e_next in edge_to_idx:
                        j = edge_to_idx[e_next]
                        T[i, j] = 1.0 / (deg_v - 1)
    
    # Compute resolvent (I - T)^{-1}
    I = np.eye(n)
    try:
        resolvent = inv(I - T)
    except:
        resolvent = I.copy()
        Tk = T.copy()
        for _ in range(200):
            resolvent += Tk
            Tk = Tk @ T
            if np.max(np.abs(Tk)) < 1e-15:
                break
    
    # Compute Φ: weight of paths from entry to exit, STAYING in S after entry
    # This is complex - let me use a simpler direct computation
    
    # For Φ[τ, ρ]: sum over entry edges of type τ, exit edges of type ρ
    # of weight of paths that enter at entry edge, bounce around S, exit at exit edge
    # WITHOUT re-exiting to the same external vertex we came from
    
    # Actually, let's compute the COMBINED transfer M directly
    # M[τ, τ'] = total weight of paths: enter type τ → internal segment → exit → external → enter type τ'
    
    # For simplicity, let me just verify that the traces of T^k match
    # and see if we can identify what makes this work
    
    return T, entry_edges, exit_edges, type_names, resolvent

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

# Main
switches = get_switches()
P_sigma = sigma_permutation_matrix()

print("=" * 80)
print("COMBINED TRANSFER MATRIX ANALYSIS")
print("=" * 80)
print()

# For each switch, let's directly verify eigenvalue equality
# and try to understand the mechanism

for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    eig1 = sorted(eigvals(T1), key=lambda x: (x.real, x.imag))
    eig2 = sorted(eigvals(T2), key=lambda x: (x.real, x.imag))
    
    max_eig_diff = max(abs(e1 - e2) for e1, e2 in zip(eig1, eig2))
    
    # Compute traces of T^k for k = 1 to 10
    traces1 = [np.trace(np.linalg.matrix_power(T1, k)) for k in range(1, 11)]
    traces2 = [np.trace(np.linalg.matrix_power(T2, k)) for k in range(1, 11)]
    
    max_trace_diff = max(abs(t1 - t2) for t1, t2 in zip(traces1, traces2))
    
    print(f"Switch {idx}:")
    print(f"  Max eigenvalue diff: {max_eig_diff:.2e}")
    print(f"  Max trace diff (k=1..10): {max_trace_diff:.2e}")
    
    # Now let's understand WHY traces match even when Ω isn't σ-symmetric
    # The key: we need to look at the INDUCED action on boundary edges
    
    S = {v1, v2, w1, w2}
    
    # Build vertex swap permutation
    def sigma_vertex(x):
        if x == w1: return w2
        if x == w2: return w1
        return x
    
    # Induced permutation on directed edges
    sigma_edges = {}
    for e in edges1:
        u, v = e
        e_sigma = (sigma_vertex(u), sigma_vertex(v))
        sigma_edges[e] = e_sigma
    
    # Check: does σ map G1 edges to G2 edges?
    G1_edge_set = set(edges1)
    G2_edge_set = set(edges2)
    
    sigma_G1_edges = set(sigma_edges[e] for e in edges1)
    
    maps_correctly = (sigma_G1_edges == G2_edge_set)
    print(f"  σ maps G1 edges to G2 edges: {maps_correctly}")
    
    if maps_correctly:
        # Build permutation matrix
        n = len(edges1)
        P = np.zeros((n, n))
        for i, e in enumerate(edges1):
            e_sigma = sigma_edges[e]
            j = edges2.index(e_sigma)
            P[i, j] = 1
        
        # Check: T2 = P @ T1 @ P^T?
        T1_conjugated = P @ T1 @ P.T
        conj_diff = np.max(np.abs(T1_conjugated - T2))
        print(f"  T2 = P σ T1 P^T: diff = {conj_diff:.2e}")
    
    print()

print("=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print("""
If σ (swapping w1 ↔ w2 on vertices) induces a permutation on directed edges
that maps G1's edge set to G2's edge set, then:

T_{G2} = P_σ T_{G1} P_σ^{-1}

This immediately gives trace equality!

Let's verify this is what's happening.
""")
