#!/usr/bin/env python3
"""Analyze the 78 NBL-cospectral pairs with n=10, min_degree>=2."""

import networkx as nx
from itertools import permutations

pairs = []
with open('/tmp/pairs78.txt') as f:
    for line in f:
        if line.strip():
            g1, g2 = line.strip().split('\t')
            pairs.append((g1, g2))

print(f'Total pairs: {len(pairs)}')

switches = []
non_switches = []

for g6_1, g6_2 in pairs:
    G1 = nx.from_graph6_bytes(g6_1.encode())
    G2 = nx.from_graph6_bytes(g6_2.encode())
    E1 = set(frozenset(e) for e in G1.edges())
    E2 = set(frozenset(e) for e in G2.edges())
    diff = len(E1 ^ E2)

    if diff == 4:
        only_in_G1 = E1 - E2
        verts = set()
        for e in only_in_G1 | (E2 - E1):
            verts.update(e)
        if len(verts) == 4:
            for perm in permutations(verts):
                v1, v2, w1, w2 = perm
                if only_in_G1 == {frozenset([v1, w1]), frozenset([v2, w2])}:
                    if G1.degree(v1) == G1.degree(v2) and G1.degree(w1) == G1.degree(w2):
                        switches.append((g6_1, G1, v1, v2, w1, w2))
                        break
            else:
                non_switches.append((g6_1, g6_2, diff))
        else:
            non_switches.append((g6_1, g6_2, diff))
    else:
        non_switches.append((g6_1, g6_2, diff))

print(f'2-edge switches: {len(switches)}')
print(f'Non-switches: {len(non_switches)}')
print()

# Analyze the switches
print('='*60)
print('ANALYZING THE 2-EDGE SWITCHES')
print('='*60)

for g6, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    ext = {v: set(x for x in G.neighbors(v) if x not in S) for v in S}

    c11 = len(ext[v1] & ext[w1])
    c12 = len(ext[v1] & ext[w2])
    c21 = len(ext[v2] & ext[w1])
    c22 = len(ext[v2] & ext[w2])

    cond_b = ext[v1] == ext[v2] or ext[w1] == ext[w2]
    uniform = c11 == c12 == c21 == c22

    print(f'{g6}: cross=({c11},{c12},{c21},{c22}) uniform={uniform} cond_b={cond_b}')

print()
print('='*60)
print('SUMMARY')
print('='*60)

cond_b_count = 0
uniform_count = 0
for g6, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    ext = {v: set(x for x in G.neighbors(v) if x not in S) for v in S}
    c11 = len(ext[v1] & ext[w1])
    c12 = len(ext[v1] & ext[w2])
    c21 = len(ext[v2] & ext[w1])
    c22 = len(ext[v2] & ext[w2])

    if ext[v1] == ext[v2] or ext[w1] == ext[w2]:
        cond_b_count += 1
    if c11 == c12 == c21 == c22:
        uniform_count += 1

print(f'Condition B (ext equality): {cond_b_count}/{len(switches)}')
print(f'Uniform cross-pattern: {uniform_count}/{len(switches)}')
