#!/usr/bin/env python3
"""
Complete the rigorous proof.

We have:
1. Φ_G = P_σ Φ_{G'} P_σ^T (verified)
2. Ω is NOT σ-symmetric in general
3. But traces still match

The key is to understand the CORRECT decomposition of tr(T^k).
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations

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

# The key insight: decompose T into blocks
# Let's partition edges into:
# - E_ext: edges entirely outside S
# - E_bnd: boundary edges (one endpoint in S, one outside)
# - E_int: edges entirely inside S

def partition_edges(G, S, edges):
    """Partition edges by their relationship to S."""
    E_ext = []  # Both endpoints outside S
    E_bnd = []  # One endpoint in S, one outside
    E_int = []  # Both endpoints in S
    
    for e in edges:
        u, v = e
        u_in = u in S
        v_in = v in S
        
        if u_in and v_in:
            E_int.append(e)
        elif u_in or v_in:
            E_bnd.append(e)
        else:
            E_ext.append(e)
    
    return E_ext, E_bnd, E_int

switches = get_switches()

print("=" * 80)
print("BLOCK STRUCTURE OF NBL MATRIX")
print("=" * 80)
print()

# Pick one switch to analyze
idx = 0
g6_1, g6_2, G1, G2, v1, v2, w1, w2 = switches[idx]
S = {v1, v2, w1, w2}

T1, edges1, e2i1 = build_nbl_matrix(G1)
T2, edges2, e2i2 = build_nbl_matrix(G2)

E_ext1, E_bnd1, E_int1 = partition_edges(G1, S, edges1)
E_ext2, E_bnd2, E_int2 = partition_edges(G2, S, edges2)

print(f"Switch {idx}:")
print(f"  |E_ext| = {len(E_ext1)} (external edges)")
print(f"  |E_bnd| = {len(E_bnd1)} (boundary edges)")
print(f"  |E_int| = {len(E_int1)} (S-internal edges)")
print()

# The key observation: E_ext and E_bnd are the SAME in G1 and G2!
# Only E_int differs.

print("Checking edge sets:")
print(f"  E_ext equal: {set(E_ext1) == set(E_ext2)}")
print(f"  E_bnd equal: {set(E_bnd1) == set(E_bnd2)}")
print(f"  E_int equal: {set(E_int1) == set(E_int2)}")
print()

print("E_int in G1:", sorted(E_int1))
print("E_int in G2:", sorted(E_int2))
print()

# Now let's understand the block structure of T
# Reorder edges as [E_ext, E_bnd, E_int]

def reorder_matrix(T, edges, E_ext, E_bnd, E_int):
    """Reorder T according to partition."""
    new_order = E_ext + E_bnd + E_int
    n = len(edges)
    
    old_to_new = {e: i for i, e in enumerate(new_order)}
    edge_to_old = {e: i for i, e in enumerate(edges)}
    
    T_reordered = np.zeros((n, n))
    for i, e_i in enumerate(new_order):
        for j, e_j in enumerate(new_order):
            old_i = edge_to_old[e_i]
            old_j = edge_to_old[e_j]
            T_reordered[i, j] = T[old_i, old_j]
    
    return T_reordered, new_order

T1_reord, order1 = reorder_matrix(T1, edges1, E_ext1, E_bnd1, E_int1)
T2_reord, order2 = reorder_matrix(T2, edges2, E_ext2, E_bnd2, E_int2)

n_ext = len(E_ext1)
n_bnd = len(E_bnd1)
n_int1 = len(E_int1)
n_int2 = len(E_int2)

print(f"Block sizes: n_ext={n_ext}, n_bnd={n_bnd}, n_int={n_int1}")
print()

# Extract blocks
# T = [T_ee  T_eb  T_ei]
#     [T_be  T_bb  T_bi]
#     [T_ie  T_ib  T_ii]

T_ee_1 = T1_reord[:n_ext, :n_ext]
T_eb_1 = T1_reord[:n_ext, n_ext:n_ext+n_bnd]
T_ei_1 = T1_reord[:n_ext, n_ext+n_bnd:]
T_be_1 = T1_reord[n_ext:n_ext+n_bnd, :n_ext]
T_bb_1 = T1_reord[n_ext:n_ext+n_bnd, n_ext:n_ext+n_bnd]
T_bi_1 = T1_reord[n_ext:n_ext+n_bnd, n_ext+n_bnd:]
T_ie_1 = T1_reord[n_ext+n_bnd:, :n_ext]
T_ib_1 = T1_reord[n_ext+n_bnd:, n_ext:n_ext+n_bnd]
T_ii_1 = T1_reord[n_ext+n_bnd:, n_ext+n_bnd:]

T_ee_2 = T2_reord[:n_ext, :n_ext]
T_eb_2 = T2_reord[:n_ext, n_ext:n_ext+n_bnd]
T_ei_2 = T2_reord[:n_ext, n_ext+n_bnd:]
T_be_2 = T2_reord[n_ext:n_ext+n_bnd, :n_ext]
T_bb_2 = T2_reord[n_ext:n_ext+n_bnd, n_ext:n_ext+n_bnd]
T_bi_2 = T2_reord[n_ext:n_ext+n_bnd, n_ext+n_bnd:]
T_ie_2 = T2_reord[n_ext+n_bnd:, :n_ext]
T_ib_2 = T2_reord[n_ext+n_bnd:, n_ext:n_ext+n_bnd]
T_ii_2 = T2_reord[n_ext+n_bnd:, n_ext+n_bnd:]

print("Checking which blocks are equal:")
print(f"  T_ee: {np.allclose(T_ee_1, T_ee_2)}")
print(f"  T_eb: {np.allclose(T_eb_1, T_eb_2)}")
print(f"  T_ei: {np.allclose(T_ei_1, T_ei_2)}")
print(f"  T_be: {np.allclose(T_be_1, T_be_2)}")
print(f"  T_bb: {np.allclose(T_bb_1, T_bb_2)}")
print(f"  T_bi: {np.allclose(T_bi_1, T_bi_2)}")
print(f"  T_ie: {np.allclose(T_ie_1, T_ie_2)}")
print(f"  T_ib: {np.allclose(T_ib_1, T_ib_2)}")
print(f"  T_ii: {np.allclose(T_ii_1, T_ii_2)}")
print()

# Key insight: The blocks involving only E_ext and E_bnd should be identical
# because the external graph and boundary edges are the same.

# The only blocks that differ involve E_int.
# But E_int has different edges in G1 vs G2!

# So we need to look at this more carefully.
# Let's check if T_bi and T_ib have a specific structure.

print("=" * 80)
print("ANALYZING THE INTERNAL BLOCK STRUCTURE")
print("=" * 80)
print()

# Internal edges in G1: (v1,w1), (w1,v1), (v2,w2), (w2,v2), plus maybe (v1,v2), (v2,v1), (w1,w2), (w2,w1)
# Internal edges in G2: (v1,w2), (w2,v1), (v2,w1), (w1,v2), plus same parallels

print("Internal edges G1:", E_int1)
print("Internal edges G2:", E_int2)
print()

# The parallel edges (v1,v2), (v2,v1), (w1,w2), (w2,w1) are the SAME in both.
# Only the switch edges differ.

# Let's identify which internal edges are switch edges vs parallel edges
switch_edges_G1 = {(v1, w1), (w1, v1), (v2, w2), (w2, v2)}
switch_edges_G2 = {(v1, w2), (w2, v1), (v2, w1), (w1, v2)}
parallel_edges = set()
if G1.has_edge(v1, v2):
    parallel_edges.update([(v1, v2), (v2, v1)])
if G1.has_edge(w1, w2):
    parallel_edges.update([(w1, w2), (w2, w1)])

print(f"Switch edges G1: {switch_edges_G1 & set(E_int1)}")
print(f"Switch edges G2: {switch_edges_G2 & set(E_int2)}")
print(f"Parallel edges: {parallel_edges & set(E_int1)}")
print()

# Now the key: T_bi connects boundary edges to internal edges.
# For a boundary edge (x, s) where x ∉ S and s ∈ S:
# T_bi[(x,s), (s,t)] = 1/(deg(s)-1) if t ∈ S and t ≠ x

# The structure of T_bi depends on which internal edges exist.
# In G1 vs G2, the switch edges differ, so T_bi differs.

# BUT: The SUM over switch edges should be the same due to degree equality!

# Let's verify: for each boundary edge, the total transition probability to switch edges

print("=" * 80)
print("KEY VERIFICATION: Row sums to switch edges")
print("=" * 80)
print()

# For each boundary edge, compute sum of transitions to switch edges
bnd_to_switch_G1 = {}
bnd_to_switch_G2 = {}

for e_bnd in E_bnd1:
    x, s = e_bnd
    if s not in S:
        x, s = s, x  # Ensure s is the S vertex
        # But actually boundary edges are directed, so this might not be right
        # Let me reconsider
    
    # e_bnd = (u, v) where the edge uv exists and one of u,v is in S
    u, v = e_bnd
    
    # Transitions from (u,v) go to (v, w) for w ∈ N(v) \ {u}
    # If v ∈ S, then w could be in S (internal) or outside S (boundary/external)
    
    if v in S:
        # Transitions to internal edges (v, w) where w ∈ S
        sum_to_switch = 0
        for w in G1.neighbors(v):
            if w != u and w in S:
                e_next = (v, w)
                if e_next in switch_edges_G1:
                    sum_to_switch += 1.0 / (G1.degree(v) - 1)
        bnd_to_switch_G1[e_bnd] = sum_to_switch
    else:
        bnd_to_switch_G1[e_bnd] = 0

for e_bnd in E_bnd2:
    u, v = e_bnd
    
    if v in S:
        sum_to_switch = 0
        for w in G2.neighbors(v):
            if w != u and w in S:
                e_next = (v, w)
                if e_next in switch_edges_G2:
                    sum_to_switch += 1.0 / (G2.degree(v) - 1)
        bnd_to_switch_G2[e_bnd] = sum_to_switch
    else:
        bnd_to_switch_G2[e_bnd] = 0

# Compare
print("Boundary edges with different switch transition sums:")
for e in E_bnd1:
    if e in bnd_to_switch_G1 and e in bnd_to_switch_G2:
        if abs(bnd_to_switch_G1[e] - bnd_to_switch_G2[e]) > 1e-10:
            print(f"  {e}: G1={bnd_to_switch_G1[e]:.4f}, G2={bnd_to_switch_G2[e]:.4f}")

# Total sum
total_G1 = sum(bnd_to_switch_G1.values())
total_G2 = sum(bnd_to_switch_G2.values())
print(f"\nTotal boundary→switch weight: G1={total_G1:.4f}, G2={total_G2:.4f}")
print(f"Equal: {abs(total_G1 - total_G2) < 1e-10}")
