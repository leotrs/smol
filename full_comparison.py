"""
Get ALL counterexamples at n=8 and compare properties properly.
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def ws(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def tri(G, u, v):
    return len(set(G.neighbors(u)) & set(G.neighbors(v)))

def get_properties(G, v1, w1, v2, w2):
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    return {
        # Intersection sizes
        'v1w1': len(ext[v1] & ext[w1]),
        'v2w2': len(ext[v2] & ext[w2]),
        'v1w2': len(ext[v1] & ext[w2]),
        'v2w1': len(ext[v2] & ext[w1]),
        'v1v2': len(ext[v1] & ext[v2]),
        'w1w2': len(ext[w1] & ext[w2]),
        
        # Weighted sums
        'ws_v1w1': round(ws(G, ext[v1] & ext[w1]), 6),
        'ws_v2w2': round(ws(G, ext[v2] & ext[w2]), 6),
        'ws_v1w2': round(ws(G, ext[v1] & ext[w2]), 6),
        'ws_v2w1': round(ws(G, ext[v2] & ext[w1]), 6),
        'ws_v1v2': round(ws(G, ext[v1] & ext[v2]), 6),
        'ws_w1w2': round(ws(G, ext[w1] & ext[w2]), 6),
        
        # Triangles
        'tri_v1w1': tri(G, v1, w1),
        'tri_v2w2': tri(G, v2, w2),
        'tri_v1w2': tri(G, v1, w2),
        'tri_v2w1': tri(G, v2, w1),
        
        # Internal edges
        'e_v1v2': G.has_edge(v1, v2),
        'e_w1w2': G.has_edge(w1, w2),
        
        # Degree sequences of intersection vertices
        'int_degs_v1w1': tuple(sorted([G.degree(x) for x in ext[v1] & ext[w1]])),
        'int_degs_v2w2': tuple(sorted([G.degree(x) for x in ext[v2] & ext[w2]])),
        'int_degs_v1w2': tuple(sorted([G.degree(x) for x in ext[v1] & ext[w2]])),
        'int_degs_v2w1': tuple(sorted([G.degree(x) for x in ext[v2] & ext[w1]])),
    }

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

# Load 11 cospectral
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
        props = get_properties(G1, *switch)
        cospec.append((g1, switch, props))

# Get ALL n=8 counterexamples
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
                
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)
                
                if not spectra_equal(nbl_matrix(G), nbl_matrix(Gp)):
                    props = get_properties(G, v1, w1, v2, w2)
                    counter.append((g6, (v1, w1, v2, w2), props))
                    break

print(f"Cospectral: {len(cospec)}, Counterexamples: {len(counter)}")
print()

# Define conditions
conditions = [
    ('tri_eq', lambda p: p['tri_v1w1'] == p['tri_v2w2']),
    ('tri_new_eq', lambda p: p['tri_v1w2'] == p['tri_v2w1']),
    ('ws_all_eq', lambda p: p['ws_v1w1'] == p['ws_v2w2'] == p['ws_v1w2'] == p['ws_v2w1']),
    ('ws_diag', lambda p: p['ws_v1w1'] == p['ws_v2w2'] and p['ws_v1w2'] == p['ws_v2w1']),
    ('ws_row', lambda p: p['ws_v1w1'] == p['ws_v1w2'] and p['ws_v2w1'] == p['ws_v2w2']),
    ('ws_col', lambda p: p['ws_v1w1'] == p['ws_v2w1'] and p['ws_v1w2'] == p['ws_v2w2']),
    ('int_degs_diag', lambda p: p['int_degs_v1w1'] == p['int_degs_v2w2'] and p['int_degs_v1w2'] == p['int_degs_v2w1']),
    ('v1v2_nonempty', lambda p: p['v1v2'] > 0),
    ('w1w2_nonempty', lambda p: p['w1w2'] > 0),
    ('v1w1_nonempty', lambda p: p['v1w1'] > 0),
    ('v1v2_AND_w1w2', lambda p: p['v1v2'] > 0 and p['w1w2'] > 0),
    ('e_v1v2', lambda p: p['e_v1v2']),
    ('e_w1w2', lambda p: p['e_w1w2']),
    ('e_both', lambda p: p['e_v1v2'] and p['e_w1w2']),
]

print("CONDITION ANALYSIS:")
print("="*70)
for name, func in conditions:
    c_pass = sum(1 for _, _, p in cospec if func(p))
    x_pass = sum(1 for _, _, p in counter if func(p))
    
    if c_pass == len(cospec) and x_pass == 0:
        marker = " *** PERFECT ***"
    elif c_pass == len(cospec):
        marker = f" (filters {len(counter)-x_pass}/{len(counter)})"
    else:
        marker = ""
    
    print(f"{name:20s}: cospec={c_pass}/{len(cospec)}, counter={x_pass}/{len(counter)}{marker}")

# Try combinations
print("\n" + "="*70)
print("COMBINATIONS:")
print("="*70)

combos = [
    ('tri_eq + ws_all_eq', lambda p: p['tri_v1w1'] == p['tri_v2w2'] and 
                                     p['ws_v1w1'] == p['ws_v2w2'] == p['ws_v1w2'] == p['ws_v2w1']),
    ('tri_eq + ws_diag', lambda p: p['tri_v1w1'] == p['tri_v2w2'] and 
                                   p['ws_v1w1'] == p['ws_v2w2'] and p['ws_v1w2'] == p['ws_v2w1']),
    ('tri_eq + ws_row', lambda p: p['tri_v1w1'] == p['tri_v2w2'] and 
                                  p['ws_v1w1'] == p['ws_v1w2'] and p['ws_v2w1'] == p['ws_v2w2']),
    ('tri_eq + int_degs_diag', lambda p: p['tri_v1w1'] == p['tri_v2w2'] and 
                                         p['int_degs_v1w1'] == p['int_degs_v2w2'] and 
                                         p['int_degs_v1w2'] == p['int_degs_v2w1']),
    ('ws_row + v1w1_nonempty', lambda p: p['ws_v1w1'] == p['ws_v1w2'] and 
                                         p['ws_v2w1'] == p['ws_v2w2'] and p['v1w1'] > 0),
]

for name, func in combos:
    c_pass = sum(1 for _, _, p in cospec if func(p))
    x_pass = sum(1 for _, _, p in counter if func(p))
    
    if c_pass == len(cospec) and x_pass == 0:
        marker = " *** PERFECT ***"
    elif c_pass == len(cospec):
        marker = f" (filters {len(counter)-x_pass}/{len(counter)})"
    else:
        marker = ""
    
    print(f"{name:30s}: cospec={c_pass}/{len(cospec)}, counter={x_pass}/{len(counter)}{marker}")
