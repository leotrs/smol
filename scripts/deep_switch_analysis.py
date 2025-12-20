#!/usr/bin/env python3
"""Deep analysis of the 11 min_degree>=2 switches to find what explains them."""

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

print(f'Analyzing {len(switches)} switches deeply...')
print()

# Collect properties to find common patterns
all_props = []

for g6, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}

    # External neighborhoods
    ext = {v: set(x for x in G.neighbors(v) if x not in S) for v in S}

    # Internal structure (edges within S beyond the switch edges)
    has_v1_v2 = G.has_edge(v1, v2)
    has_w1_w2 = G.has_edge(w1, w2)

    # Degrees
    d_v = G.degree(v1)
    d_w = G.degree(w1)

    # Cross intersections
    c11 = len(ext[v1] & ext[w1])
    c12 = len(ext[v1] & ext[w2])
    c21 = len(ext[v2] & ext[w1])
    c22 = len(ext[v2] & ext[w2])

    # Union/intersection of external neighborhoods
    ext_v_union = ext[v1] | ext[v2]
    ext_w_union = ext[w1] | ext[w2]
    ext_v_inter = ext[v1] & ext[v2]
    ext_w_inter = ext[w1] & ext[w2]

    # Symmetric differences
    sym_v = ext[v1] ^ ext[v2]
    sym_w = ext[w1] ^ ext[w2]

    # Key conditions to test
    union_equal = ext_v_union == ext_w_union
    sym_equal = sym_v == sym_w
    inter_equal = ext_v_inter == ext_w_inter

    # Size relationships
    union_size_equal = len(ext_v_union) == len(ext_w_union)
    inter_size_equal = len(ext_v_inter) == len(ext_w_inter)
    sym_size_equal = len(sym_v) == len(sym_w)

    props = {
        'g6': g6,
        'd_v': d_v,
        'd_w': d_w,
        'has_v1_v2': has_v1_v2,
        'has_w1_w2': has_w1_w2,
        'cross': (c11, c12, c21, c22),
        'union_equal': union_equal,
        'sym_equal': sym_equal,
        'inter_equal': inter_equal,
        'union_size_equal': union_size_equal,
        'inter_size_equal': inter_size_equal,
        'sym_size_equal': sym_size_equal,
        'ext_v_union': ext_v_union,
        'ext_w_union': ext_w_union,
        'sym_v': sym_v,
        'sym_w': sym_w,
    }
    all_props.append(props)

    print(f'{g6}:')
    print(f'  cross: {props["cross"]}')
    print(f'  union_equal: {union_equal}, sym_equal: {sym_equal}, inter_equal: {inter_equal}')
    print(f'  ext_v_union={ext_v_union}')
    print(f'  ext_w_union={ext_w_union}')
    print(f'  sym_v={sym_v}, sym_w={sym_w}')
    print()

print('=' * 70)
print('COMMON PROPERTIES (must be True for ALL 11):')
print('=' * 70)

for prop in ['union_equal', 'sym_equal', 'inter_equal', 'union_size_equal', 'inter_size_equal', 'sym_size_equal']:
    all_true = all(p[prop] for p in all_props)
    count = sum(1 for p in all_props if p[prop])
    print(f'{prop}: {count}/11 {"*** ALL TRUE ***" if all_true else ""}')

# Check if cross pattern is always uniform
cross_uniform = all(p['cross'][0] == p['cross'][1] == p['cross'][2] == p['cross'][3] for p in all_props)
print(f'cross_uniform: {11 if cross_uniform else "varies"}/11 {"*** ALL TRUE ***" if cross_uniform else ""}')

conn.close()
