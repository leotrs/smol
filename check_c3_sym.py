"""
Test (C3-sym): Diagonal symmetry condition.
- ws(ext(v1) ∩ ext(w1)) = ws(ext(v2) ∩ ext(w2))  [removed edges equivalent]
- ws(ext(v1) ∩ ext(w2)) = ws(ext(v2) ∩ ext(w1))  [added edges equivalent]
- tri(v1,w1) = tri(v2,w2)
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
            return False, k
        P1, P2 = P1 @ T1, P2 @ T2
    return True, max_k

def weighted_sum(G, vertices):
    return sum(1/(G.degree(x)-1) for x in vertices if G.degree(x) > 1)

def triangles_through_edge(G, u, v):
    return len(set(G.neighbors(u)) & set(G.neighbors(v)))

def find_c1c2c3sym_switches(G, tol=1e-9):
    """Find switches satisfying C1 + C2 + C3-sym."""
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
                
                ext = {x: set(G.neighbors(x)) - S for x in S}
                
                # C2
                if len(ext[v1] & ext[w1]) != len(ext[v2] & ext[w1]):
                    continue
                if len(ext[v1] & ext[w2]) != len(ext[v2] & ext[w2]):
                    continue
                
                # C3-sym: diagonal symmetry
                # Removed edges equivalent
                ws_v1w1 = weighted_sum(G, ext[v1] & ext[w1])
                ws_v2w2 = weighted_sum(G, ext[v2] & ext[w2])
                if not np.isclose(ws_v1w1, ws_v2w2, atol=tol):
                    continue
                
                # Added edges equivalent  
                ws_v1w2 = weighted_sum(G, ext[v1] & ext[w2])
                ws_v2w1 = weighted_sum(G, ext[v2] & ext[w1])
                if not np.isclose(ws_v1w2, ws_v2w1, atol=tol):
                    continue
                
                # Triangle counts through removed edges
                if triangles_through_edge(G, v1, w1) != triangles_through_edge(G, v2, w2):
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

total = 0
cospectral = 0
counterexamples = []

for n in range(4, 9):
    print(f"n={n}: ", end="", flush=True)
    graphs = generate_graphs(n)
    n_sw, n_cosp = 0, 0
    
    for g6 in graphs:
        G = to_graph(g6)
        if min(dict(G.degree()).values()) < 2:
            continue
        
        for v1, w1, v2, w2, Gp in find_c1c2c3sym_switches(G):
            n_sw += 1
            T_G, T_Gp = nbl_matrix(G), nbl_matrix(Gp)
            eq, k = spectra_equal(T_G, T_Gp)
            if eq:
                n_cosp += 1
            else:
                counterexamples.append((g6, (v1, w1, v2, w2), k))
    
    total += n_sw
    cospectral += n_cosp
    print(f"{n_sw} switches, {n_cosp} cospectral, {n_sw - n_cosp} counterexamples")

print(f"\nTOTAL: {total} (C1+C2+C3-sym) switches")
print(f"Cospectral: {cospectral}")
print(f"Counterexamples: {len(counterexamples)}")

if counterexamples:
    print("\nFirst 10 counterexamples (diverged at k):")
    for g6, sw, k in counterexamples[:10]:
        print(f"  {g6}, switch {sw}, k={k}")
else:
    print("\n✓ (C1)+(C2)+(C3-sym) appears SUFFICIENT!")
