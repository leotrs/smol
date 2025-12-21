#!/usr/bin/env python3
"""
Deep analysis: understand WHY traces match for all 11 switches.
Key insight: the trace counts closed walks, and we need to understand
how closed walks are preserved under the switch.
"""

import networkx as nx
import numpy as np
import psycopg2
from itertools import permutations
from collections import defaultdict

def build_nbl_matrix(G):
    """Build NBL transition matrix."""
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

print("BOUNDARY TYPE ANALYSIS")
print("=" * 80)
print()

# For each switch, compute the boundary structure and check σ-symmetry
for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
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
    
    # The key question: what is the first-step transition matrix P from exit types to entry types?
    # P[exit_type, entry_type] = sum over edges of that type
    
    # Types: v1, v2, w1_s, w2_s, w1_u, w2_u
    # For |shared|=1, we have w1_s = w2_s = {z} (the single shared vertex)
    
    print(f"Switch {idx}: {g6_1}")
    print(f"  |shared|={len(shared)}, parallel=(v1v2:{has_v1v2}, w1w2:{has_w1w2})")
    print(f"  shared={shared}, unique_1={unique_1}, unique_2={unique_2}")
    
    # Compute the first-step matrix from each boundary region
    # From v1 (exit) to various entry types
    
    # Exit from v1 means edge (v1, x) for x in ext_v1
    # Entry to v1 means edge (y, v1) for y in ext_v1
    
    # For each external vertex x, determine which types it belongs to
    def get_vertex_types(x):
        types = []
        if x in ext_v1:
            types.append('v1')
        if x in ext_v2:
            types.append('v2')
        if x in shared:
            types.append('shared')
        if x in unique_1:
            types.append('u1')
        if x in unique_2:
            types.append('u2')
        return types
    
    # Compute the first-step matrix
    # P[from_type][to_type] = total transition weight
    from_types = ['v1', 'v2', 'shared', 'u1', 'u2']
    to_types = ['v1', 'v2', 'shared', 'u1', 'u2']
    
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    
    P = defaultdict(lambda: defaultdict(float))
    
    # For each exit edge (s, x) where s in S and x not in S
    for s in S:
        ext_s = set(y for y in G1.neighbors(s) if y not in S)
        for x in ext_s:
            exit_edge = (s, x)
            if exit_edge not in e2i1:
                continue
            exit_idx = e2i1[exit_edge]
            
            # Determine exit type
            if s == v1:
                exit_type = 'v1'
            elif s == v2:
                exit_type = 'v2'
            elif s == w1:
                if x in shared:
                    exit_type = 'shared'  # from w1 to shared
                else:
                    exit_type = 'u1'  # from w1 to unique_1
            elif s == w2:
                if x in shared:
                    exit_type = 'shared'  # from w2 to shared
                else:
                    exit_type = 'u2'  # from w2 to unique_2
            
            # Find all entry edges this can transition to
            for entry_idx in range(len(edges1)):
                if T1[exit_idx, entry_idx] > 0:
                    entry_edge = edges1[entry_idx]
                    y, t = entry_edge  # edge (y, t)
                    
                    if t not in S:
                        continue  # Not an entry edge
                    
                    # Determine entry type
                    if t == v1:
                        entry_type = 'v1'
                    elif t == v2:
                        entry_type = 'v2'
                    elif t == w1:
                        if y in shared:
                            entry_type = 'shared'
                        else:
                            entry_type = 'u1'
                    elif t == w2:
                        if y in shared:
                            entry_type = 'shared'
                        else:
                            entry_type = 'u2'
                    else:
                        continue
                    
                    P[exit_type][entry_type] += T1[exit_idx, entry_idx]
    
    print("  First-step matrix P (exit -> entry):")
    for ft in from_types:
        row = [P[ft][tt] for tt in to_types]
        print(f"    {ft}: {[f'{x:.4f}' for x in row]}")
    
    # Check σ-symmetry: P[τ, ρ] = P[σ(τ), σ(ρ)]
    # σ: v1 <-> v2, shared <-> shared, u1 <-> u2
    def sigma(t):
        if t == 'v1': return 'v2'
        if t == 'v2': return 'v1'
        if t == 'shared': return 'shared'
        if t == 'u1': return 'u2'
        if t == 'u2': return 'u1'
    
    symmetric = True
    for ft in from_types:
        for tt in to_types:
            val1 = P[ft][tt]
            val2 = P[sigma(ft)][sigma(tt)]
            if abs(val1 - val2) > 1e-10:
                symmetric = False
                print(f"  ✗ Asymmetry: P[{ft},{tt}]={val1:.4f} != P[{sigma(ft)},{sigma(tt)}]={val2:.4f}")
    
    if symmetric:
        print("  ✓ First-step matrix is σ-symmetric!")
    
    print()

conn.close()
