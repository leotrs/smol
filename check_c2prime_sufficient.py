"""
Check if (C1)+(C2') is SUFFICIENT for NBL-cospectrality.
Find switches that satisfy C2' but are NOT cospectral.
"""

import networkx as nx
import numpy as np
from itertools import combinations
import subprocess

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def nbl_matrix(G):
    edges = []
    for u, v in G.edges():
        edges.append((u, v))
        edges.append((v, u))
    edge_to_idx = {e: i for i, e in enumerate(edges)}
    n = len(edges)
    T = np.zeros((n, n))
    for (u, v), i in edge_to_idx.items():
        deg_v = G.degree(v)
        if deg_v <= 1:
            continue
        for w in G.neighbors(v):
            if w != u:
                j = edge_to_idx[(v, w)]
                T[i, j] = 1.0 / (deg_v - 1)
    return T

def spectra_equal(T1, T2, max_k=50, tol=1e-9):
    if T1.shape != T2.shape:
        return False
    P1, P2 = T1.copy(), T2.copy()
    for k in range(1, max_k + 1):
        if not np.isclose(np.trace(P1), np.trace(P2), atol=tol, rtol=tol):
            return False, k
        P1 = P1 @ T1
        P2 = P2 @ T2
    return True, max_k

def weighted_sum(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def find_c1c2prime_switches(G):
    """Find switches satisfying C1 + C2' (weighted)."""
    results = []
    for e1, e2 in combinations(G.edges(), 2):
        for v1, w1 in [e1, e1[::-1]]:
            for v2, w2 in [e2, e2[::-1]]:
                if G.has_edge(v1, w2) or G.has_edge(v2, w1):
                    continue
                S = {v1, v2, w1, w2}
                if len(S) != 4:
                    continue
                # C1
                if G.degree(v1) != G.degree(v2):
                    continue
                if G.degree(w1) != G.degree(w2):
                    continue
                # C2' (weighted)
                ext = {x: set(G.neighbors(x)) - S for x in S}
                ws1_w1 = weighted_sum(G, ext[v1] & ext[w1])
                ws2_w1 = weighted_sum(G, ext[v2] & ext[w1])
                if not np.isclose(ws1_w1, ws2_w1, atol=1e-9):
                    continue
                ws1_w2 = weighted_sum(G, ext[v1] & ext[w2])
                ws2_w2 = weighted_sum(G, ext[v2] & ext[w2])
                if not np.isclose(ws1_w2, ws2_w2, atol=1e-9):
                    continue
                
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)
                results.append((v1, w1, v2, w2, Gp))
    return results

def generate_graphs(n):
    result = subprocess.run(['geng', '-c', str(n)], capture_output=True, text=True)
    return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

counterexamples = []
total = 0

for n in range(4, 9):
    print(f"n={n}: ", end="", flush=True)
    graphs = generate_graphs(n)
    n_switches = 0
    n_cosp = 0
    
    for g6 in graphs:
        G = to_graph(g6)
        if min(dict(G.degree()).values()) < 2:
            continue
        
        for v1, w1, v2, w2, Gp in find_c1c2prime_switches(G):
            n_switches += 1
            T_G = nbl_matrix(G)
            T_Gp = nbl_matrix(Gp)
            
            equal, k = spectra_equal(T_G, T_Gp)
            if equal:
                n_cosp += 1
            else:
                counterexamples.append((g6, (v1, w1, v2, w2), k))
    
    total += n_switches
    print(f"{n_switches} (C2') switches, {n_cosp} cospectral, {n_switches - n_cosp} counterexamples")

print(f"\nTOTAL: {total} (C2') switches, {len(counterexamples)} counterexamples")

if counterexamples:
    print("\nFirst 5 counterexamples:")
    for g6, sw, k in counterexamples[:5]:
        print(f"  {g6}, switch {sw}, diverged at k={k}")
