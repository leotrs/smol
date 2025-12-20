#!/usr/bin/env python3
"""Check if uniform cross-pattern holds for ALL cospectral switches."""

import networkx as nx
import psycopg2
from itertools import permutations

conn = psycopg2.connect('dbname=smol')
cur = conn.cursor()

# Get ALL NBL cospectral pairs (no min_degree filter)
cur.execute('''
    SELECT g1.graph6, g2.graph6
    FROM cospectral_mates cm
    JOIN graphs g1 ON cm.graph1_id = g1.id
    JOIN graphs g2 ON cm.graph2_id = g2.id
    WHERE cm.matrix_type = 'nbl'
''')
pairs = cur.fetchall()

# Find all 2-edge switches
switches = []
for g6_1, g6_2 in pairs:
    G1 = nx.from_graph6_bytes(g6_1.encode())
    G2 = nx.from_graph6_bytes(g6_2.encode())
    E1 = set(frozenset(e) for e in G1.edges())
    E2 = set(frozenset(e) for e in G2.edges())
    only_in_G1 = E1 - E2
    if len(only_in_G1) != 2:
        continue
    verts = set()
    for e in only_in_G1 | (E2 - E1):
        verts.update(e)
    if len(verts) != 4:
        continue
    for perm in permutations(verts):
        v1, v2, w1, w2 = perm
        if only_in_G1 == {frozenset([v1, w1]), frozenset([v2, w2])}:
            if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                switches.append((g6_1, G1, v1, v2, w1, w2))
                break

print(f'Total cospectral 2-edge switches: {len(switches)}')
print()

uniform_count = 0
non_uniform = []

for g6, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    ext = {v: set(x for x in G.neighbors(v) if x not in S) for v in [v1, v2, w1, w2]}

    c11 = len(ext[v1] & ext[w1])
    c12 = len(ext[v1] & ext[w2])
    c21 = len(ext[v2] & ext[w1])
    c22 = len(ext[v2] & ext[w2])

    is_uniform = (c11 == c12 == c21 == c22)

    if is_uniform:
        uniform_count += 1
    else:
        non_uniform.append((g6, (c11, c12, c21, c22)))

print(f'Uniform cross-pattern: {uniform_count}/{len(switches)}')
print(f'Non-uniform: {len(non_uniform)}/{len(switches)}')

if non_uniform:
    print()
    print('NON-UNIFORM EXAMPLES:')
    for g6, cross in non_uniform[:10]:
        print(f'  {g6}: {cross}')

# Also check: is "column-equal" (not necessarily uniform) always true?
col_equal_count = 0
for g6, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    ext = {v: set(x for x in G.neighbors(v) if x not in S) for v in [v1, v2, w1, w2]}
    c11 = len(ext[v1] & ext[w1])
    c12 = len(ext[v1] & ext[w2])
    c21 = len(ext[v2] & ext[w1])
    c22 = len(ext[v2] & ext[w2])
    if c11 == c21 and c12 == c22:
        col_equal_count += 1

print()
print(f'Column-equal (c11==c21, c12==c22): {col_equal_count}/{len(switches)}')

conn.close()
