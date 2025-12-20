#!/usr/bin/env python3
"""
Find the TRUE invariants across all 11 NBL-cospectral switches.
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

print("SEARCHING FOR UNIVERSAL INVARIANTS")
print("=" * 80)
print()

# Collect all properties
all_data = []

for idx, (g6_1, g6_2, G, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # Edge counts from unique sets
    edges_u1_shared = sum(1 for x in unique_1 for z in shared if G.has_edge(x, z))
    edges_u2_shared = sum(1 for y in unique_2 for z in shared if G.has_edge(y, z))
    
    edges_u1_v1 = sum(1 for x in unique_1 if G.has_edge(x, v1))
    edges_u1_v2 = sum(1 for x in unique_1 if G.has_edge(x, v2))
    edges_u2_v1 = sum(1 for y in unique_2 if G.has_edge(y, v1))
    edges_u2_v2 = sum(1 for y in unique_2 if G.has_edge(y, v2))
    
    edges_in_u1 = sum(1 for x in unique_1 for y in unique_1 if x < y and G.has_edge(x, y))
    edges_in_u2 = sum(1 for x in unique_2 for y in unique_2 if x < y and G.has_edge(x, y))
    
    edges_u1_u2 = sum(1 for x in unique_1 for y in unique_2 if G.has_edge(x, y))
    
    degs_u1 = sorted([G.degree(x) for x in unique_1])
    degs_u2 = sorted([G.degree(x) for x in unique_2])
    
    data = {
        'idx': idx,
        'g6': g6_1,
        'shared_size': len(shared),
        'unique_sizes_equal': len(unique_1) == len(unique_2),
        'unique_size': len(unique_1),
        'edges_u1_shared': edges_u1_shared,
        'edges_u2_shared': edges_u2_shared,
        'edges_to_shared_equal': edges_u1_shared == edges_u2_shared,
        'edges_u1_v1': edges_u1_v1,
        'edges_u1_v2': edges_u1_v2,
        'edges_u2_v1': edges_u2_v1,
        'edges_u2_v2': edges_u2_v2,
        'edges_u1_to_v': edges_u1_v1 + edges_u1_v2,
        'edges_u2_to_v': edges_u2_v1 + edges_u2_v2,
        'edges_to_v_equal': (edges_u1_v1 + edges_u1_v2) == (edges_u2_v1 + edges_u2_v2),
        'edges_in_u1': edges_in_u1,
        'edges_in_u2': edges_in_u2,
        'edges_within_equal': edges_in_u1 == edges_in_u2,
        'edges_u1_u2': edges_u1_u2,
        'degs_u1': degs_u1,
        'degs_u2': degs_u2,
        'degs_equal': degs_u1 == degs_u2,
        'sum_degs_u1': sum(degs_u1),
        'sum_degs_u2': sum(degs_u2),
        'sum_degs_equal': sum(degs_u1) == sum(degs_u2),
    }
    all_data.append(data)

# Check which properties are invariant across all 11
print("Properties that hold for ALL 11 switches:")
print("-" * 40)

properties_to_check = [
    ('unique_sizes_equal', '|unique_1| = |unique_2|'),
    ('edges_to_shared_equal', 'edges(u1->shared) = edges(u2->shared)'),
    ('edges_to_v_equal', 'edges(u1->V) = edges(u2->V)'),
    ('edges_within_equal', 'edges(within u1) = edges(within u2)'),
    ('degs_equal', 'degree multiset of u1 = degree multiset of u2'),
    ('sum_degs_equal', 'sum of degrees in u1 = sum in u2'),
]

for prop, desc in properties_to_check:
    all_true = all(d[prop] for d in all_data)
    count = sum(1 for d in all_data if d[prop])
    marker = "✓ UNIVERSAL" if all_true else ""
    print(f"  {desc}: {count}/11 {marker}")

print()
print("=" * 80)
print("DETAILED EDGE COUNT ANALYSIS")
print("=" * 80)
print()

for d in all_data:
    print(f"Switch {d['idx']}: {d['g6']}")
    print(f"  |shared|={d['shared_size']}, |unique|={d['unique_size']}")
    print(f"  u1->shared={d['edges_u1_shared']}, u2->shared={d['edges_u2_shared']} (equal: {d['edges_to_shared_equal']})")
    print(f"  u1->V={d['edges_u1_to_v']}, u2->V={d['edges_u2_to_v']} (equal: {d['edges_to_v_equal']})")
    print(f"  within u1={d['edges_in_u1']}, within u2={d['edges_in_u2']} (equal: {d['edges_within_equal']})")
    print(f"  u1<->u2={d['edges_u1_u2']}")
    print(f"  degs(u1)={d['degs_u1']}, degs(u2)={d['degs_u2']} (equal: {d['degs_equal']})")
    print(f"  sum_degs: u1={d['sum_degs_u1']}, u2={d['sum_degs_u2']} (equal: {d['sum_degs_equal']})")
    print()

# Now check: for each switch, is the TOTAL external connectivity of u1 equal to that of u2?
print("=" * 80)
print("TOTAL EXTERNAL CONNECTIVITY CHECK")
print("=" * 80)
print()

for idx, (g6_1, g6_2, G, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    # Total edges from unique_1 to everything outside unique_1
    # = edges to S (w1 only, since unique_1 ⊂ ext(w1)) + edges to shared + edges to unique_2 + edges to "rest"
    
    # Actually, let's compute total edges from each unique set
    total_from_u1 = sum(G.degree(x) for x in unique_1)
    total_from_u2 = sum(G.degree(y) for y in unique_2)
    
    # Edges internal to unique sets
    internal_u1 = 2 * sum(1 for x in unique_1 for y in unique_1 if x < y and G.has_edge(x, y))
    internal_u2 = 2 * sum(1 for x in unique_2 for y in unique_2 if x < y and G.has_edge(x, y))
    
    # External edges from unique sets
    external_from_u1 = total_from_u1 - internal_u1
    external_from_u2 = total_from_u2 - internal_u2
    
    print(f"Switch {idx}: total_deg(u1)={total_from_u1}, total_deg(u2)={total_from_u2}, equal={total_from_u1==total_from_u2}")
    print(f"          external_from(u1)={external_from_u1}, external_from(u2)={external_from_u2}, equal={external_from_u1==external_from_u2}")

conn.close()
