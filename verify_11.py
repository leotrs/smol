"""
Verify 11 cospectral switches pass all my conditions.
If they all pass but still have counterexamples at n=8, something deeper is missing.
"""

import networkx as nx
import numpy as np

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

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

def ws(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def tri(G, u, v):
    return len(set(G.neighbors(u)) & set(G.neighbors(v)))

def check_conditions(G, v1, w1, v2, w2, tol=1e-9):
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    results = {}
    
    # C1
    results['C1_v'] = G.degree(v1) == G.degree(v2)
    results['C1_w'] = G.degree(w1) == G.degree(w2)
    
    # C2
    results['C2_1'] = len(ext[v1] & ext[w1]) == len(ext[v2] & ext[w1])
    results['C2_2'] = len(ext[v1] & ext[w2]) == len(ext[v2] & ext[w2])
    
    # Triangles
    results['tri'] = tri(G, v1, w1) == tri(G, v2, w2)
    
    # Row symmetry
    ws_v1w1 = ws(G, ext[v1] & ext[w1])
    ws_v1w2 = ws(G, ext[v1] & ext[w2])
    ws_v2w1 = ws(G, ext[v2] & ext[w1])
    ws_v2w2 = ws(G, ext[v2] & ext[w2])
    
    results['row_v1'] = np.isclose(ws_v1w1, ws_v1w2, atol=tol)
    results['row_v2'] = np.isclose(ws_v2w1, ws_v2w2, atol=tol)
    
    # Diagonal symmetry
    results['diag_1'] = np.isclose(ws_v1w1, ws_v2w2, atol=tol)
    results['diag_2'] = np.isclose(ws_v1w2, ws_v2w1, atol=tol)
    
    # Non-empty intersection
    results['nonempty'] = len(ext[v1] & ext[w1]) > 0 or len(ext[v2] & ext[w2]) > 0
    
    # v1v2, w1w2 overlap
    results['v1v2'] = len(ext[v1] & ext[v2]) > 0
    results['w1w2'] = len(ext[w1] & ext[w2]) > 0
    
    return results

pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

print('Conditions satisfied by 11 cospectral switches:')
print()

for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if not switch:
        continue
    
    v1, w1, v2, w2 = switch
    results = check_conditions(G1, v1, w1, v2, w2)
    
    all_pass = all([results['C1_v'], results['C1_w'], results['C2_1'], results['C2_2'], results['tri']])
    
    fails = [k for k, v in results.items() if not v]
    
    print(f'{g1[:12]}... sw=({v1},{w1},{v2},{w2})')
    if fails:
        print(f'  FAILS: {fails}')
    else:
        print('  All basic conditions pass')
    
    # Show ws values
    S = {v1, v2, w1, w2}
    ext = {x: set(G1.neighbors(x)) - S for x in S}
    ws_v1w1 = ws(G1, ext[v1] & ext[w1])
    ws_v1w2 = ws(G1, ext[v1] & ext[w2])
    ws_v2w1 = ws(G1, ext[v2] & ext[w1])
    ws_v2w2 = ws(G1, ext[v2] & ext[w2])
    print(f'  ws: v1w1={ws_v1w1:.3f}, v2w2={ws_v2w2:.3f}, v1w2={ws_v1w2:.3f}, v2w1={ws_v2w1:.3f}')
    print()
