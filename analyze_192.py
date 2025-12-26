"""
Analyze the 192 counterexamples that pass all_ws_eq + tri + nonempty_vv_ww.
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess
from collections import Counter

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

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
        if not np.isclose(np.trace(P1), np.trace(P2), atol=1e-9):
            return False
        P1, P2 = P1 @ T1, P2 @ T2
    return True

def ws(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def tri(G, u, v):
    return len(set(G.neighbors(u)) & set(G.neighbors(v)))

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
                results.append((v1, w1, v2, w2, Gp, ext))
    return results

def passes_condition(G, v1, w1, v2, w2, ext, tol=1e-9):
    return (
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v2]&ext[w2])) < tol and
        abs(ws(G, ext[v1]&ext[w2]) - ws(G, ext[v2]&ext[w1])) < tol and
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v1]&ext[w2])) < tol and
        tri(G, v1, w1) == tri(G, v2, w2) and
        len(ext[v1]&ext[v2]) > 0 and len(ext[w1]&ext[w2]) > 0
    )

result = subprocess.run(['geng', '-c', '8'], capture_output=True, text=True)
graphs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

counterexamples = []

for g6 in graphs:
    G = to_graph(g6)
    if min(dict(G.degree()).values()) < 2:
        continue
    for v1, w1, v2, w2, Gp, ext in find_c1c2_switches(G):
        if not passes_condition(G, v1, w1, v2, w2, ext):
            continue
        T_G, T_Gp = nbl_matrix(G), nbl_matrix(Gp)
        if not spectra_equal(T_G, T_Gp):
            # Collect info
            info = {
                'g6': g6,
                'switch': (v1, w1, v2, w2),
                'degs': (G.degree(v1), G.degree(w1)),
                'tri': tri(G, v1, w1),
                'ws': ws(G, ext[v1]&ext[w1]),
                'int_vw': len(ext[v1]&ext[w1]),
                'int_vv': len(ext[v1]&ext[v2]),
                'int_ww': len(ext[w1]&ext[w2]),
                'ws_vv': ws(G, ext[v1]&ext[v2]),
                'ws_ww': ws(G, ext[w1]&ext[w2]),
                # Internal structure
                'v1v2_edge': G.has_edge(v1, v2),
                'w1w2_edge': G.has_edge(w1, w2),
            }
            counterexamples.append(info)

print(f"Found {len(counterexamples)} counterexamples")
print()

# Analyze patterns
print("=== Internal edge patterns ===")
v1v2_edge = Counter(c['v1v2_edge'] for c in counterexamples)
w1w2_edge = Counter(c['w1w2_edge'] for c in counterexamples)
both_edge = Counter((c['v1v2_edge'], c['w1w2_edge']) for c in counterexamples)
print(f"v1-v2 edge: {dict(v1v2_edge)}")
print(f"w1-w2 edge: {dict(w1w2_edge)}")
print(f"(v1v2, w1w2): {dict(both_edge)}")
print()

print("=== ws(vv) vs ws(ww) ===")
ws_equal = sum(1 for c in counterexamples if abs(c['ws_vv'] - c['ws_ww']) < 1e-9)
print(f"ws_vv = ws_ww: {ws_equal}/{len(counterexamples)}")
print()

print("=== Degree patterns ===")
deg_counts = Counter(c['degs'] for c in counterexamples)
print(f"(deg_v, deg_w): {dict(deg_counts)}")
print()

print("=== First 10 counterexamples ===")
for c in counterexamples[:10]:
    print(f"{c['g6']} sw={c['switch']}")
    print(f"  degs={c['degs']}, tri={c['tri']}, ws={c['ws']:.3f}")
    print(f"  int: vw={c['int_vw']}, vv={c['int_vv']}, ww={c['int_ww']}")
    print(f"  ws_vv={c['ws_vv']:.3f}, ws_ww={c['ws_ww']:.3f}")
    print(f"  edges: v1v2={c['v1v2_edge']}, w1w2={c['w1w2_edge']}")
    print()
