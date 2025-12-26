"""
Analyze the 387 remaining counterexamples that pass ws_row + w1w2.
What distinguishes them from the 11 cospectral switches?
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess
from collections import Counter

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def ws(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def tri(G, u, v):
    return len(set(G.neighbors(u)) & set(G.neighbors(v)))

def get_full_properties(G, v1, w1, v2, w2):
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    p = {}
    
    # All intersection sizes
    for (a, b), name in [((v1,w1),'v1w1'), ((v2,w2),'v2w2'), ((v1,w2),'v1w2'), 
                         ((v2,w1),'v2w1'), ((v1,v2),'v1v2'), ((w1,w2),'w1w2')]:
        p[name] = len(ext[a] & ext[b])
    
    # All weighted sums
    for (a, b), name in [((v1,w1),'ws_v1w1'), ((v2,w2),'ws_v2w2'), ((v1,w2),'ws_v1w2'), 
                         ((v2,w1),'ws_v2w1'), ((v1,v2),'ws_v1v2'), ((w1,w2),'ws_w1w2')]:
        p[name] = round(ws(G, ext[a] & ext[b]), 6)
    
    # Triangles
    p['tri_v1w1'] = tri(G, v1, w1)
    p['tri_v2w2'] = tri(G, v2, w2)
    p['tri_v1w2'] = tri(G, v1, w2)
    p['tri_v2w1'] = tri(G, v2, w1)
    
    # Internal edges
    p['e_v1v2'] = G.has_edge(v1, v2)
    p['e_w1w2'] = G.has_edge(w1, w2)
    
    # Degree sequences of intersection vertices
    for (a, b), name in [((v1,w1),'int_degs_v1w1'), ((v2,w2),'int_degs_v2w2'), 
                         ((v1,w2),'int_degs_v1w2'), ((v2,w1),'int_degs_v2w1'),
                         ((v1,v2),'int_degs_v1v2'), ((w1,w2),'int_degs_w1w2')]:
        p[name] = tuple(sorted([G.degree(x) for x in ext[a] & ext[b]]))
    
    # External degree sequences
    for x, name in [(v1,'ext_degs_v1'), (w1,'ext_degs_w1'), (v2,'ext_degs_v2'), (w2,'ext_degs_w2')]:
        p[name] = tuple(sorted([G.degree(y) for y in ext[x]]))
    
    # Degrees of v, w
    p['deg_v1'] = G.degree(v1)
    p['deg_w1'] = G.degree(w1)
    
    return p

def nbl_matrix(G):
    edges = [(u,v) for u,v in G.edges()] + [(v,u) for u,v in G.edges()]
    idx = {e:i for i,e in enumerate(edges)}
    n = len(edges)
    T = np.zeros((n, n))
    for (u,v), i in idx.items():
        d = G.degree(v)
        if d <= 1: continue
        for w in G.neighbors(v):
            if w != u:
                T[i, idx[(v,w)]] = 1.0 / (d - 1)
    return T

def spectra_equal(T1, T2, max_k=30):
    P1, P2 = T1.copy(), T2.copy()
    for k in range(1, max_k + 1):
        if not np.isclose(np.trace(P1), np.trace(P2), atol=1e-9):
            return False
        P1, P2 = P1 @ T1, P2 @ T2
    return True

def find_switch(G1, G2):
    e1 = set(frozenset(e) for e in G1.edges())
    e2 = set(frozenset(e) for e in G2.edges())
    only_in_1 = e1 - e2
    only_in_2 = e2 - e1
    if len(only_in_1) != 2 or len(only_in_2) != 2:
        return None
    removed = [tuple(e) for e in only_in_1]
    added = [tuple(e) for e in only_in_2]
    for (a, b), (c, d) in [(removed[0], removed[1]), (removed[1], removed[0])]:
        for v1, w1 in [(a, b), (b, a)]:
            for v2, w2 in [(c, d), (d, c)]:
                expected = {frozenset({v1, w2}), frozenset({v2, w1})}
                actual = set(frozenset(e) for e in added)
                if expected == actual:
                    return (v1, w1, v2, w2)
    return None

# Load cospectral
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

cospec = []
for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if switch:
        props = get_full_properties(G1, *switch)
        cospec.append((g1, switch, props))

# Get counterexamples that pass ws_row + w1w2
result = subprocess.run(['geng', '-c', '-d2', '8'], capture_output=True, text=True)
graphs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

counter = []
for g6 in graphs:
    G = to_graph(g6)
    for e1, e2 in combinations(G.edges(), 2):
        for v1, w1 in [e1, e1[::-1]]:
            for v2, w2 in [e2, e2[::-1]]:
                if G.has_edge(v1, w2) or G.has_edge(v2, w1):
                    continue
                S = {v1, v2, w1, w2}
                if len(S) != 4:
                    continue
                if G.degree(v1) != G.degree(v2):
                    continue
                if G.degree(w1) != G.degree(w2):
                    continue
                ext = {x: set(G.neighbors(x)) - S for x in S}
                if len(ext[v1] & ext[w1]) != len(ext[v2] & ext[w1]):
                    continue
                if len(ext[v1] & ext[w2]) != len(ext[v2] & ext[w2]):
                    continue
                
                # ws_row
                ws_v1w1 = round(ws(G, ext[v1] & ext[w1]), 6)
                ws_v1w2 = round(ws(G, ext[v1] & ext[w2]), 6)
                ws_v2w1 = round(ws(G, ext[v2] & ext[w1]), 6)
                ws_v2w2 = round(ws(G, ext[v2] & ext[w2]), 6)
                if ws_v1w1 != ws_v1w2 or ws_v2w1 != ws_v2w2:
                    continue
                
                # w1w2 nonempty
                if len(ext[w1] & ext[w2]) == 0:
                    continue
                
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)
                
                if not spectra_equal(nbl_matrix(G), nbl_matrix(Gp)):
                    props = get_full_properties(G, v1, w1, v2, w2)
                    counter.append((g6, (v1, w1, v2, w2), props))
                    break

print(f"Remaining counterexamples after ws_row + w1w2: {len(counter)}")
print()

# Find discriminating properties
print("="*70)
print("PROPERTY VALUES COMPARISON")
print("="*70)

# Check specific properties
props_to_check = [
    'tri_v1w1', 'tri_v2w2', 'tri_v1w2', 'tri_v2w1',
    'v1v2', 'w1w2', 'v1w1',
    'ws_v1v2', 'ws_w1w2',
    'e_v1v2', 'e_w1w2',
]

for prop in props_to_check:
    cosp_vals = Counter(str(p[prop]) for _, _, p in cospec)
    ctr_vals = Counter(str(p[prop]) for _, _, p in counter)
    print(f"\n{prop}:")
    print(f"  Cospec: {dict(cosp_vals)}")
    print(f"  Counter: {dict(ctr_vals)}")

# Check derived conditions
print("\n" + "="*70)
print("DERIVED CONDITIONS")
print("="*70)

conditions = [
    ('tri_eq', lambda p: p['tri_v1w1'] == p['tri_v2w2']),
    ('tri_new_eq', lambda p: p['tri_v1w2'] == p['tri_v2w1']),
    ('tri_all_eq', lambda p: p['tri_v1w1'] == p['tri_v2w2'] == p['tri_v1w2'] == p['tri_v2w1']),
    ('ws_v1v2_eq_w1w2', lambda p: p['ws_v1v2'] == p['ws_w1w2']),
    ('v1v2_ge_1', lambda p: p['v1v2'] >= 1),
    ('v1v2_ge_2', lambda p: p['v1v2'] >= 2),
    ('int_degs_v1v2_eq_w1w2', lambda p: p['int_degs_v1v2'] == p['int_degs_w1w2']),
    ('e_v1v2', lambda p: p['e_v1v2']),
    ('e_w1w2', lambda p: p['e_w1w2']),
    ('e_both', lambda p: p['e_v1v2'] and p['e_w1w2']),
    ('ws_diag', lambda p: p['ws_v1w1'] == p['ws_v2w2'] and p['ws_v1w2'] == p['ws_v2w1']),
    ('int_degs_diag', lambda p: p['int_degs_v1w1'] == p['int_degs_v2w2'] and p['int_degs_v1w2'] == p['int_degs_v2w1']),
]

for name, func in conditions:
    c_pass = sum(1 for _, _, p in cospec if func(p))
    x_pass = sum(1 for _, _, p in counter if func(p))
    
    if c_pass == 11 and x_pass == 0:
        marker = " *** PERFECT ***"
    elif c_pass == 11:
        marker = f" (leaves {x_pass})"
    else:
        marker = ""
    
    print(f"{name:25s}: cospec={c_pass}/11, counter={x_pass}/{len(counter)}{marker}")
