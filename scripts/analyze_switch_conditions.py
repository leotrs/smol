#!/usr/bin/env python3
"""Analyze which conditions explain the min_degree>=2 switches."""

import networkx as nx
import psycopg2
from itertools import permutations

conn = psycopg2.connect('dbname=smol')
cur = conn.cursor()
cur.execute('''
    SELECT g1.graph6, g2.graph6, g1.n
    FROM cospectral_mates cm
    JOIN graphs g1 ON cm.graph1_id = g1.id
    JOIN graphs g2 ON cm.graph2_id = g2.id
    WHERE cm.matrix_type = 'nbl'
      AND g1.min_degree >= 2
      AND g2.min_degree >= 2
''')
pairs = cur.fetchall()

# Find ONLY switches that correspond to actual cospectral pairs in the database
switches = []
for g6_1, g6_2, n in pairs:
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
                switches.append((g6_1, g6_2, n, G1, v1, v2, w1, w2))
                break

print(f'THE {len(switches)} KNOWN COSPECTRAL SWITCHES (min_degree >= 2):')
print()

cond_b = 0
cond_c = 0
neither = 0

for g6_1, g6_2, n, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    ext_v1 = set(x for x in G.neighbors(v1) if x not in S)
    ext_v2 = set(x for x in G.neighbors(v2) if x not in S)
    ext_w1 = set(x for x in G.neighbors(w1) if x not in S)
    ext_w2 = set(x for x in G.neighbors(w2) if x not in S)

    B = (ext_v1 == ext_v2) or (ext_w1 == ext_w2)

    c11 = len(ext_v1 & ext_w1)
    c12 = len(ext_v1 & ext_w2)
    c21 = len(ext_v2 & ext_w1)
    c22 = len(ext_v2 & ext_w2)

    sym_v = len(ext_v1 ^ ext_v2)
    sym_w = len(ext_w1 ^ ext_w2)

    col_eq = (c11 == c21) and (c12 == c22)
    all_nz = c11 > 0 and c12 > 0 and c21 > 0 and c22 > 0
    C = col_eq and all_nz and (sym_v == 2) and (sym_w == 2) and not B

    if B:
        cond_b += 1
        status = 'B'
    elif C:
        cond_c += 1
        status = 'C'
    else:
        neither += 1
        status = 'NEITHER'

    print(f'{g6_1}: cross=({c11},{c12},{c21},{c22}), sym=({sym_v},{sym_w}) -> {status}')

print()
print('=' * 60)
print('SUMMARY')
print('=' * 60)
print(f'Condition B: {cond_b}/{len(switches)}')
print(f'Condition C: {cond_c}/{len(switches)}')
print(f'Neither B nor C: {neither}/{len(switches)}')

conn.close()
