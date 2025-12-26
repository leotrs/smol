"""Analyze first counterexample G?bBdo"""

import networkx as nx
import numpy as np

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

G = to_graph('G?bBdo')
v1, w1, v2, w2 = 4, 0, 1, 6
S = {v1, v2, w1, w2}

print("=== G?bBdo ===")
print(f"Edges: {list(G.edges())}")
print(f"Degrees: {dict(G.degree())}")
print()

print(f"Switch: v1={v1}, w1={w1}, v2={v2}, w2={w2}")
print(f"S = {S}")
print()

# Check C1, C2
ext = {x: set(G.neighbors(x)) - S for x in S}
print("(C1) Degrees:")
print(f"  deg(v1={v1})={G.degree(v1)}, deg(v2={v2})={G.degree(v2)}")
print(f"  deg(w1={w1})={G.degree(w1)}, deg(w2={w2})={G.degree(w2)}")
print()

print("External neighborhoods:")
for x in S:
    print(f"  ext({x}) = {ext[x]}")
print()

print("(C2) Intersections:")
print(f"  |ext(v1) ∩ ext(w1)| = {len(ext[v1] & ext[w1])}, |ext(v2) ∩ ext(w1)| = {len(ext[v2] & ext[w1])}")
print(f"  |ext(v1) ∩ ext(w2)| = {len(ext[v1] & ext[w2])}, |ext(v2) ∩ ext(w2)| = {len(ext[v2] & ext[w2])}")
print()

# Build G'
Gp = G.copy()
Gp.remove_edge(v1, w1)
Gp.remove_edge(v2, w2)
Gp.add_edge(v1, w2)
Gp.add_edge(v2, w1)

print("=== G' (after switch) ===")
print(f"Edges: {list(Gp.edges())}")
print()

# Traces
T_G = nbl_matrix(G)
T_Gp = nbl_matrix(Gp)

print("=== Traces ===")
P_G, P_Gp = T_G.copy(), T_Gp.copy()
for k in range(1, 8):
    tr_G = np.trace(P_G)
    tr_Gp = np.trace(P_Gp)
    match = "✓" if np.isclose(tr_G, tr_Gp) else "✗"
    print(f"  tr(T^{k}): G={tr_G:.6f}, G'={tr_Gp:.6f}  {match}")
    P_G = P_G @ T_G
    P_Gp = P_Gp @ T_Gp

# Triangle counts
print(f"\nTriangle count: G={sum(nx.triangles(G).values())//3}, G'={sum(nx.triangles(Gp).values())//3}")
