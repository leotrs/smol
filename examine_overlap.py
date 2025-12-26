"""
Examine the overlapping signature cases.
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

def get_detailed_props(G, v1, w1, v2, w2):
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    p = {}
    
    for (a, b), name in [((v1,w1),'v1w1'), ((v2,w2),'v2w2'), ((v1,w2),'v1w2'), 
                         ((v2,w1),'v2w1'), ((v1,v2),'v1v2'), ((w1,w2),'w1w2')]:
        p[name] = len(ext[a] & ext[b])
        p[f'ws_{name}'] = round(ws(G, ext[a] & ext[b]), 6)
        p[f'int_degs_{name}'] = tuple(sorted([G.degree(x) for x in ext[a] & ext[b]]))
    
    p['tri_v1w1'] = tri(G, v1, w1)
    p['tri_v2w2'] = tri(G, v2, w2)
    p['tri_v1w2'] = tri(G, v1, w2)
    p['tri_v2w1'] = tri(G, v2, w1)
    
    p['e_v1v2'] = G.has_edge(v1, v2)
    p['e_w1w2'] = G.has_edge(w1, w2)
    
    for x, name in [(v1,'v1'), (w1,'w1'), (v2,'v2'), (w2,'w2')]:
        p[f'deg_{name}'] = G.degree(x)
        p[f'ext_degs_{name}'] = tuple(sorted([G.degree(y) for y in ext[x]]))
        p[f'ext_size_{name}'] = len(ext[x])
    
    # Full external neighborhoods for comparison
    p['ext_v1'] = ext[v1]
    p['ext_w1'] = ext[w1]
    p['ext_v2'] = ext[v2]
    p['ext_w2'] = ext[w2]
    
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

# The overlapping signature
target_sig = (1, 1, 0, 1, 0.25, 0, 0.25, False, False)
# (v1w1, v1w2, v1v2, w1w2, ws_v1w1, ws_v1v2, ws_w1w2, e_v1v2, e_w1w2)

# Get cospectral cases with this signature
print("COSPECTRAL CASES WITH OVERLAPPING SIGNATURE:")
print("="*70)

# ICQbUjqz? and ICQeRhuv?
for g6 in ['ICQbUjqz?', 'ICQeRhuv?']:
    G = to_graph(g6)
    
    # Find the 2-edge switch manually
    pairs = []
    with open('docs/78_pairs.txt') as f:
        for line in f:
            if g6 in line:
                g1, g2 = line.strip().split(',')
                G1 = to_graph(g1)
                G2 = to_graph(g2)
                
                e1 = set(frozenset(e) for e in G1.edges())
                e2 = set(frozenset(e) for e in G2.edges())
                removed = list(e1 - e2)
                added = list(e2 - e1)
                
                print(f"\n{g6}")
                print(f"  Removed: {[tuple(e) for e in removed]}")
                print(f"  Added: {[tuple(e) for e in added]}")
                print(f"  Edges: {list(G1.edges())}")
                print(f"  Degrees: {dict(G1.degree())}")
                
                # Get the switch
                for (a, b), (c, d) in [(removed[0], removed[1]), (removed[1], removed[0])]:
                    for v1, w1 in [(tuple(a)[0], tuple(a)[1]), (tuple(a)[1], tuple(a)[0])]:
                        for v2, w2 in [(tuple(c)[0], tuple(c)[1]), (tuple(c)[1], tuple(c)[0])]:
                            exp = {frozenset({v1, w2}), frozenset({v2, w1})}
                            act = set(added)
                            if exp == act:
                                p = get_detailed_props(G1, v1, w1, v2, w2)
                                print(f"  Switch: ({v1},{w1},{v2},{w2})")
                                print(f"  ext_v1={p['ext_v1']}, ext_w1={p['ext_w1']}")
                                print(f"  ext_v2={p['ext_v2']}, ext_w2={p['ext_w2']}")
                                print(f"  ext_degs_v1={p['ext_degs_v1']}, ext_degs_w1={p['ext_degs_w1']}")
                                print(f"  ext_degs_v2={p['ext_degs_v2']}, ext_degs_w2={p['ext_degs_w2']}")
                                print(f"  int_degs_v1w1={p['int_degs_v1w1']}, int_degs_w1w2={p['int_degs_w1w2']}")

# Now find counterexamples with same signature
print("\n" + "="*70)
print("COUNTEREXAMPLES WITH OVERLAPPING SIGNATURE:")
print("="*70)

result = subprocess.run(['geng', '-c', '-d2', '8'], capture_output=True, text=True)
graphs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

count = 0
for g6 in graphs:
    if count >= 5:
        break
    G = to_graph(g6)
    
    for e1, e2 in combinations(G.edges(), 2):
        if count >= 5:
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
                
                # C2
                if len(ext[v1] & ext[w1]) != len(ext[v2] & ext[w1]):
                    continue
                if len(ext[v1] & ext[w2]) != len(ext[v2] & ext[w2]):
                    continue
                
                # Check signature
                v1w1 = len(ext[v1] & ext[w1])
                v1w2 = len(ext[v1] & ext[w2])
                v1v2 = len(ext[v1] & ext[v2])
                w1w2 = len(ext[w1] & ext[w2])
                ws_v1w1 = round(ws(G, ext[v1] & ext[w1]), 6)
                ws_v1v2 = round(ws(G, ext[v1] & ext[v2]), 6)
                ws_w1w2 = round(ws(G, ext[w1] & ext[w2]), 6)
                e_v1v2 = G.has_edge(v1, v2)
                e_w1w2 = G.has_edge(w1, w2)
                
                sig = (v1w1, v1w2, v1v2, w1w2, ws_v1w1, ws_v1v2, ws_w1w2, e_v1v2, e_w1w2)
                
                if sig != target_sig:
                    continue
                
                # Check if counterexample
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)
                
                if not spectra_equal(nbl_matrix(G), nbl_matrix(Gp)):
                    p = get_detailed_props(G, v1, w1, v2, w2)
                    print(f"\n{g6} sw=({v1},{w1},{v2},{w2})")
                    print(f"  Edges: {list(G.edges())}")
                    print(f"  Degrees: {dict(G.degree())}")
                    print(f"  ext_v1={p['ext_v1']}, ext_w1={p['ext_w1']}")
                    print(f"  ext_v2={p['ext_v2']}, ext_w2={p['ext_w2']}")
                    print(f"  ext_degs_v1={p['ext_degs_v1']}, ext_degs_w1={p['ext_degs_w1']}")
                    print(f"  ext_degs_v2={p['ext_degs_v2']}, ext_degs_w2={p['ext_degs_w2']}")
                    print(f"  int_degs_v1w1={p['int_degs_v1w1']}, int_degs_w1w2={p['int_degs_w1w2']}")
                    count += 1
                    break
