#!/usr/bin/env python3
"""Find a universal property for ALL cospectral switches."""

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

# Look for properties based on degrees and internal structure
tests = []

for g6, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    ext = {v: set(x for x in G.neighbors(v) if x not in S) for v in S}

    c11 = len(ext[v1] & ext[w1])
    c12 = len(ext[v1] & ext[w2])
    c21 = len(ext[v2] & ext[w1])
    c22 = len(ext[v2] & ext[w2])

    # Degrees
    d_v = G.degree(v1)  # = G.degree(v2)
    d_w = G.degree(w1)  # = G.degree(w2)

    # Internal edges (within S)
    has_v1v2 = G.has_edge(v1, v2)
    has_w1w2 = G.has_edge(w1, w2)

    # Sizes of external neighborhoods
    ext_sizes = (len(ext[v1]), len(ext[v2]), len(ext[w1]), len(ext[w2]))

    # The key insight: in a switch, v1-w1 and v2-w2 become v1-w2 and v2-w1
    # For NBL, what matters is the non-backtracking transitions

    # External neighborhood sizes (outside S)
    # ext_v = d_v - (1 if has_v1v2 else 0) - 1  (subtract the w-neighbor)
    # Actually simpler: len(ext[v1]) = d_v - #{neighbors of v1 in S}

    tests.append({
        'g6': g6,
        'cross': (c11, c12, c21, c22),
        'd_v': d_v,
        'd_w': d_w,
        'has_v1v2': has_v1v2,
        'has_w1w2': has_w1w2,
        'ext_sizes': ext_sizes,
        'sum_cross': c11 + c12 + c21 + c22,
        'prod_diag': c11 * c22,
        'prod_antidiag': c12 * c21,
    })

# Check: is prod_diag == prod_antidiag always?
prod_equal = sum(1 for t in tests if t['prod_diag'] == t['prod_antidiag'])
print(f'c11*c22 == c12*c21: {prod_equal}/{len(tests)}')

# Look at failures
failures = [t for t in tests if t['prod_diag'] != t['prod_antidiag']]
if failures:
    print('\nFailures for product condition:')
    for t in failures[:5]:
        print(f"  {t['g6']}: cross={t['cross']}, prod={t['prod_diag']} vs {t['prod_antidiag']}")

# Try: is there a relationship with degrees?
# For each switch, the condition might depend on d_v and d_w
print('\n\nLooking for degree-dependent patterns...')

# Check if column-equal OR row-equal is universal
col_or_row = sum(1 for t in tests if
    (t['cross'][0] == t['cross'][2] and t['cross'][1] == t['cross'][3]) or
    (t['cross'][0] == t['cross'][1] and t['cross'][2] == t['cross'][3]))
print(f'col-equal OR row-equal: {col_or_row}/{len(tests)}')

# Check the failures
col_row_failures = [t for t in tests if not (
    (t['cross'][0] == t['cross'][2] and t['cross'][1] == t['cross'][3]) or
    (t['cross'][0] == t['cross'][1] and t['cross'][2] == t['cross'][3]))]
if col_row_failures:
    print('\nFailures for col-OR-row:')
    for t in col_row_failures[:10]:
        print(f"  {t['g6']}: cross={t['cross']}, d_v={t['d_v']}, d_w={t['d_w']}")

# Maybe the condition is weaker: sum_diag == sum_antidiag
sum_equal = sum(1 for t in tests if t['cross'][0] + t['cross'][3] == t['cross'][1] + t['cross'][2])
print(f'\nc11+c22 == c12+c21: {sum_equal}/{len(tests)}')

# Check Condition B
print('\n' + '='*60)
print('CONDITION B (external neighborhood equality):')
cond_b = 0
for g6, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    ext = {v: set(x for x in G.neighbors(v) if x not in S) for v in S}
    if ext[v1] == ext[v2] or ext[w1] == ext[w2]:
        cond_b += 1

print(f'Condition B: {cond_b}/{len(switches)}')
print(f'NOT explained by B: {len(switches) - cond_b}')

# The switches NOT explained by B - what do THEY have in common?
print('\n' + '='*60)
print('Switches NOT explained by Condition B:')
not_b = []
for g6, G, v1, v2, w1, w2 in switches:
    S = {v1, v2, w1, w2}
    ext = {v: set(x for x in G.neighbors(v) if x not in S) for v in S}
    if ext[v1] != ext[v2] and ext[w1] != ext[w2]:
        c11 = len(ext[v1] & ext[w1])
        c12 = len(ext[v1] & ext[w2])
        c21 = len(ext[v2] & ext[w1])
        c22 = len(ext[v2] & ext[w2])
        not_b.append({'g6': g6, 'cross': (c11, c12, c21, c22)})

print(f'Total not-B: {len(not_b)}')

# Check properties on NOT-B switches
uniform_in_notb = sum(1 for t in not_b if t['cross'][0] == t['cross'][1] == t['cross'][2] == t['cross'][3])
col_eq_in_notb = sum(1 for t in not_b if t['cross'][0] == t['cross'][2] and t['cross'][1] == t['cross'][3])
row_eq_in_notb = sum(1 for t in not_b if t['cross'][0] == t['cross'][1] and t['cross'][2] == t['cross'][3])
sum_eq_in_notb = sum(1 for t in not_b if t['cross'][0] + t['cross'][3] == t['cross'][1] + t['cross'][2])

print(f'  uniform_cross: {uniform_in_notb}/{len(not_b)}')
print(f'  col_equal: {col_eq_in_notb}/{len(not_b)}')
print(f'  row_equal: {row_eq_in_notb}/{len(not_b)}')
print(f'  sum_diag_eq_antidiag: {sum_eq_in_notb}/{len(not_b)}')

conn.close()
