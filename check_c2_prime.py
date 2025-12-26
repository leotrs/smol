"""
Check if strengthened (C2') explains the counterexamples.
C2': weighted sums must match, not just counts.
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
            return False
        P1 = P1 @ T1
        P2 = P2 @ T2
    return True

def weighted_sum(G, vertices):
    """Sum of 1/(deg(x)-1) for x in vertices."""
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def check_c2_prime(G, v1, w1, v2, w2, tol=1e-9):
    """Check strengthened C2': weighted intersection sums match."""
    S = {v1, v2, w1, w2}
    ext = {x: set(G.neighbors(x)) - S for x in S}
    
    # Check both pairs
    ws1_w1 = weighted_sum(G, ext[v1] & ext[w1])
    ws2_w1 = weighted_sum(G, ext[v2] & ext[w1])
    if not np.isclose(ws1_w1, ws2_w1, atol=tol):
        return False
    
    ws1_w2 = weighted_sum(G, ext[v1] & ext[w2])
    ws2_w2 = weighted_sum(G, ext[v2] & ext[w2])
    if not np.isclose(ws1_w2, ws2_w2, atol=tol):
        return False
    
    return True

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

def generate_graphs(n):
    result = subprocess.run(['geng', '-c', str(n)], capture_output=True, text=True)
    return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

# Test on n=8
print("Testing (C2') hypothesis on n=8...\n")

graphs = generate_graphs(8)
c2_only = 0  # satisfies C2 but not C2'
c2_prime = 0  # satisfies both C2 and C2'
c2_only_cospectral = 0
c2_prime_not_cospectral = 0

for g6 in graphs:
    G = to_graph(g6)
    if min(dict(G.degree()).values()) < 2:
        continue
    
    for v1, w1, v2, w2, Gp in find_c1c2_switches(G):
        satisfies_c2_prime = check_c2_prime(G, v1, w1, v2, w2)
        
        T_G = nbl_matrix(G)
        T_Gp = nbl_matrix(Gp)
        is_cospectral = spectra_equal(T_G, T_Gp)
        
        if satisfies_c2_prime:
            c2_prime += 1
            if not is_cospectral:
                c2_prime_not_cospectral += 1
        else:
            c2_only += 1
            if is_cospectral:
                c2_only_cospectral += 1

print(f"Satisfies (C2) only (not C2'): {c2_only}")
print(f"  Of these, cospectral anyway: {c2_only_cospectral}")
print()
print(f"Satisfies (C2'): {c2_prime}")
print(f"  Of these, NOT cospectral: {c2_prime_not_cospectral}")
print()

if c2_prime_not_cospectral == 0 and c2_only_cospectral == 0:
    print("✓ (C2') perfectly predicts NBL-cospectrality!")
elif c2_prime_not_cospectral == 0:
    print(f"(C2') is SUFFICIENT but not necessary ({c2_only_cospectral} extra cospectral)")
else:
    print(f"(C2') is NOT sufficient - {c2_prime_not_cospectral} counterexamples remain")
