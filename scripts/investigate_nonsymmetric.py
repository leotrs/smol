#!/usr/bin/env python3
"""
Investigate the 3 switches with non-σ-symmetric first-step matrices.
They must achieve trace equality through a different mechanism.
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

# Focus on switches 0, 1, 10 (non-σ-symmetric) vs 2, 5, 7 (σ-symmetric with |shared|=1)
print("COMPARISON: σ-SYMMETRIC VS NON-σ-SYMMETRIC (|shared|=1 cases)")
print("=" * 80)
print()

for idx in [0, 1, 2, 5, 7, 10]:
    g6_1, g6_2, G1, G2, v1, v2, w1, w2 = switches[idx]
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # Degrees
    degs_u1 = sorted([G1.degree(x) for x in unique_1])
    degs_u2 = sorted([G1.degree(x) for x in unique_2])
    
    # Edges within unique sets
    edges_in_u1 = sum(1 for x in unique_1 for y in unique_1 if x < y and G1.has_edge(x, y))
    edges_in_u2 = sum(1 for x in unique_2 for y in unique_2 if x < y and G1.has_edge(x, y))
    
    # Edges between unique sets
    edges_u1_u2 = sum(1 for x in unique_1 for y in unique_2 if G1.has_edge(x, y))
    
    # Edges from unique to shared
    edges_u1_shared = sum(1 for x in unique_1 for z in shared if G1.has_edge(x, z))
    edges_u2_shared = sum(1 for y in unique_2 for z in shared if G1.has_edge(y, z))
    
    # Edges from unique to v's
    edges_u1_v1 = sum(1 for x in unique_1 if G1.has_edge(x, v1))
    edges_u1_v2 = sum(1 for x in unique_1 if G1.has_edge(x, v2))
    edges_u2_v1 = sum(1 for y in unique_2 if G1.has_edge(y, v1))
    edges_u2_v2 = sum(1 for y in unique_2 if G1.has_edge(y, v2))
    
    # Shared vertex adjacency to v's
    edges_shared_v1 = sum(1 for z in shared if G1.has_edge(z, v1))
    edges_shared_v2 = sum(1 for z in shared if G1.has_edge(z, v2))
    
    has_v1v2 = G1.has_edge(v1, v2)
    has_w1w2 = G1.has_edge(w1, w2)
    
    # Determine if σ-symmetric based on previous analysis
    is_symmetric = idx in [2, 5, 7]
    
    print(f"Switch {idx}: {'σ-SYMMETRIC' if is_symmetric else 'NOT σ-symmetric'}")
    print(f"  G1: {g6_1}")
    print(f"  Vertices: v1={v1}, v2={v2}, w1={w1}, w2={w2}")
    print(f"  Parallel: v1-v2={has_v1v2}, w1-w2={has_w1w2}")
    print(f"  shared={shared}, unique_1={unique_1}, unique_2={unique_2}")
    print(f"  Degrees: u1={degs_u1}, u2={degs_u2}, uniform={degs_u1==degs_u2}")
    print(f"  Edges within unique: u1={edges_in_u1}, u2={edges_in_u2}, equal={edges_in_u1==edges_in_u2}")
    print(f"  Edges u1<->u2: {edges_u1_u2}")
    print(f"  Edges to shared: u1->sh={edges_u1_shared}, u2->sh={edges_u2_shared}")
    print(f"  Edges to v's: u1->v1={edges_u1_v1}, u1->v2={edges_u1_v2}, u2->v1={edges_u2_v1}, u2->v2={edges_u2_v2}")
    print(f"  Shared to v's: sh->v1={edges_shared_v1}, sh->v2={edges_shared_v2}")
    print()

# Now let's look at why the non-symmetric ones still work
print("=" * 80)
print("ANALYZING NON-σ-SYMMETRIC SWITCHES")
print("=" * 80)
print()

for idx in [0, 1, 10]:
    g6_1, g6_2, G1, G2, v1, v2, w1, w2 = switches[idx]
    
    T1, edges1, e2i1 = build_nbl_matrix(G1)
    T2, edges2, e2i2 = build_nbl_matrix(G2)
    
    print(f"Switch {idx}: {g6_1}")
    
    # Compare T^k diagonal sums by edge type
    S = {v1, v2, w1, w2}
    
    # Classify edges by whether they involve S
    def classify_edge(e, G, v1, v2, w1, w2):
        a, b = e
        if a in S and b in S:
            return 'internal'
        elif a in S or b in S:
            return 'boundary'
        else:
            return 'external'
    
    # Compare diagonal contributions from different edge types
    print(f"  Diagonal sum by edge type for T^k:")
    
    Tk1 = np.eye(len(edges1))
    Tk2 = np.eye(len(edges2))
    
    for k in range(1, 8):
        Tk1 = Tk1 @ T1
        Tk2 = Tk2 @ T2
        
        # Sum diagonal by edge type
        diag_internal_1 = sum(Tk1[i,i] for i, e in enumerate(edges1) if classify_edge(e, G1, v1, v2, w1, w2) == 'internal')
        diag_boundary_1 = sum(Tk1[i,i] for i, e in enumerate(edges1) if classify_edge(e, G1, v1, v2, w1, w2) == 'boundary')
        diag_external_1 = sum(Tk1[i,i] for i, e in enumerate(edges1) if classify_edge(e, G1, v1, v2, w1, w2) == 'external')
        
        diag_internal_2 = sum(Tk2[i,i] for i, e in enumerate(edges2) if classify_edge(e, G2, v1, v2, w1, w2) == 'internal')
        diag_boundary_2 = sum(Tk2[i,i] for i, e in enumerate(edges2) if classify_edge(e, G2, v1, v2, w1, w2) == 'boundary')
        diag_external_2 = sum(Tk2[i,i] for i, e in enumerate(edges2) if classify_edge(e, G2, v1, v2, w1, w2) == 'external')
        
        total_1 = diag_internal_1 + diag_boundary_1 + diag_external_1
        total_2 = diag_internal_2 + diag_boundary_2 + diag_external_2
        
        print(f"    k={k}: G1=(int:{diag_internal_1:.4f}, bnd:{diag_boundary_1:.4f}, ext:{diag_external_1:.4f}) = {total_1:.4f}")
        print(f"         G2=(int:{diag_internal_2:.4f}, bnd:{diag_boundary_2:.4f}, ext:{diag_external_2:.4f}) = {total_2:.4f}")
        print(f"         diff: int={diag_internal_1-diag_internal_2:.4f}, bnd={diag_boundary_1-diag_boundary_2:.4f}, ext={diag_external_1-diag_external_2:.4f}")
    
    print()

conn.close()
