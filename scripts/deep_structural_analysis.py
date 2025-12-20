#!/usr/bin/env python3
"""
Deep structural analysis of all 11 switches to find the underlying mechanisms.
"""

import networkx as nx
import psycopg2
from itertools import permutations
import numpy as np

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

# Find 2-edge switches
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

print("COMPLETE STRUCTURAL ANALYSIS OF ALL 11 SWITCHES")
print("=" * 80)
print()

# Classify by mechanism
mechanism_a = []  # Both parallel, |shared|=2, uniform unique deg
mechanism_b_candidates = []  # Others

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
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # Cross intersections
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    
    # Degrees
    degs_u1 = sorted([G.degree(x) for x in unique_1])
    degs_u2 = sorted([G.degree(x) for x in unique_2])
    
    # Edge counts - detailed breakdown
    # From unique to S
    edges_u1_w1 = len(unique_1)  # All in unique_1 are adjacent to w1
    edges_u2_w2 = len(unique_2)  # All in unique_2 are adjacent to w2
    edges_u1_v1 = sum(1 for x in unique_1 if G.has_edge(x, v1))
    edges_u1_v2 = sum(1 for x in unique_1 if G.has_edge(x, v2))
    edges_u2_v1 = sum(1 for y in unique_2 if G.has_edge(y, v1))
    edges_u2_v2 = sum(1 for y in unique_2 if G.has_edge(y, v2))
    
    # From unique to shared
    edges_u1_shared = sum(1 for x in unique_1 for z in shared if G.has_edge(x, z))
    edges_u2_shared = sum(1 for y in unique_2 for z in shared if G.has_edge(y, z))
    
    # Within unique
    edges_in_u1 = sum(1 for x in unique_1 for y in unique_1 if x < y and G.has_edge(x, y))
    edges_in_u2 = sum(1 for x in unique_2 for y in unique_2 if x < y and G.has_edge(x, y))
    
    # Between unique sets
    edges_u1_u2 = sum(1 for x in unique_1 for y in unique_2 if G.has_edge(x, y))
    
    # From shared to v's
    edges_shared_v1 = sum(1 for z in shared if G.has_edge(z, v1))
    edges_shared_v2 = sum(1 for z in shared if G.has_edge(z, v2))
    
    # Shared vertex degrees
    degs_shared = sorted([G.degree(z) for z in shared]) if shared else []
    
    # Internal S structure
    # Count edges within S (besides the switched edges)
    internal_edges = []
    if has_v1v2:
        internal_edges.append('v1-v2')
    if has_w1w2:
        internal_edges.append('w1-w2')
    if G.has_edge(v1, w2):
        internal_edges.append('v1-w2')
    if G.has_edge(v2, w1):
        internal_edges.append('v2-w1')
    
    # Mechanism A check
    is_mech_a = (has_v1v2 and has_w1w2 and len(shared) == 2 and 
                 c11 == c12 == c21 == c22 and
                 len(unique_1) == len(unique_2) == 2 and
                 len(set(degs_u1 + degs_u2)) == 1)
    
    data = {
        'idx': idx,
        'g6': g6_1,
        'd_v': d_v,
        'd_w': d_w,
        'has_v1v2': has_v1v2,
        'has_w1w2': has_w1w2,
        'internal_edges': internal_edges,
        'shared': shared,
        'shared_size': len(shared),
        'unique_1': unique_1,
        'unique_2': unique_2,
        'cross': (c11, c12, c21, c22),
        'degs_u1': degs_u1,
        'degs_u2': degs_u2,
        'degs_shared': degs_shared,
        'edges_u1_v1': edges_u1_v1,
        'edges_u1_v2': edges_u1_v2,
        'edges_u2_v1': edges_u2_v1,
        'edges_u2_v2': edges_u2_v2,
        'edges_u1_shared': edges_u1_shared,
        'edges_u2_shared': edges_u2_shared,
        'edges_in_u1': edges_in_u1,
        'edges_in_u2': edges_in_u2,
        'edges_u1_u2': edges_u1_u2,
        'edges_shared_v1': edges_shared_v1,
        'edges_shared_v2': edges_shared_v2,
        'is_mech_a': is_mech_a,
    }
    
    if is_mech_a:
        mechanism_a.append(data)
    else:
        mechanism_b_candidates.append(data)
    
    print(f"Switch {idx}: {g6_1}")
    print(f"  S-structure: v1-v2:{has_v1v2}, w1-w2:{has_w1w2}, internal:{internal_edges}")
    print(f"  Degrees: d_v={d_v}, d_w={d_w}")
    print(f"  |shared|={len(shared)}, shared={shared}, degs_shared={degs_shared}")
    print(f"  unique_1={unique_1}, unique_2={unique_2}")
    print(f"  degs_u1={degs_u1}, degs_u2={degs_u2}")
    print(f"  Cross: ({c11},{c12},{c21},{c22})")
    print(f"  Edges u->v: u1->v1={edges_u1_v1}, u1->v2={edges_u1_v2}, u2->v1={edges_u2_v1}, u2->v2={edges_u2_v2}")
    print(f"  Edges u->shared: u1->sh={edges_u1_shared}, u2->sh={edges_u2_shared}")
    print(f"  Edges within u: e(u1)={edges_in_u1}, e(u2)={edges_in_u2}")
    print(f"  Edges u1<->u2: {edges_u1_u2}")
    print(f"  Edges shared->v: sh->v1={edges_shared_v1}, sh->v2={edges_shared_v2}")
    print(f"  => {'MECHANISM A' if is_mech_a else 'MECHANISM B candidate'}")
    print()

print("=" * 80)
print(f"MECHANISM A: {len(mechanism_a)} switches")
print(f"MECHANISM B candidates: {len(mechanism_b_candidates)} switches")
print("=" * 80)
print()

# Analyze Mechanism B candidates
print("MECHANISM B CANDIDATE ANALYSIS")
print("=" * 80)
print()

# Find common patterns
print("Looking for common patterns among non-Mechanism-A switches...")
print()

# Check various symmetry conditions
for d in mechanism_b_candidates:
    idx = d['idx']
    print(f"Switch {idx}: {d['g6']}")
    
    # Check: edges_u1_v1 + edges_u1_v2 = edges_u2_v1 + edges_u2_v2 (known universal)
    u1_to_v = d['edges_u1_v1'] + d['edges_u1_v2']
    u2_to_v = d['edges_u2_v1'] + d['edges_u2_v2']
    print(f"  u1->V total: {u1_to_v}, u2->V total: {u2_to_v}, equal: {u1_to_v == u2_to_v}")
    
    # Check: more detailed symmetry
    # Is there a "twisted" symmetry where edges_u1_v1 = edges_u2_v2 and edges_u1_v2 = edges_u2_v1?
    twisted = (d['edges_u1_v1'] == d['edges_u2_v2']) and (d['edges_u1_v2'] == d['edges_u2_v1'])
    direct = (d['edges_u1_v1'] == d['edges_u2_v1']) and (d['edges_u1_v2'] == d['edges_u2_v2'])
    print(f"  Twisted symmetry (u1v1=u2v2, u1v2=u2v1): {twisted}")
    print(f"  Direct symmetry (u1v1=u2v1, u1v2=u2v2): {direct}")
    
    # Check degree sum symmetry
    sum_u1 = sum(d['degs_u1'])
    sum_u2 = sum(d['degs_u2'])
    print(f"  Sum degrees: u1={sum_u1}, u2={sum_u2}, equal: {sum_u1 == sum_u2}")
    
    # External connectivity balance
    # Total edges from u1 to outside u1 = edges to w1 + edges to v's + edges to shared + edges to u2
    ext_u1 = len(d['unique_1']) + u1_to_v + d['edges_u1_shared'] + d['edges_u1_u2']
    ext_u2 = len(d['unique_2']) + u2_to_v + d['edges_u2_shared'] + d['edges_u1_u2']
    print(f"  External edges from u1: {ext_u1}, from u2: {ext_u2}")
    
    # Total degree = internal + external
    total_u1 = sum_u1
    total_u2 = sum_u2
    internal_u1 = 2 * d['edges_in_u1']
    internal_u2 = 2 * d['edges_in_u2']
    print(f"  Internal degree u1: {internal_u1}, u2: {internal_u2}")
    print()

print("=" * 80)
print("CHECKING FOR GENERALIZED SYMMETRY CONDITIONS")
print("=" * 80)
print()

# For each switch, compute the "balance" equations
for d in mechanism_b_candidates:
    idx = d['idx']
    print(f"Switch {idx}:")
    
    # The key insight: for NBL cospectrality, the TOTAL flow through boundary types must match
    # Let's compute various "flow" quantities
    
    # Flow from unique_1 to the v-side vs unique_2 to the v-side
    # This should be balanced in some way
    
    # Quantity 1: |ext(v1) ∩ unique_1| vs |ext(v1) ∩ unique_2|
    # By uniform cross-intersection, these are equal!
    c = d['cross'][0]  # All cross values are equal
    print(f"  Cross-intersection c = {c}")
    print(f"  |ext(v1) ∩ unique_1| = |ext(v1) ∩ unique_2| = c - |ext(v1) ∩ shared|")
    
    # The shared vertex is key
    print(f"  Shared vertices: {d['shared']}")
    print(f"  Edges shared->v1: {d['edges_shared_v1']}, shared->v2: {d['edges_shared_v2']}")
    
    # Does the single shared vertex connect equally to v1 and v2?
    if d['shared_size'] == 1:
        z = list(d['shared'])[0]
        z_v1 = d['edges_shared_v1']
        z_v2 = d['edges_shared_v2']
        print(f"  Single shared vertex z connects to: v1={z_v1}, v2={z_v2}")
    print()

conn.close()
