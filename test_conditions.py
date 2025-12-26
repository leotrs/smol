"""
Test stronger condition: all 6 weighted sums satisfy certain symmetries.

The 2x2 matrix of ws(vi, wj) we've checked.
But there are also ws(v1,v2) and ws(w1,w2).

Maybe we need: ws(v1∩v2) = ws(w1∩w2)?
Or non-empty v1∩v2 and w1∩w2?
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess

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

result = subprocess.run(['geng', '-c', '8'], capture_output=True, text=True)
graphs = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

# Test various conditions
conditions = {
    'base': lambda G, v1, w1, v2, w2, ext, tol: True,  # Just C1+C2
    'all_ws_eq': lambda G, v1, w1, v2, w2, ext, tol: (
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v2]&ext[w2])) < tol and
        abs(ws(G, ext[v1]&ext[w2]) - ws(G, ext[v2]&ext[w1])) < tol and
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v1]&ext[w2])) < tol
    ),
    'all_ws_eq + tri': lambda G, v1, w1, v2, w2, ext, tol: (
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v2]&ext[w2])) < tol and
        abs(ws(G, ext[v1]&ext[w2]) - ws(G, ext[v2]&ext[w1])) < tol and
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v1]&ext[w2])) < tol and
        tri(G, v1, w1) == tri(G, v2, w2)
    ),
    'all_ws_eq + tri + ws_vv=ws_ww': lambda G, v1, w1, v2, w2, ext, tol: (
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v2]&ext[w2])) < tol and
        abs(ws(G, ext[v1]&ext[w2]) - ws(G, ext[v2]&ext[w1])) < tol and
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v1]&ext[w2])) < tol and
        tri(G, v1, w1) == tri(G, v2, w2) and
        abs(ws(G, ext[v1]&ext[v2]) - ws(G, ext[w1]&ext[w2])) < tol
    ),
    'all_ws_eq + tri + nonempty_vw': lambda G, v1, w1, v2, w2, ext, tol: (
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v2]&ext[w2])) < tol and
        abs(ws(G, ext[v1]&ext[w2]) - ws(G, ext[v2]&ext[w1])) < tol and
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v1]&ext[w2])) < tol and
        tri(G, v1, w1) == tri(G, v2, w2) and
        len(ext[v1]&ext[w1]) > 0
    ),
    'all_ws_eq + tri + nonempty_vv_ww': lambda G, v1, w1, v2, w2, ext, tol: (
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v2]&ext[w2])) < tol and
        abs(ws(G, ext[v1]&ext[w2]) - ws(G, ext[v2]&ext[w1])) < tol and
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v1]&ext[w2])) < tol and
        tri(G, v1, w1) == tri(G, v2, w2) and
        len(ext[v1]&ext[v2]) > 0 and len(ext[w1]&ext[w2]) > 0
    ),
    'all6_ws_eq + tri': lambda G, v1, w1, v2, w2, ext, tol: (
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v2]&ext[w2])) < tol and
        abs(ws(G, ext[v1]&ext[w2]) - ws(G, ext[v2]&ext[w1])) < tol and
        abs(ws(G, ext[v1]&ext[w1]) - ws(G, ext[v1]&ext[w2])) < tol and
        abs(ws(G, ext[v1]&ext[v2]) - ws(G, ext[w1]&ext[w2])) < tol and
        abs(ws(G, ext[v1]&ext[v2]) - ws(G, ext[v1]&ext[w1])) < tol and
        tri(G, v1, w1) == tri(G, v2, w2)
    ),
}

results = {k: {'cospec': 0, 'counter': 0} for k in conditions}
tol = 1e-9

for g6 in graphs:
    G = to_graph(g6)
    if min(dict(G.degree()).values()) < 2:
        continue
    for v1, w1, v2, w2, Gp, ext in find_c1c2_switches(G):
        T_G, T_Gp = nbl_matrix(G), nbl_matrix(Gp)
        is_cospec = spectra_equal(T_G, T_Gp)
        
        for name, cond in conditions.items():
            if cond(G, v1, w1, v2, w2, ext, tol):
                if is_cospec:
                    results[name]['cospec'] += 1
                else:
                    results[name]['counter'] += 1

print(f"{'Condition':<40} {'Cospec':>8} {'Counter':>8} {'Precision':>10}")
print("-" * 70)
for name, r in results.items():
    total = r['cospec'] + r['counter']
    prec = r['cospec'] / total if total > 0 else 0
    print(f"{name:<40} {r['cospec']:>8} {r['counter']:>8} {prec:>10.1%}")
