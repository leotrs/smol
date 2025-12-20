#!/usr/bin/env python3
"""
Comprehensive analysis of ALL 78 NBL-cospectral pairs (n=10, min_degree>=2).

Goal: Test whether condition 3 (|shared|=2) is necessary for NBL-cospectrality
in 2-edge switches, and characterize the non-switch pairs.
"""

import networkx as nx
import psycopg2
from itertools import permutations
from collections import defaultdict

conn = psycopg2.connect('dbname=smol')
cur = conn.cursor()

# Get ALL 78 NBL-cospectral pairs with min_degree >= 2
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

print(f"Total NBL-cospectral pairs (n=10, min_degree>=2): {len(pairs)}")
print("=" * 80)
print()

# Classify each pair
two_edge_switches = []
non_switches = []

for g6_1, g6_2 in pairs:
    G1 = nx.from_graph6_bytes(g6_1.encode())
    G2 = nx.from_graph6_bytes(g6_2.encode())
    E1 = set(frozenset(e) for e in G1.edges())
    E2 = set(frozenset(e) for e in G2.edges())
    only_in_G1 = E1 - E2
    only_in_G2 = E2 - E1
    
    edge_diff = len(only_in_G1)
    
    if edge_diff != 2:
        non_switches.append((g6_1, g6_2, G1, G2, edge_diff))
        continue
    
    # Check if it's a valid 2-edge switch
    verts = set()
    for e in only_in_G1 | only_in_G2:
        verts.update(e)
    
    if len(verts) != 4:
        non_switches.append((g6_1, g6_2, G1, G2, edge_diff))
        continue
    
    # Find the switch labeling
    found = False
    for perm in permutations(verts):
        v1, v2, w1, w2 = perm
        e1 = frozenset([v1, w1])
        e2 = frozenset([v2, w2])
        new_e1 = frozenset([v1, w2])
        new_e2 = frozenset([v2, w1])
        
        if only_in_G1 == {e1, e2} and only_in_G2 == {new_e1, new_e2}:
            if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                two_edge_switches.append((g6_1, g6_2, G1, v1, v2, w1, w2))
                found = True
                break
    
    if not found:
        non_switches.append((g6_1, g6_2, G1, G2, edge_diff))

print(f"2-edge switches: {len(two_edge_switches)}")
print(f"Non-switches: {len(non_switches)}")
print()

# Analyze 2-edge switches for Mechanism A conditions
print("=" * 80)
print("ANALYSIS OF 2-EDGE SWITCHES")
print("=" * 80)
print()

shared_distribution = defaultdict(list)
mechanism_a_satisfied = []

for idx, (g6_1, g6_2, G, v1, v2, w1, w2) in enumerate(two_edge_switches):
    S = {v1, v2, w1, w2}
    
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    d_v = G.degree(v1)
    d_w = G.degree(w1)
    
    # Condition 1: Degree equality (always true by construction)
    cond1 = True
    
    # Condition 2: Both parallel edges
    has_v1v2 = G.has_edge(v1, v2)
    has_w1w2 = G.has_edge(w1, w2)
    cond2 = has_v1v2 and has_w1w2
    
    # Condition 3: |shared| = 2
    shared = ext_w1 & ext_w2
    cond3_val = len(shared)
    cond3 = (cond3_val == 2)
    
    # Condition 4: Uniform cross-intersection
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    cond4 = (c11 == c12 == c21 == c22)
    
    # Condition 5: |unique_1| = |unique_2| = 2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    cond5 = (len(unique_1) == len(unique_2) == 2)
    
    # Condition 6: Uniform unique degrees
    degs_unique_1 = sorted([G.degree(x) for x in unique_1]) if unique_1 else []
    degs_unique_2 = sorted([G.degree(x) for x in unique_2]) if unique_2 else []
    cond6 = (len(set(degs_unique_1 + degs_unique_2)) == 1) if (unique_1 or unique_2) else True
    
    all_mechanism_a = cond1 and cond2 and cond3 and cond4 and cond5 and cond6
    
    shared_distribution[cond3_val].append(idx)
    if all_mechanism_a:
        mechanism_a_satisfied.append(idx)
    
    print(f"Switch {idx}: {g6_1}")
    print(f"  Cond 1 (deg equal):     ✓")
    print(f"  Cond 2 (parallel):      {'✓' if cond2 else '✗'} (v1-v2:{has_v1v2}, w1-w2:{has_w1w2})")
    print(f"  Cond 3 (|shared|=2):    {'✓' if cond3 else '✗'} (|shared|={cond3_val})")
    print(f"  Cond 4 (uniform cross): {'✓' if cond4 else '✗'} ({c11},{c12},{c21},{c22})")
    print(f"  Cond 5 (|unique|=2):    {'✓' if cond5 else '✗'} ({len(unique_1)},{len(unique_2)})")
    print(f"  Cond 6 (uniform deg):   {'✓' if cond6 else '✗'} ({degs_unique_1},{degs_unique_2})")
    print(f"  => {'MECHANISM A' if all_mechanism_a else 'other mechanism'}")
    print()

print("=" * 80)
print("SUMMARY: CONDITION 3 RELAXATION")
print("=" * 80)
print()
print("Distribution of |shared| among 2-edge switches:")
for val in sorted(shared_distribution.keys()):
    indices = shared_distribution[val]
    print(f"  |shared| = {val}: {len(indices)} switches (indices: {indices})")

print()
print(f"Mechanism A (all 6 conditions): {len(mechanism_a_satisfied)}/{len(two_edge_switches)}")
print()

# Key finding
print("=" * 80)
print("KEY FINDING")
print("=" * 80)
print()
if len(shared_distribution) > 1:
    non_2_count = sum(len(v) for k, v in shared_distribution.items() if k != 2)
    print(f"There are {non_2_count} NBL-cospectral 2-edge switches with |shared| ≠ 2.")
    print("Therefore, CONDITION 3 (|shared| = 2) IS NOT NECESSARY for NBL-cospectrality.")
    print()
    print("Switches with |shared| ≠ 2 that are still NBL-cospectral:")
    for val in sorted(shared_distribution.keys()):
        if val != 2:
            for idx in shared_distribution[val]:
                g6 = two_edge_switches[idx][0]
                print(f"  Switch {idx}: {g6} (|shared|={val})")

# Analyze non-switches
print()
print("=" * 80)
print("ANALYSIS OF NON-SWITCH PAIRS")
print("=" * 80)
print()

edge_diff_dist = defaultdict(int)
for _, _, _, _, edge_diff in non_switches:
    edge_diff_dist[edge_diff] += 1

print("Edge difference distribution:")
for diff in sorted(edge_diff_dist.keys()):
    print(f"  {diff} edges differ: {edge_diff_dist[diff]} pairs")

conn.close()
