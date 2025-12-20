#!/usr/bin/env python3
"""Find what property ALL cospectral switches share."""

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
''')
pairs = cur.fetchall()

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

print(f'Analyzing {len(switches)} cospectral switches...')
print()

# Test many properties
properties = {
    'uniform_cross': 0,
    'col_equal': 0,
    'row_equal': 0,
    'col_OR_row': 0,
    'sum_cross_equal': 0,  # c11+c22 == c12+c21
    'product_cross_equal': 0,  # c11*c22 == c12*c21
    'diag_equal': 0,  # c11 == c22 and c12 == c21
    'antidiag_equal': 0,  # c11 == c22 or c12 == c21
    'trace_equal_antitrace': 0,  # c11+c22 == c12+c21
    'all_same_parity': 0,  # all even or all odd
    'ext_v_size_eq_ext_w_size': 0,  # |ext(v1)|+|ext(v2)| == |ext(w1)|+|ext(w2)|
    'sym_v_size_eq_sym_w_size': 0,  # |sym_v| == |sym_w|
    'ext_v_union_eq_ext_w_union': 0,
    'sym_v_eq_sym_w': 0,
}

for g6, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    ext = {v: set(x for x in G.neighbors(v) if x not in S) for v in [v1, v2, w1, w2]}

    c11 = len(ext[v1] & ext[w1])
    c12 = len(ext[v1] & ext[w2])
    c21 = len(ext[v2] & ext[w1])
    c22 = len(ext[v2] & ext[w2])

    ext_v_union = ext[v1] | ext[v2]
    ext_w_union = ext[w1] | ext[w2]
    sym_v = ext[v1] ^ ext[v2]
    sym_w = ext[w1] ^ ext[w2]

    if c11 == c12 == c21 == c22:
        properties['uniform_cross'] += 1
    if c11 == c21 and c12 == c22:
        properties['col_equal'] += 1
    if c11 == c12 and c21 == c22:
        properties['row_equal'] += 1
    if (c11 == c21 and c12 == c22) or (c11 == c12 and c21 == c22):
        properties['col_OR_row'] += 1
    if c11 + c22 == c12 + c21:
        properties['sum_cross_equal'] += 1
    if c11 * c22 == c12 * c21:
        properties['product_cross_equal'] += 1
    if c11 == c22 and c12 == c21:
        properties['diag_equal'] += 1
    if c11 == c22 or c12 == c21:
        properties['antidiag_equal'] += 1
    if (c11 + c12 + c21 + c22) % 2 == 0 or all(x % 2 == c11 % 2 for x in [c11, c12, c21, c22]):
        properties['all_same_parity'] += 1
    if len(ext[v1]) + len(ext[v2]) == len(ext[w1]) + len(ext[w2]):
        properties['ext_v_size_eq_ext_w_size'] += 1
    if len(sym_v) == len(sym_w):
        properties['sym_v_size_eq_sym_w_size'] += 1
    if ext_v_union == ext_w_union:
        properties['ext_v_union_eq_ext_w_union'] += 1
    if sym_v == sym_w:
        properties['sym_v_eq_sym_w'] += 1

print('Property                              Count    All?')
print('-' * 55)
for prop, count in sorted(properties.items(), key=lambda x: -x[1]):
    is_all = '*** ALL ***' if count == len(switches) else ''
    print(f'{prop:<35} {count:>5}/{len(switches)}  {is_all}')

conn.close()
