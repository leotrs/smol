"""
Compare 11 cospectral switches vs 734 counterexamples.
Look for 1-3 principled distinguishing properties.
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

def spectra_equal(T1, T2, max_k=50):
    P1, P2 = T1.copy(), T2.copy()
    for k in range(1, max_k + 1):
        if not np.isclose(np.trace(P1), np.trace(P2), atol=1e-6):
            return False
        P1, P2 = P1 @ T1, P2 @ T2
    return True

def get_properties(G, v1, w1, v2, w2):
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    return {
        'v1w1': len(ext[v1] & ext[w1]),
        'v2w2': len(ext[v2] & ext[w2]),
        'v1w2': len(ext[v1] & ext[w2]),
        'v2w1': len(ext[v2] & ext[w1]),
        'v1v2': len(ext[v1] & ext[v2]),
        'w1w2': len(ext[w1] & ext[w2]),
        'e_v1v2': G.has_edge(v1, v2),
        'e_w1w2': G.has_edge(w1, w2),
    }

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

# Get 11 cospectral switches
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

# Get counterexamples (C1 + C2 + row_sym satisfied but not cospectral)
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
                ws_v1w1 = ws(G, ext[v1] & ext[w1])
                ws_v1w2 = ws(G, ext[v1] & ext[w2])
                ws_v2w1 = ws(G, ext[v2] & ext[w1])
                ws_v2w2 = ws(G, ext[v2] & ext[w2])
                if not np.isclose(ws_v1w1, ws_v1w2, atol=1e-6):
                    continue
                if not np.isclose(ws_v2w1, ws_v2w2, atol=1e-6):
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

# Property 1: v1∩w1 non-empty
print("1. v1∩w1 > 0:")
c_pass = sum(1 for _, _, p in cospec if p['v1w1'] > 0)
x_pass = sum(1 for _, _, p in counter if p['v1w1'] > 0)
print(f"   Cospec: {c_pass}/11, Counter: {x_pass}/{len(counter)}")

# Property 2: w1∩w2 non-empty  
print("2. w1∩w2 > 0:")
c_pass = sum(1 for _, _, p in cospec if p['w1w2'] > 0)
x_pass = sum(1 for _, _, p in counter if p['w1w2'] > 0)
print(f"   Cospec: {c_pass}/11, Counter: {x_pass}/{len(counter)}")

# Property 3: v1∩v2 non-empty
print("3. v1∩v2 > 0:")
c_pass = sum(1 for _, _, p in cospec if p['v1v2'] > 0)
x_pass = sum(1 for _, _, p in counter if p['v1v2'] > 0)
print(f"   Cospec: {c_pass}/11, Counter: {x_pass}/{len(counter)}")

# Combination: v1w1 > 0 AND w1w2 > 0
print("4. v1∩w1 > 0 AND w1∩w2 > 0:")
c_pass = sum(1 for _, _, p in cospec if p['v1w1'] > 0 and p['w1w2'] > 0)
x_pass = sum(1 for _, _, p in counter if p['v1w1'] > 0 and p['w1w2'] > 0)
print(f"   Cospec: {c_pass}/11, Counter: {x_pass}/{len(counter)}")

# Look at the distribution of (v1w1, w1w2) pairs
print()
print("Distribution of (v1∩w1, w1∩w2):")
print("Cospectral:")
for _, _, p in cospec:
    print(f"  ({p['v1w1']}, {p['w1w2']})")
print("Counterexamples (first 20):")
ctr_pairs = Counter((p['v1w1'], p['w1w2']) for _, _, p in counter)
for pair, cnt in ctr_pairs.most_common(20):
    print(f"  {pair}: {cnt}")
