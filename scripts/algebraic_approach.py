#!/usr/bin/env python3
"""
Attempt a cleaner algebraic proof using block structure of T.

The idea: express tr(T^k) in terms of block matrices and show equality.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations
from numpy.linalg import matrix_power

def get_one_switch():
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
        
        for perm in permutations(list(verts)):
            v1, v2, w1, w2 = perm
            e1 = frozenset([v1, w1])
            e2 = frozenset([v2, w2])
            new_e1 = frozenset([v1, w2])
            new_e2 = frozenset([v2, w1])
            
            if only_in_G1 == {e1, e2} and only_in_G2 == {new_e1, new_e2}:
                if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                    return G1, G2, v1, v2, w1, w2
    
    return None

def build_ordered_nbl(G, S, switch_edges_G):
    """
    Build NBL matrix with edges ordered as:
    [E_ext, E_bnd, E_int_parallel, E_int_switch]
    
    Returns T and the edge ordering.
    """
    all_edges = [(u, v) for u, v in G.edges()] + [(v, u) for u, v in G.edges()]
    
    E_ext = []
    E_bnd = []
    E_int_parallel = []
    E_int_switch = []
    
    for e in all_edges:
        u, v = e
        u_in = u in S
        v_in = v in S
        
        if not u_in and not v_in:
            E_ext.append(e)
        elif u_in != v_in:
            E_bnd.append(e)
        else:  # both in S
            if e in switch_edges_G:
                E_int_switch.append(e)
            else:
                E_int_parallel.append(e)
    
    ordered_edges = E_ext + E_bnd + E_int_parallel + E_int_switch
    edge_to_idx = {e: i for i, e in enumerate(ordered_edges)}
    
    n = len(ordered_edges)
    T = np.zeros((n, n))
    
    for i, (u, v) in enumerate(ordered_edges):
        deg_v = G.degree(v)
        if deg_v > 1:
            for w in G.neighbors(v):
                if w != u:
                    e_next = (v, w)
                    if e_next in edge_to_idx:
                        j = edge_to_idx[e_next]
                        T[i, j] = 1.0 / (deg_v - 1)
    
    sizes = (len(E_ext), len(E_bnd), len(E_int_parallel), len(E_int_switch))
    return T, ordered_edges, sizes

G1, G2, v1, v2, w1, w2 = get_one_switch()
S = {v1, v2, w1, w2}

switch_G1 = {(v1, w1), (w1, v1), (v2, w2), (w2, v2)}
switch_G2 = {(v1, w2), (w2, v1), (v2, w1), (w1, v2)}

T1, edges1, sizes1 = build_ordered_nbl(G1, S, switch_G1)
T2, edges2, sizes2 = build_ordered_nbl(G2, S, switch_G2)

n_ext, n_bnd, n_par, n_sw = sizes1

print("Block sizes:", sizes1)
print(f"  External: {n_ext}")
print(f"  Boundary: {n_bnd}")
print(f"  Internal parallel: {n_par}")
print(f"  Internal switch: {n_sw}")
print()

# Extract blocks
def extract_blocks(T, sizes):
    n_ext, n_bnd, n_par, n_sw = sizes
    i1 = n_ext
    i2 = n_ext + n_bnd
    i3 = n_ext + n_bnd + n_par
    
    blocks = {}
    labels = ['e', 'b', 'p', 's']
    boundaries = [0, i1, i2, i3, T.shape[0]]
    
    for i, li in enumerate(labels):
        for j, lj in enumerate(labels):
            blocks[li + lj] = T[boundaries[i]:boundaries[i+1], boundaries[j]:boundaries[j+1]]
    
    return blocks

B1 = extract_blocks(T1, sizes1)
B2 = extract_blocks(T2, sizes2)

print("Checking which blocks are equal between G and G':")
for key in sorted(B1.keys()):
    if B1[key].size > 0 and B2[key].size > 0:
        diff = np.max(np.abs(B1[key] - B2[key]))
        status = "=" if diff < 1e-10 else f"≠ (diff={diff:.4f})"
        print(f"  T_{key}: {status}")
print()

# The key insight: which blocks differ?
# Expected: ee, eb, ep, be, bb, bp, pe, pb, pp should be equal
# Differing: anything involving 's' (switch edges)

print("=" * 60)
print("KEY OBSERVATION:")
print("=" * 60)
print()
print("Let T = [A  B ]  where A covers (ext, bnd, parallel)")
print("        [C  D ]  and D covers switch edges")
print()
print("Then tr(T^k) = tr(A^k) + tr(contributions involving D)")
print()

# Build A and D blocks
i_split = n_ext + n_bnd + n_par

A1 = T1[:i_split, :i_split]
B1_block = T1[:i_split, i_split:]
C1_block = T1[i_split:, :i_split]
D1 = T1[i_split:, i_split:]

A2 = T2[:i_split, :i_split]
B2_block = T2[:i_split, i_split:]
C2_block = T2[i_split:, :i_split]
D2 = T2[i_split:, i_split:]

print("Checking A blocks (non-switch):")
print(f"  max|A1 - A2| = {np.max(np.abs(A1 - A2)):.2e}")
print()

# A1 = A2, so tr(A1^k) = tr(A2^k)

# For the switch contributions, we need to analyze:
# tr(T^k) - tr(A^k) = terms involving B, C, D

# The trace formula for block matrices is complex, but we can compute directly:

print("Direct trace comparison:")
for k in range(1, 8):
    T1k = matrix_power(T1, k)
    T2k = matrix_power(T2, k)
    A1k = matrix_power(A1, k)
    A2k = matrix_power(A2, k)
    
    tr_T1 = np.trace(T1k)
    tr_T2 = np.trace(T2k)
    tr_A1 = np.trace(A1k)
    tr_A2 = np.trace(A2k)
    
    # Switch contribution
    sw_T1 = np.trace(T1k[i_split:, i_split:])
    sw_T2 = np.trace(T2k[i_split:, i_split:])
    
    print(f"k={k}: tr(T1)={tr_T1:.6f}, tr(T2)={tr_T2:.6f}, diff={abs(tr_T1-tr_T2):.2e}")
    print(f"      tr(A1)={tr_A1:.6f}, tr(A2)={tr_A2:.6f}, diff={abs(tr_A1-tr_A2):.2e}")
    print(f"      switch_diag(T1^k)={sw_T1:.6f}, switch_diag(T2^k)={sw_T2:.6f}, diff={abs(sw_T1-sw_T2):.2e}")
print()

# The issue: tr(T^k) ≠ tr(A^k) + tr(D^k) due to cross terms
# We need a different approach

print("=" * 60)
print("ALGEBRAIC APPROACH: Similarity on switch subspace")
print("=" * 60)
print()

# Define permutation on switch edges:
# G1 switch edges: (v1,w1), (w1,v1), (v2,w2), (w2,v2)
# G2 switch edges: (v1,w2), (w2,v1), (v2,w1), (w1,v2)

# σ permutation swaps w1 ↔ w2
# (v1,w1) → (v1,w2)
# (w1,v1) → (w2,v1)
# (v2,w2) → (v2,w1)
# (w2,v2) → (w1,v2)

switch_edges_G1 = [(v1,w1), (w1,v1), (v2,w2), (w2,v2)]
switch_edges_G2 = [(v1,w2), (w2,v1), (v2,w1), (w1,v2)]

# Build permutation matrix P_σ on switch edges
# P_σ @ (vector indexed by G1 switch edges) = (vector indexed by G2 switch edges)

# We need: T2 = P @ T1 @ P^(-1) where P is identity on non-switch, σ on switch
# This would give tr(T1^k) = tr(T2^k) directly

# Build full permutation matrix
n = len(edges1)
P = np.zeros((n, n))

for i, e in enumerate(edges1):
    u, v = e
    e_sigma = (u if u not in {w1,w2} else (w2 if u == w1 else w1),
               v if v not in {w1,w2} else (w2 if v == w1 else w1))
    
    # Find e_sigma in edges2
    if e_sigma in edges2:
        j = edges2.index(e_sigma)
        P[j, i] = 1
    else:
        # Edge doesn't exist in G2
        pass

# Check if P is a valid permutation
print(f"P is permutation matrix: {np.allclose(P @ P.T, np.eye(n)) and np.allclose(P.T @ P, np.eye(n))}")
print(f"P row sums: min={P.sum(axis=1).min()}, max={P.sum(axis=1).max()}")
print(f"P col sums: min={P.sum(axis=0).min()}, max={P.sum(axis=0).max()}")
print()

# The problem: P is NOT a permutation because some edges in G1 don't exist in G2!
# Specifically, switch edges (v1,w1), (v2,w2) in G1 map to (v1,w1), (v2,w2) under σ,
# but these don't exist in G2.

print("The simple similarity approach fails because σ doesn't map")
print("G1 edges to G2 edges bijectively.")
print()
print("This is why we need the more subtle PAIRING argument.")
