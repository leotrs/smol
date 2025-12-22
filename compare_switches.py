"""
Compare structural properties of:
1. The 11 cospectral direct-switch pairs (from 78)
2. Counterexamples (C1+C2 but NOT cospectral)
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

def analyze_switch(G, v1, w1, v2, w2):
    """Extract properties of a switch configuration."""
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    # Degrees
    degs = tuple(sorted([G.degree(v1), G.degree(w1), G.degree(v2), G.degree(w2)]))
    
    # Internal edges (edges within S)
    internal = [(u,v) for u,v in G.edges() if u in S and v in S]
    n_internal = len(internal)
    
    # Is v1-v2 edge present?
    v1v2_edge = G.has_edge(v1, v2)
    w1w2_edge = G.has_edge(w1, w2)
    
    # External overlap
    ext_overlap_v = len(ext[v1] & ext[v2])  # shared external neighbors of v1, v2
    ext_overlap_w = len(ext[w1] & ext[w2])

    # Triangles involving switched edges
    tri_v1w1 = len(set(G.neighbors(v1)) & set(G.neighbors(w1)))
    tri_v2w2 = len(set(G.neighbors(v2)) & set(G.neighbors(w2)))
    
    return {
        'degs': degs,
        'n_internal': n_internal,
        'v1v2_edge': v1v2_edge,
        'w1w2_edge': w1w2_edge,
        'ext_overlap_v': ext_overlap_v,
        'ext_overlap_w': ext_overlap_w,
        'tri_v1w1': tri_v1w1,
        'tri_v2w2': tri_v2w2,
    }

# Load the 11 cospectral pairs
pairs = []
with open('docs/78_pairs.txt') as f:
    for line in f:
        line = line.strip()
        if ',' in line:
            g1, g2 = line.split(',')
            pairs.append((g1, g2))

cospectral_switches = []
for g1, g2 in pairs:
    G1, G2 = to_graph(g1), to_graph(g2)
    switch = find_switch(G1, G2)
    if switch:
        props = analyze_switch(G1, *switch)
        cospectral_switches.append((g1, switch, props))

print("=== 11 COSPECTRAL SWITCHES ===")
for g6, sw, props in cospectral_switches:
    print(f"{g6[:12]}... {sw}")
    print(f"  degs={props['degs']}, internal={props['n_internal']}, v1v2={props['v1v2_edge']}, w1w2={props['w1w2_edge']}")
    print(f"  ext_overlap: v={props['ext_overlap_v']}, w={props['ext_overlap_w']}")
    print(f"  triangles: v1w1={props['tri_v1w1']}, v2w2={props['tri_v2w2']}")

# Now get some counterexamples
def find_c1c2_switches(G):
    results = []
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
                results.append((v1, w1, v2, w2, Gp))
    return results

def nbl_matrix(G):
    edges = [(u,v) for u,v in G.edges()] + [(v,u) for u,v in G.edges()]
    idx = {e:i for i,e in enumerate(edges)}
    n = len(edges)
    T = np.zeros((n, n))
    for (u,v), i in idx.items():
        d = G.degree(v)
        if d <= 1:
            continue
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

# Find counterexamples at n=8
print("\n=== COUNTEREXAMPLES (first 5) ===")
result = subprocess.run(['geng', '-c', '8'], capture_output=True, text=True)
graphs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

counter = 0
for g6 in graphs:
    G = to_graph(g6)
    if min(dict(G.degree()).values()) < 2:
        continue
    for v1, w1, v2, w2, Gp in find_c1c2_switches(G):
        T_G, T_Gp = nbl_matrix(G), nbl_matrix(Gp)
        if not spectra_equal(T_G, T_Gp):
            props = analyze_switch(G, v1, w1, v2, w2)
            print(f"{g6} {(v1,w1,v2,w2)}")
            print(f"  degs={props['degs']}, internal={props['n_internal']}, v1v2={props['v1v2_edge']}, w1w2={props['w1w2_edge']}")
            print(f"  ext_overlap: v={props['ext_overlap_v']}, w={props['ext_overlap_w']}")
            print(f"  triangles: v1w1={props['tri_v1w1']}, v2w2={props['tri_v2w2']}")
            counter += 1
            if counter >= 5:
                break
    if counter >= 5:
        break
