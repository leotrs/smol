#!/usr/bin/env python3
"""
Deep dive into WHY switch_diag(T1^k) = switch_diag(T2^k).

We have:
T = [A  B]
    [C  D]

where A is identical in G and G', and D (switch-to-switch) is also identical.
Only B (non-switch to switch) and C (switch to non-switch) differ.

The diagonal of T^k on switch edges is:
(T^k)_ss = sum over all paths of length k that start and end at switch edges

Let's compute this using the Woodbury-like decomposition.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations

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
        else:
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
    return T, ordered_edges, E_int_switch, sizes

G1, G2, v1, v2, w1, w2 = get_one_switch()
S = {v1, v2, w1, w2}

switch_G1 = {(v1, w1), (w1, v1), (v2, w2), (w2, v2)}
switch_G2 = {(v1, w2), (w2, v1), (v2, w1), (w1, v2)}

T1, edges1, sw_edges1, sizes1 = build_ordered_nbl(G1, S, switch_G1)
T2, edges2, sw_edges2, sizes2 = build_ordered_nbl(G2, S, switch_G2)

n_ext, n_bnd, n_par, n_sw = sizes1
i_split = n_ext + n_bnd + n_par

print("Switch edges in G1:", sw_edges1)
print("Switch edges in G2:", sw_edges2)
print()

# Extract 2x2 block structure
A1 = T1[:i_split, :i_split]
B1 = T1[:i_split, i_split:]
C1 = T1[i_split:, :i_split]
D1 = T1[i_split:, i_split:]

A2 = T2[:i_split, :i_split]
B2 = T2[:i_split, i_split:]
C2 = T2[i_split:, :i_split]
D2 = T2[i_split:, i_split:]

print("Block comparison:")
print(f"  A1 = A2: {np.allclose(A1, A2)}")
print(f"  B1 = B2: {np.allclose(B1, B2)}")
print(f"  C1 = C2: {np.allclose(C1, C2)}")
print(f"  D1 = D2: {np.allclose(D1, D2)}")
print()

# What's the structure of B and C?
print("B1 (non-switch → switch):")
print(B1)
print()
print("B2 (non-switch → switch):")
print(B2)
print()

print("C1 (switch → non-switch):")
print(C1)
print()
print("C2 (switch → non-switch):")
print(C2)
print()

# Key observation: B and C have a specific structure
# B1[:, i] = transitions INTO switch edge i
# C1[i, :] = transitions OUT OF switch edge i

# The pairing: sw_edges1 = [(v1,w1), (w1,v1), (v2,w2), (w2,v2)]
#              sw_edges2 = [(v1,w2), (w2,v1), (v2,w1), (w1,v2)]

# Under σ (swap w1 ↔ w2):
# (v1,w1) ↔ (v1,w2)
# (w1,v1) ↔ (w2,v1)
# (v2,w2) ↔ (v2,w1)
# (w2,v2) ↔ (w1,v2)

# Build permutation on switch edges
P_sw = np.zeros((4, 4))
# sw_edges1[0] = (v1,w1) should map to sw_edges2 position of (v1,w2)
# sw_edges1[1] = (w1,v1) should map to sw_edges2 position of (w2,v1)
# etc.

sigma_map = {
    (v1, w1): (v1, w2),
    (w1, v1): (w2, v1),
    (v2, w2): (v2, w1),
    (w2, v2): (w1, v2),
}

for i, e1 in enumerate(sw_edges1):
    e2 = sigma_map[e1]
    j = sw_edges2.index(e2)
    P_sw[j, i] = 1

print("Permutation matrix on switch edges (σ):")
print(P_sw)
print()

# Check: D2 = P_sw @ D1 @ P_sw.T?
print("D2 = P_σ D1 P_σ^T:", np.allclose(D2, P_sw @ D1 @ P_sw.T))
print()

# Check: C2 = P_sw @ C1?
print("C2 = P_σ C1:", np.allclose(C2, P_sw @ C1))
print()

# Check: B2 = B1 @ P_sw.T?
print("B2 = B1 P_σ^T:", np.allclose(B2, B1 @ P_sw.T))
print()

# AHA! So:
# T2 = [A      B1 @ P^T]
#      [P @ C1   P @ D1 @ P^T]

# This means T2 = Q @ T1 @ Q^{-1} where Q = [I  0]
#                                           [0  P]

# Let's verify!
n = T1.shape[0]
Q = np.eye(n)
Q[i_split:, i_split:] = P_sw

print("T2 = Q T1 Q^{-1}:", np.allclose(T2, Q @ T1 @ np.linalg.inv(Q)))
print()

if np.allclose(T2, Q @ T1 @ np.linalg.inv(Q)):
    print("=" * 60)
    print("EUREKA! T2 is SIMILAR to T1!")
    print("=" * 60)
    print()
    print("This IMMEDIATELY implies tr(T1^k) = tr(T2^k) for all k.")
    print()
    print("The similarity is given by Q = [I  0 ]")
    print("                               [0  P_σ]")
    print()
    print("where P_σ is the permutation on switch edges induced by σ: w1 ↔ w2")
