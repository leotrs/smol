#!/usr/bin/env python3
"""
Investigate the deep structure that makes all 11 switches NBL-cospectral.
Focus on finding the common mechanism.
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

print("DEEP STRUCTURE ANALYSIS")
print("=" * 80)
print()

# For each switch, analyze the LOCAL structure around v1, v2, w1, w2
for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # Partition the external vertices
    # A vertex can be in: ext(v1) only, ext(v2) only, both ext(v1) and ext(v2), or neither
    # Combined with: shared, unique_1, unique_2, or "other"
    
    # Key insight: vertices in unique_j connect to wj but not to w_{3-j}
    # The switch swaps which w they connect to from the v's perspective
    
    # Let's look at the FULL external vertex classification
    all_ext = ext_v1 | ext_v2 | ext_w1 | ext_w2
    
    print(f"Switch {idx}: {g6_1}")
    print(f"  S = {{{v1}, {v2}, {w1}, {w2}}}")
    print(f"  Degrees: d_v={G1.degree(v1)}, d_w={G1.degree(w1)}")
    
    # For each external vertex, compute its "type"
    vertex_types = {}
    for x in all_ext:
        in_v1 = x in ext_v1
        in_v2 = x in ext_v2
        in_w1 = x in ext_w1
        in_w2 = x in ext_w2
        
        type_str = ""
        if in_v1: type_str += "v1"
        if in_v2: type_str += "v2"
        if in_w1: type_str += "w1"
        if in_w2: type_str += "w2"
        
        vertex_types[x] = type_str
    
    # Group vertices by type
    types_to_verts = defaultdict(set)
    for x, t in vertex_types.items():
        types_to_verts[t].add(x)
    
    print("  External vertex types:")
    for t in sorted(types_to_verts.keys()):
        verts = types_to_verts[t]
        degs = [G1.degree(x) for x in verts]
        print(f"    {t}: {len(verts)} vertices, degrees={sorted(degs)}")
    
    # Key observation: the switch swaps w1 <-> w2 in edge connections
    # So vertices with type containing "w1" but not "w2" should pair with
    # vertices with type containing "w2" but not "w1"
    
    # Check the "w1 only" vs "w2 only" pairing
    w1_only_types = [t for t in types_to_verts if 'w1' in t and 'w2' not in t]
    w2_only_types = [t for t in types_to_verts if 'w2' in t and 'w1' not in t]
    
    print(f"  w1-only types: {w1_only_types}")
    print(f"  w2-only types: {w2_only_types}")
    
    # For each w1-only type, find its "partner" w2-only type
    for t1 in w1_only_types:
        t2 = t1.replace('w1', 'w2')
        if t2 in types_to_verts:
            v1_set = types_to_verts[t1]
            v2_set = types_to_verts[t2]
            degs1 = sorted([G1.degree(x) for x in v1_set])
            degs2 = sorted([G1.degree(x) for x in v2_set])
            match = "✓" if len(v1_set) == len(v2_set) and degs1 == degs2 else "≈" if len(v1_set) == len(v2_set) else "✗"
            print(f"    {t1} <-> {t2}: |{len(v1_set)}|={len(v2_set)}| {match}, degs: {degs1} vs {degs2}")
    
    print()

# Now let's check: what exactly are the types present in each switch?
print("=" * 80)
print("TYPE CARDINALITY COMPARISON")
print("=" * 80)
print()

# Collect all types seen across all switches
all_types_seen = set()
for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    all_ext = ext_v1 | ext_v2 | ext_w1 | ext_w2
    
    for x in all_ext:
        type_str = ""
        if x in ext_v1: type_str += "v1"
        if x in ext_v2: type_str += "v2"
        if x in ext_w1: type_str += "w1"
        if x in ext_w2: type_str += "w2"
        all_types_seen.add(type_str)

print(f"All external vertex types seen: {sorted(all_types_seen)}")
print()

# For each switch, check if cardinalities match between paired types
print("Cardinality matching for paired types:")
all_match = True
for idx, (g6_1, g6_2, G1, G2, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    ext_v1 = set(x for x in G1.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G1.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G1.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G1.neighbors(w2) if x not in S)
    all_ext = ext_v1 | ext_v2 | ext_w1 | ext_w2
    
    types_to_verts = defaultdict(set)
    for x in all_ext:
        type_str = ""
        if x in ext_v1: type_str += "v1"
        if x in ext_v2: type_str += "v2"
        if x in ext_w1: type_str += "w1"
        if x in ext_w2: type_str += "w2"
        types_to_verts[type_str].add(x)
    
    # Check pairs
    issues = []
    for t1 in types_to_verts:
        if 'w1' in t1 and 'w2' not in t1:
            t2 = t1.replace('w1', 'w2')
            n1 = len(types_to_verts[t1])
            n2 = len(types_to_verts.get(t2, set()))
            if n1 != n2:
                issues.append(f"{t1}:{n1} vs {t2}:{n2}")
                all_match = False
    
    if issues:
        print(f"  Switch {idx}: MISMATCH - {issues}")
    else:
        print(f"  Switch {idx}: ✓ All paired types have equal cardinality")

print()
if all_match:
    print("*** ALL 11 SWITCHES have matching cardinalities for paired types! ***")

conn.close()
