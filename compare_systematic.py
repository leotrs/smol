"""
Systematic comparison: 11 working 2-edge switches vs counterexamples.
Find the distinguishing property.
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess

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

def weighted_sum(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def get_switch_properties(G, v1, w1, v2, w2):
    """Extract comprehensive properties of the switch."""
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    # Degrees in G
    degs = {x: G.degree(x) for x in S}
    
    # Internal edges within S
    internal_edges = [(u,v) for u,v in G.edges() if u in S and v in S]
    
    # Triangles through each switched edge
    tri_v1w1 = len(set(G.neighbors(v1)) & set(G.neighbors(w1)))
    tri_v2w2 = len(set(G.neighbors(v2)) & set(G.neighbors(w2)))
    
    # Edges between {v1,w1} and {v2,w2}
    cross_edges = []
    if G.has_edge(v1, v2): cross_edges.append(('v1','v2'))
    if G.has_edge(v1, w2): cross_edges.append(('v1','w2'))  # This should be False (switch adds it)
    if G.has_edge(w1, v2): cross_edges.append(('w1','v2'))  # This should be False
    if G.has_edge(w1, w2): cross_edges.append(('w1','w2'))
    
    # External intersections (sizes)
    ext_v1_w1 = len(ext[v1] & ext[w1])
    ext_v2_w2 = len(ext[v2] & ext[w2])
    ext_v1_w2 = len(ext[v1] & ext[w2])
    ext_v2_w1 = len(ext[v2] & ext[w1])
    ext_v1_v2 = len(ext[v1] & ext[v2])
    ext_w1_w2 = len(ext[w1] & ext[w2])
    
    # Weighted external intersections
    ws_v1_w1 = weighted_sum(G, ext[v1] & ext[w1])
    ws_v2_w2 = weighted_sum(G, ext[v2] & ext[w2])
    ws_v1_w2 = weighted_sum(G, ext[v1] & ext[w2])
    ws_v2_w1 = weighted_sum(G, ext[v2] & ext[w1])
    ws_v1_v2 = weighted_sum(G, ext[v1] & ext[v2])
    ws_w1_w2 = weighted_sum(G, ext[w1] & ext[w2])
    
    # External degree sequences (degrees of ext neighbors)
    ext_degs = {x: sorted([G.degree(y) for y in ext[x]]) for x in S}
    
    return {
        'degs': degs,
        'n_internal': len(internal_edges),
        'internal': internal_edges,
        'tri_v1w1': tri_v1w1,
        'tri_v2w2': tri_v2w2,
        'cross': cross_edges,
        'ext_sizes': {
            'v1∩w1': ext_v1_w1, 'v2∩w2': ext_v2_w2,
            'v1∩w2': ext_v1_w2, 'v2∩w1': ext_v2_w1,
            'v1∩v2': ext_v1_v2, 'w1∩w2': ext_w1_w2,
        },
        'ws': {
            'v1∩w1': ws_v1_w1, 'v2∩w2': ws_v2_w2,
            'v1∩w2': ws_v1_w2, 'v2∩w1': ws_v2_w1,
            'v1∩v2': ws_v1_v2, 'w1∩w2': ws_w1_w2,
        },
        'ext_degs': ext_degs,
        'ext': ext,
    }

# Load the 11 cospectral switches
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

cospectral = []
for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if switch:
        props = get_switch_properties(G1, *switch)
        cospectral.append((g1, switch, props))

# Get counterexamples
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

def spectra_equal(T1, T2, max_k=20):
    P1, P2 = T1.copy(), T2.copy()
    for k in range(1, max_k + 1):
        if not np.isclose(np.trace(P1), np.trace(P2), atol=1e-9):
            return False
        P1, P2 = P1 @ T1, P2 @ T2
    return True

result = subprocess.run(['geng', '-c', '8'], capture_output=True, text=True)
graphs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

counterexamples = []
for g6 in graphs:
    if len(counterexamples) >= 20:
        break
    G = to_graph(g6)
    if min(dict(G.degree()).values()) < 2:
        continue
    
    for e1, e2 in combinations(G.edges(), 2):
        if len(counterexamples) >= 20:
            break
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
                
                T_G, T_Gp = nbl_matrix(G), nbl_matrix(Gp)
                if not spectra_equal(T_G, T_Gp):
                    props = get_switch_properties(G, v1, w1, v2, w2)
                    counterexamples.append((g6, (v1, w1, v2, w2), props))
                    break

print("="*70)
print("COSPECTRAL SWITCHES (from 78 pairs)")
print("="*70)
for g6, sw, p in cospectral:
    print(f"\n{g6} switch={sw}")
    print(f"  tri(v1,w1)={p['tri_v1w1']}, tri(v2,w2)={p['tri_v2w2']}, equal={p['tri_v1w1']==p['tri_v2w2']}")
    print(f"  ext_sizes: {p['ext_sizes']}")
    print(f"  ws: v1∩w1={p['ws']['v1∩w1']:.3f}, v2∩w2={p['ws']['v2∩w2']:.3f}, v1∩w2={p['ws']['v1∩w2']:.3f}, v2∩w1={p['ws']['v2∩w1']:.3f}")
    print(f"  ws: v1∩v2={p['ws']['v1∩v2']:.3f}, w1∩w2={p['ws']['w1∩w2']:.3f}")
    print(f"  cross: {p['cross']}")

print("\n" + "="*70)
print("COUNTEREXAMPLES (C1+C2 satisfied, NOT cospectral)")
print("="*70)
for g6, sw, p in counterexamples[:10]:
    print(f"\n{g6} switch={sw}")
    print(f"  tri(v1,w1)={p['tri_v1w1']}, tri(v2,w2)={p['tri_v2w2']}, equal={p['tri_v1w1']==p['tri_v2w2']}")
    print(f"  ext_sizes: {p['ext_sizes']}")
    print(f"  ws: v1∩w1={p['ws']['v1∩w1']:.3f}, v2∩w2={p['ws']['v2∩w2']:.3f}, v1∩w2={p['ws']['v1∩w2']:.3f}, v2∩w1={p['ws']['v2∩w1']:.3f}")
    print(f"  ws: v1∩v2={p['ws']['v1∩v2']:.3f}, w1∩w2={p['ws']['w1∩w2']:.3f}")
    print(f"  cross: {p['cross']}")
