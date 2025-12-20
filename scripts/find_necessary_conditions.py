#!/usr/bin/env python3
"""
Identify the TRUE necessary conditions for NBL-cospectral 2-edge switches.
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

print(f"Analyzing {len(switches)} NBL-cospectral 2-edge switches")
print("=" * 80)
print()

# Check many potential conditions
conditions = {
    'cond1_deg_v_equal': [],
    'cond1_deg_w_equal': [],
    'cond2_has_v1v2': [],
    'cond2_has_w1w2': [],
    'cond2_both_parallel': [],
    'cond2_at_least_one_parallel': [],
    'cond3_shared_eq_2': [],
    'cond3_shared_geq_1': [],
    'cond4_uniform_cross': [],
    'cond4_column_equal': [],  # c11=c21 and c12=c22
    'cond5_unique_sizes_equal': [],
    'cond5_unique_sizes_eq_2': [],
    'cond6_uniform_unique_deg': [],
    'cond6_deg_multisets_equal': [],
    'cond6_sum_degs_equal': [],
    # New conditions to test
    'edges_u1_to_v_eq_u2_to_v': [],
    'edges_u1_shared_eq_u2_shared': [],
    'edges_within_u1_eq_u2': [],
}

for idx, (g6_1, g6_2, G, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    shared = ext_w1 & ext_w2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    
    degs_u1 = sorted([G.degree(x) for x in unique_1])
    degs_u2 = sorted([G.degree(x) for x in unique_2])
    
    edges_u1_v1 = sum(1 for x in unique_1 if G.has_edge(x, v1))
    edges_u1_v2 = sum(1 for x in unique_1 if G.has_edge(x, v2))
    edges_u2_v1 = sum(1 for y in unique_2 if G.has_edge(y, v1))
    edges_u2_v2 = sum(1 for y in unique_2 if G.has_edge(y, v2))
    
    edges_u1_shared = sum(1 for x in unique_1 for z in shared if G.has_edge(x, z))
    edges_u2_shared = sum(1 for y in unique_2 for z in shared if G.has_edge(y, z))
    
    edges_in_u1 = sum(1 for x in unique_1 for y in unique_1 if x < y and G.has_edge(x, y))
    edges_in_u2 = sum(1 for x in unique_2 for y in unique_2 if x < y and G.has_edge(x, y))
    
    # Record conditions
    conditions['cond1_deg_v_equal'].append(G.degree(v1) == G.degree(v2))
    conditions['cond1_deg_w_equal'].append(G.degree(w1) == G.degree(w2))
    conditions['cond2_has_v1v2'].append(G.has_edge(v1, v2))
    conditions['cond2_has_w1w2'].append(G.has_edge(w1, w2))
    conditions['cond2_both_parallel'].append(G.has_edge(v1, v2) and G.has_edge(w1, w2))
    conditions['cond2_at_least_one_parallel'].append(G.has_edge(v1, v2) or G.has_edge(w1, w2))
    conditions['cond3_shared_eq_2'].append(len(shared) == 2)
    conditions['cond3_shared_geq_1'].append(len(shared) >= 1)
    conditions['cond4_uniform_cross'].append(c11 == c12 == c21 == c22)
    conditions['cond4_column_equal'].append(c11 == c21 and c12 == c22)
    conditions['cond5_unique_sizes_equal'].append(len(unique_1) == len(unique_2))
    conditions['cond5_unique_sizes_eq_2'].append(len(unique_1) == len(unique_2) == 2)
    conditions['cond6_uniform_unique_deg'].append(len(set(degs_u1 + degs_u2)) <= 1)
    conditions['cond6_deg_multisets_equal'].append(degs_u1 == degs_u2)
    conditions['cond6_sum_degs_equal'].append(sum(degs_u1) == sum(degs_u2))
    conditions['edges_u1_to_v_eq_u2_to_v'].append((edges_u1_v1 + edges_u1_v2) == (edges_u2_v1 + edges_u2_v2))
    conditions['edges_u1_shared_eq_u2_shared'].append(edges_u1_shared == edges_u2_shared)
    conditions['edges_within_u1_eq_u2'].append(edges_in_u1 == edges_in_u2)

# Print results
print("CONDITION SATISFACTION ACROSS ALL 11 SWITCHES")
print("-" * 60)
print()

universal = []
partial = []

for cond_name, values in conditions.items():
    count = sum(values)
    if count == len(switches):
        universal.append(cond_name)
        marker = "✓ UNIVERSAL"
    else:
        partial.append((cond_name, count))
        marker = ""
    print(f"{cond_name}: {count}/{len(switches)} {marker}")

print()
print("=" * 80)
print("UNIVERSAL CONDITIONS (hold for ALL 11 cospectral switches)")
print("=" * 80)
for cond in universal:
    print(f"  ✓ {cond}")

print()
print("=" * 80)
print("NON-UNIVERSAL CONDITIONS")
print("=" * 80)
for cond, count in partial:
    print(f"  {cond}: {count}/11")

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("The following conditions are NECESSARY for NBL-cospectral 2-edge switches:")
for cond in universal:
    print(f"  • {cond}")
print()
print("The following Mechanism A conditions are NOT necessary:")
not_necessary = [
    ('cond2_both_parallel', 'Both parallel edges exist'),
    ('cond3_shared_eq_2', '|shared| = 2'),
    ('cond6_uniform_unique_deg', 'All unique vertices have same degree'),
]
for cond, desc in not_necessary:
    if cond not in universal:
        print(f"  • {desc}")

conn.close()
