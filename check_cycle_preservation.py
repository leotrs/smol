"""
Test (C1)+(C2)+(C3-cycles): switch must preserve all cycle counts.
This checks G vs G' directly - not a "local" condition.
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
        if d <= 1:
            continue
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

def count_cycles(H, max_k=8):
    """Count cycles of each length up to max_k."""
    counts = {}
    for k in range(3, max_k + 1):
        count = 0
        for start in H.nodes():
            stack = [(start, [start])]
            while stack:
                node, path = stack.pop()
                if len(path) == k:
                    if H.has_edge(node, start):
                        count += 1
                    continue
                for nbr in H.neighbors(node):
                    if nbr not in path:
                        stack.append((nbr, path + [nbr]))
        counts[k] = count // (2 * k)
    return counts

def find_c1c2_cycle_preserving_switches(G, max_cycle=8):
    """Find switches satisfying C1 + C2 + cycle preservation."""
    results = []
    cycles_G = count_cycles(G, max_cycle)
    
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
                # C2
                ext = {x: set(G.neighbors(x)) - S for x in S}
                if len(ext[v1] & ext[w1]) != len(ext[v2] & ext[w1]):
                    continue
                if len(ext[v1] & ext[w2]) != len(ext[v2] & ext[w2]):
                    continue
                
                # Build G'
                Gp = G.copy()
                Gp.remove_edge(v1, w1)
                Gp.remove_edge(v2, w2)
                Gp.add_edge(v1, w2)
                Gp.add_edge(v2, w1)
                
                # Check cycle preservation
                cycles_Gp = count_cycles(Gp, max_cycle)
                if cycles_G != cycles_Gp:
                    continue
                
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
        
        for v1, w1, v2, w2, Gp in find_c1c2_cycle_preserving_switches(G):
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

print(f"\nTOTAL: {total} cycle-preserving switches")
print(f"Cospectral: {cospectral}")
print(f"Counterexamples: {len(counterexamples)}")

if counterexamples:
    print("\nFirst 5 counterexamples:")
    for g6, sw, k in counterexamples[:5]:
        print(f"  {g6}, switch {sw}, diverged at k={k}")
else:
    print("\n✓ (C1)+(C2)+(cycle preservation) appears SUFFICIENT!")
