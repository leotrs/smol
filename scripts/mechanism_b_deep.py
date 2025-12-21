#!/usr/bin/env python3
"""
Deep investigation of Mechanism B switches.
Goal: Find the exact condition that makes non-σ-symmetric switches cospectral.
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

# Focus on the 3 non-σ-symmetric switches
mech_b_g6 = ['ICQbeZqz?', 'ICQfAxuv?', 'ICXmeqsWw']
mech_b = [(g6_1, g6_2, G1, G2, v1, v2, w1, w2) for g6_1, g6_2, G1, G2, v1, v2, w1, w2 in switches if g6_1 in mech_b_g6]

print("MECHANISM B DEEP ANALYSIS")
print("=" * 80)
print()

for g6_1, g6_2, G1, G2, v1, v2, w1, w2 in mech_b:
    print(f"Switch: {g6_1}")
    print(f"  v1={v1}, v2={v2}, w1={w1}, w2={w2}")
    
    S = {v1, v2, w1, w2}
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    print(f"  shared={shared}")
    print(f"  unique_1={unique_1}, unique_2={unique_2}")
    
    # For each external vertex, print its full adjacency
    print("  External vertex adjacencies:")
    all_ext = ext_v1 | ext_v2 | ext_w1 | ext_w2
    for x in sorted(all_ext):
        adj_in_S = [s for s in S if G1.has_edge(x, s)]
        adj_ext = [y for y in all_ext if G1.has_edge(x, y) and y != x]
        print(f"    {x} (deg={G1.degree(x)}): in_S={adj_in_S}, ext={adj_ext}")
    
    # Check if there's an automorphism of the external graph
    # that swaps unique_1 with unique_2 and fixes shared
    print("\n  Checking for external symmetry...")
    
    # Build the external graph (vertices = all_ext, edges = edges between them)
    ext_graph = G1.subgraph(all_ext).copy()
    
    # Add "type" attribute to each vertex
    for x in ext_graph.nodes():
        if x in shared:
            ext_graph.nodes[x]['type'] = 'shared'
        elif x in unique_1:
            ext_graph.nodes[x]['type'] = 'u1'
        elif x in unique_2:
            ext_graph.nodes[x]['type'] = 'u2'
        else:
            ext_graph.nodes[x]['type'] = 'other'
        
        # Also record adjacency to S
        ext_graph.nodes[x]['adj_v1'] = G1.has_edge(x, v1)
        ext_graph.nodes[x]['adj_v2'] = G1.has_edge(x, v2)
        ext_graph.nodes[x]['adj_w1'] = G1.has_edge(x, w1)
        ext_graph.nodes[x]['adj_w2'] = G1.has_edge(x, w2)
    
    # Look for a mapping u1 <-> u2 that preserves the structure
    u1_list = sorted(unique_1)
    u2_list = sorted(unique_2)
    
    print(f"  u1_list={u1_list}, u2_list={u2_list}")
    
    # Try all bijections from u1 to u2
    from itertools import permutations as perms
    
    valid_mappings = []
    for perm in perms(u2_list):
        mapping = dict(zip(u1_list, perm))
        # Extend mapping to fix shared vertices
        for z in shared:
            mapping[z] = z
        
        # Check if this mapping preserves:
        # 1. Edges within ext_graph
        # 2. Adjacency to v1, v2 (with swapped roles)
        
        valid = True
        
        # Check edges within u1, u2
        for x in u1_list:
            for y in u1_list:
                if x < y:
                    edge_in_u1 = ext_graph.has_edge(x, y)
                    edge_in_u2 = ext_graph.has_edge(mapping[x], mapping[y])
                    if edge_in_u1 != edge_in_u2:
                        valid = False
                        break
            if not valid:
                break
        
        if not valid:
            continue
        
        # Check edges between u1 and shared vs u2 and shared
        for x in u1_list:
            for z in shared:
                edge_u1_sh = ext_graph.has_edge(x, z)
                edge_u2_sh = ext_graph.has_edge(mapping[x], z)
                if edge_u1_sh != edge_u2_sh:
                    valid = False
                    break
            if not valid:
                break
        
        if not valid:
            continue
        
        # Check edges between u1 and u2
        for x in u1_list:
            for y in u2_list:
                # Edge x-y should map to edge mapping[x]-mapping^{-1}[y]
                # But since we're mapping u1->u2, this is tricky
                # Actually, edges between u1 and u2 don't need to be preserved
                # because in both G and G', these edges are the same
                pass
        
        # Check adjacency to v1, v2 (with swap)
        for x in u1_list:
            adj_v1_x = ext_graph.nodes[x]['adj_v1']
            adj_v2_x = ext_graph.nodes[x]['adj_v2']
            adj_v1_mx = ext_graph.nodes[mapping[x]]['adj_v1']
            adj_v2_mx = ext_graph.nodes[mapping[x]]['adj_v2']
            
            # Under σ: v1 <-> v2, so x->v1 should match mapping[x]->v2
            if adj_v1_x != adj_v2_mx or adj_v2_x != adj_v1_mx:
                valid = False
                break
        
        if valid:
            valid_mappings.append(mapping)
    
    if valid_mappings:
        print(f"  Found {len(valid_mappings)} valid u1<->u2 mapping(s)!")
        for m in valid_mappings:
            print(f"    {m}")
    else:
        print("  No valid u1<->u2 mapping found!")
    
    # NEW: Check if the shared vertex(s) have a special structure
    print("\n  Shared vertex analysis:")
    for z in shared:
        adj_v1 = G1.has_edge(z, v1)
        adj_v2 = G1.has_edge(z, v2)
        print(f"    z={z}: adj_v1={adj_v1}, adj_v2={adj_v2}")
        
        # Neighbors of z in external graph
        z_ext_neighbors = [y for y in all_ext if G1.has_edge(z, y) and y != z]
        print(f"    z={z}: ext_neighbors={z_ext_neighbors}")
    
    print()

# Now check: what if we use a DIFFERENT permutation σ?
# Instead of swapping v1<->v2, what if we swap based on the actual structure?

print("=" * 80)
print("ALTERNATIVE PERMUTATION ANALYSIS")
print("=" * 80)
print()

for g6_1, g6_2, G1, G2, v1, v2, w1, w2 in mech_b:
    print(f"Switch: {g6_1}")
    
    S = {v1, v2, w1, w2}
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # What if the "swap" is not v1<->v2 but something else?
    # In particular, for these switches, maybe the swap should be w1<->w2?
    
    # Under w1<->w2 swap:
    # - shared stays shared
    # - unique_1 becomes unique_2 and vice versa
    # - v1 and v2 stay fixed
    
    # This is the σ permutation we've been using!
    # But maybe the issue is that the external matrix P is symmetric under a DIFFERENT permutation
    
    # Let's compute P under the identity (no swap on v's) and see if u1<->u2 works alone
    
    print("  Testing if P is symmetric under u1<->u2 swap only (fixing v1,v2):")
    
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
    
    # Check symmetry under different permutations
    types = ['v1', 'v2', 'shared', 'u1', 'u2']
    
    # Permutation 1: swap v1<->v2, u1<->u2
    def sigma1(t):
        if t == 'v1': return 'v2'
        if t == 'v2': return 'v1'
        if t == 'shared': return 'shared'
        if t == 'u1': return 'u2'
        if t == 'u2': return 'u1'
    
    # Permutation 2: swap u1<->u2 only
    def sigma2(t):
        if t == 'v1': return 'v1'
        if t == 'v2': return 'v2'
        if t == 'shared': return 'shared'
        if t == 'u1': return 'u2'
        if t == 'u2': return 'u1'
    
    # Permutation 3: swap v1<->v2 only
    def sigma3(t):
        if t == 'v1': return 'v2'
        if t == 'v2': return 'v1'
        if t == 'shared': return 'shared'
        if t == 'u1': return 'u1'
        if t == 'u2': return 'u2'
    
    for name, sigma in [('v1<->v2, u1<->u2', sigma1), ('u1<->u2 only', sigma2), ('v1<->v2 only', sigma3)]:
        symmetric = True
        for ft in types:
            for tt in types:
                if abs(P[ft][tt] - P[sigma(ft)][sigma(tt)]) > 1e-10:
                    symmetric = False
                    break
            if not symmetric:
                break
        print(f"    {name}: {'symmetric' if symmetric else 'NOT symmetric'}")
    
    # Print the P matrix
    print("  P matrix:")
    for ft in types:
        row = [f"{P[ft][tt]:.3f}" for tt in types]
        print(f"    {ft}: {row}")
    
    print()

conn.close()
