#!/usr/bin/env python3
"""
Check all Mechanism A conditions for NBL-cospectral 2-edge switches.

Mechanism A conditions:
1. deg(v1) = deg(v2) and deg(w1) = deg(w2)
2. v1-v2 ∈ E and w1-w2 ∈ E (both parallel edges)
3. |shared| = 2 where shared = ext(w1) ∩ ext(w2)
4. |ext(vi) ∩ ext(wj)| = c for all i,j (uniform cross-intersection)
5. |unique_1| = |unique_2| = 2
6. deg(x) = d_u for all x in unique_1 ∪ unique_2 (uniform unique degrees)
"""

import networkx as nx
import psycopg2
from itertools import permutations
from collections import defaultdict

conn = psycopg2.connect('dbname=smol')
cur = conn.cursor()

# Get NBL cospectral pairs with min_degree >= 2
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

print(f"Found {len(switches)} NBL-cospectral 2-edge switches (min_degree >= 2)")
print("=" * 80)
print()

# Analyze each switch
results = []
shared_values = defaultdict(int)
unique_values = defaultdict(int)

for idx, (g6_1, g6_2, G, v1, v2, w1, w2) in enumerate(switches):
    S = {v1, v2, w1, w2}
    
    # External neighborhoods
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)
    
    # Condition 1: Degree equality (already satisfied by construction)
    d_v = G.degree(v1)
    d_w = G.degree(w1)
    cond1 = True
    
    # Condition 2: Both parallel edges
    has_v1v2 = G.has_edge(v1, v2)
    has_w1w2 = G.has_edge(w1, w2)
    cond2 = has_v1v2 and has_w1w2
    
    # Condition 3: |shared| = 2
    shared = ext_w1 & ext_w2
    cond3_val = len(shared)
    cond3 = (cond3_val == 2)
    shared_values[cond3_val] += 1
    
    # Condition 4: Uniform cross-intersection
    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)
    cond4 = (c11 == c12 == c21 == c22)
    cross_val = c11 if cond4 else None
    
    # Condition 5: |unique_1| = |unique_2| = 2
    unique_1 = ext_w1 - ext_w2
    unique_2 = ext_w2 - ext_w1
    cond5_vals = (len(unique_1), len(unique_2))
    cond5 = (len(unique_1) == len(unique_2) == 2)
    unique_values[cond5_vals] += 1
    
    # Condition 6: Uniform unique degrees
    degs_unique_1 = sorted([G.degree(x) for x in unique_1]) if unique_1 else []
    degs_unique_2 = sorted([G.degree(x) for x in unique_2]) if unique_2 else []
    cond6 = (len(set(degs_unique_1 + degs_unique_2)) == 1) if (unique_1 or unique_2) else True
    unique_deg = degs_unique_1[0] if (cond6 and degs_unique_1) else None
    
    all_conds = cond1 and cond2 and cond3 and cond4 and cond5 and cond6
    
    results.append({
        'idx': idx,
        'g6': g6_1,
        'd_v': d_v,
        'd_w': d_w,
        'cond1': cond1,
        'cond2': cond2,
        'has_v1v2': has_v1v2,
        'has_w1w2': has_w1w2,
        'cond3': cond3,
        'shared_size': cond3_val,
        'shared': shared,
        'cond4': cond4,
        'cross': (c11, c12, c21, c22),
        'cross_val': cross_val,
        'cond5': cond5,
        'unique_sizes': cond5_vals,
        'unique_1': unique_1,
        'unique_2': unique_2,
        'cond6': cond6,
        'degs_unique': (degs_unique_1, degs_unique_2),
        'unique_deg': unique_deg,
        'all_mechanism_a': all_conds,
    })

# Print detailed results
for r in results:
    status = "✓ MECHANISM A" if r['all_mechanism_a'] else "✗"
    print(f"Switch {r['idx']}: {r['g6']}")
    print(f"  Degrees: d_v={r['d_v']}, d_w={r['d_w']}")
    print(f"  Cond 1 (deg equal):      {r['cond1']}")
    print(f"  Cond 2 (parallel edges): {r['cond2']} (v1-v2: {r['has_v1v2']}, w1-w2: {r['has_w1w2']})")
    print(f"  Cond 3 (|shared|=2):     {r['cond3']} (|shared|={r['shared_size']}, shared={r['shared']})")
    print(f"  Cond 4 (uniform cross):  {r['cond4']} (cross={r['cross']})")
    print(f"  Cond 5 (|unique|=2):     {r['cond5']} (sizes={r['unique_sizes']})")
    print(f"  Cond 6 (uniform deg):    {r['cond6']} (degs={r['degs_unique']})")
    print(f"  => {status}")
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

print("Distribution of |shared|:")
for val, count in sorted(shared_values.items()):
    print(f"  |shared| = {val}: {count} switches")

print()
print("Distribution of (|unique_1|, |unique_2|):")
for val, count in sorted(unique_values.items()):
    print(f"  {val}: {count} switches")

print()
cond_counts = {
    'cond1': sum(1 for r in results if r['cond1']),
    'cond2': sum(1 for r in results if r['cond2']),
    'cond3': sum(1 for r in results if r['cond3']),
    'cond4': sum(1 for r in results if r['cond4']),
    'cond5': sum(1 for r in results if r['cond5']),
    'cond6': sum(1 for r in results if r['cond6']),
    'all': sum(1 for r in results if r['all_mechanism_a']),
}

print("Condition satisfaction:")
print(f"  Cond 1 (degree equality):      {cond_counts['cond1']}/{len(results)}")
print(f"  Cond 2 (both parallel edges):  {cond_counts['cond2']}/{len(results)}")
print(f"  Cond 3 (|shared| = 2):         {cond_counts['cond3']}/{len(results)}")
print(f"  Cond 4 (uniform cross):        {cond_counts['cond4']}/{len(results)}")
print(f"  Cond 5 (|unique| = 2 each):    {cond_counts['cond5']}/{len(results)}")
print(f"  Cond 6 (uniform unique deg):   {cond_counts['cond6']}/{len(results)}")
print(f"  ALL (Mechanism A):             {cond_counts['all']}/{len(results)}")

# Find switches that violate only condition 3
print()
print("=" * 80)
print("SWITCHES VIOLATING ONLY CONDITION 3 (|shared| ≠ 2)")
print("=" * 80)
for r in results:
    if r['cond1'] and r['cond2'] and not r['cond3'] and r['cond4'] and r['cond5'] and r['cond6']:
        print(f"  {r['g6']}: |shared|={r['shared_size']}")

# Find switches satisfying all except condition 2
print()
print("=" * 80)
print("SWITCHES VIOLATING ONLY CONDITION 2 (missing parallel edge)")
print("=" * 80)
for r in results:
    if r['cond1'] and not r['cond2'] and r['cond4']:
        print(f"  {r['g6']}: v1-v2={r['has_v1v2']}, w1-w2={r['has_w1w2']}, |shared|={r['shared_size']}")

conn.close()
