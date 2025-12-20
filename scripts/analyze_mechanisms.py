#!/usr/bin/env python3
"""
Deeper analysis of the 11 switches to identify different mechanisms.

From the first analysis:
- 4 switches satisfy Mechanism A (both parallel edges, |shared|=2)
- 7 switches violate Mechanism A

Let's see if there are other mechanisms at play.
"""

import networkx as nx
import psycopg2
from itertools import permutations

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
                switches.append((g6_1, g6_2, G1, v1, v2, w1, w2))
                break

print("DETAILED MECHANISM ANALYSIS")
print("=" * 80)
print()

# Classify by (has_both_parallel, |shared|) pattern
patterns = {}

for idx, (g6_1, g6_2, G, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    d_v = G.degree(v1)
    d_w = G.degree(w1)
    
    has_v1v2 = G.has_edge(v1, v2)
    has_w1w2 = G.has_edge(w1, w2)
    parallel_count = int(has_v1v2) + int(has_w1w2)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # Cross intersections
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    
    # Degrees in unique sets
    degs_u1 = sorted([G.degree(x) for x in unique_1])
    degs_u2 = sorted([G.degree(x) for x in unique_2])
    
    # Edges within unique sets
    edges_in_u1 = sum(1 for x in unique_1 for y in unique_1 if x < y and G.has_edge(x, y))
    edges_in_u2 = sum(1 for x in unique_2 for y in unique_2 if x < y and G.has_edge(x, y))
    
    # Edges between unique sets
    edges_u1_u2 = sum(1 for x in unique_1 for y in unique_2 if G.has_edge(x, y))
    
    # Edges from unique to shared
    edges_u1_shared = sum(1 for x in unique_1 for z in shared if G.has_edge(x, z))
    edges_u2_shared = sum(1 for y in unique_2 for z in shared if G.has_edge(y, z))
    
    # Edges from unique to v1, v2
    edges_u1_v1 = sum(1 for x in unique_1 if G.has_edge(x, v1))
    edges_u1_v2 = sum(1 for x in unique_1 if G.has_edge(x, v2))
    edges_u2_v1 = sum(1 for y in unique_2 if G.has_edge(y, v1))
    edges_u2_v2 = sum(1 for y in unique_2 if G.has_edge(y, v2))
    
    pattern_key = (parallel_count, len(shared))
    if pattern_key not in patterns:
        patterns[pattern_key] = []
    patterns[pattern_key].append(idx)
    
    print(f"Switch {idx}: {g6_1}")
    print(f"  Parallel edges: {parallel_count} (v1-v2: {has_v1v2}, w1-w2: {has_w1w2})")
    print(f"  |shared|={len(shared)}, |unique_1|={len(unique_1)}, |unique_2|={len(unique_2)}")
    print(f"  Cross: ({c11}, {c12}, {c21}, {c22})")
    print(f"  Degrees: d_v={d_v}, d_w={d_w}")
    print(f"  Unique degrees: u1={degs_u1}, u2={degs_u2}")
    print(f"  Edges within unique: e(u1)={edges_in_u1}, e(u2)={edges_in_u2}")
    print(f"  Edges u1<->u2: {edges_u1_u2}")
    print(f"  Edges to shared: u1->shared={edges_u1_shared}, u2->shared={edges_u2_shared}")
    print(f"  Edges to v's: u1->v1={edges_u1_v1}, u1->v2={edges_u1_v2}, u2->v1={edges_u2_v1}, u2->v2={edges_u2_v2}")
    print()

print("=" * 80)
print("PATTERN CLASSIFICATION: (parallel_count, |shared|)")
print("=" * 80)
for key, indices in sorted(patterns.items()):
    print(f"  {key}: {len(indices)} switches (indices: {indices})")

print()
print("=" * 80)
print("POTENTIAL MECHANISM B: No parallel edges, |shared|=1")
print("=" * 80)

# Look at the switches with no parallel edges
for idx, (g6_1, g6_2, G, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    has_v1v2 = G.has_edge(v1, v2)
    has_w1w2 = G.has_edge(w1, w2)
    
    if has_v1v2 or has_w1w2:
        continue
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # The single shared vertex - is it special?
    if len(shared) == 1:
        z = list(shared)[0]
        # Is z adjacent to v1 and v2?
        z_adj_v1 = G.has_edge(z, v1)
        z_adj_v2 = G.has_edge(z, v2)
        
        print(f"Switch {idx}: shared vertex z={z}")
        print(f"  z adjacent to v1? {z_adj_v1}")
        print(f"  z adjacent to v2? {z_adj_v2}")
        print(f"  z degree: {G.degree(z)}")
        print(f"  unique_1 = {unique_1}, unique_2 = {unique_2}")
        
        # Check: is there a "column edge" connecting ext(v1)∩unique_j to ext(v2)∩unique_j?
        u1_cap_v1 = unique_1 & ext_v1
        u1_cap_v2 = unique_1 & ext_v2
        u2_cap_v1 = unique_2 & ext_v1
        u2_cap_v2 = unique_2 & ext_v2
        
        # Column edges in w1 column: edges between u1_cap_v1 and u1_cap_v2
        col_edges_w1 = [(x, y) for x in u1_cap_v1 for y in u1_cap_v2 if G.has_edge(x, y)]
        col_edges_w2 = [(x, y) for x in u2_cap_v1 for y in u2_cap_v2 if G.has_edge(x, y)]
        
        print(f"  Column edges in w1: {col_edges_w1}")
        print(f"  Column edges in w2: {col_edges_w2}")
        print()

print()
print("=" * 80)
print("CHECKING: Do all 11 switches have uniform cross-intersection?")
print("=" * 80)
all_uniform = True
for idx, (g6_1, g6_2, G, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    
    uniform = (c11 == c12 == c21 == c22)
    if not uniform:
        all_uniform = False
        print(f"Switch {idx}: NOT uniform - ({c11}, {c12}, {c21}, {c22})")

if all_uniform:
    print("YES - All 11 switches have uniform cross-intersection!")

conn.close()
