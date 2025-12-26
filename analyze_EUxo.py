"""
Detailed analysis of the EUxo counterexample.
"""

import networkx as nx
import numpy as np

def to_graph(g6):
    return nx.from_graph6_bytes(g6.encode())

def nbl_matrix(G):
    """Compute the NBL transition matrix."""
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
    
    return T, edges, edge_to_idx

# Load EUxo
G = to_graph('EUxo')
print("=== Graph EUxo ===")
print(f"Vertices: {list(G.nodes())}")
print(f"Edges: {list(G.edges())}")
print(f"Degrees: {dict(G.degree())}")
print()

# Draw adjacency
print("Adjacency structure:")
for v in G.nodes():
    print(f"  {v}: neighbors = {list(G.neighbors(v))}")
print()

# The counterexample switch: (0, 2, 3, 1)
# This means v1=0, w1=2, v2=3, w2=1
# G has edges 0-2, 3-1
# G' swaps to 0-1, 3-2
v1, w1, v2, w2 = 0, 2, 3, 1
S = {v1, v2, w1, w2}

print("=== Switch Analysis ===")
print(f"v1={v1}, w1={w1}, v2={v2}, w2={w2}")
print(f"S = {S}")
print()

# Check (C1): degree equality
print("(C1) Degree equality:")
print(f"  deg(v1={v1}) = {G.degree(v1)}, deg(v2={v2}) = {G.degree(v2)} -> equal: {G.degree(v1) == G.degree(v2)}")
print(f"  deg(w1={w1}) = {G.degree(w1)}, deg(w2={w2}) = {G.degree(w2)} -> equal: {G.degree(w1) == G.degree(w2)}")
print()

# External neighborhoods
ext = {x: set(G.neighbors(x)) - S for x in S}
print("External neighborhoods (ext(x) = N(x) \\ S):")
for x in S:
    print(f"  ext({x}) = {ext[x]}")
print()

# Check (C2): intersection equality
print("(C2) Intersection equality:")
print(f"  |ext(v1) ∩ ext(w1)| = |ext({v1}) ∩ ext({w1})| = |{ext[v1] & ext[w1]}| = {len(ext[v1] & ext[w1])}")
print(f"  |ext(v2) ∩ ext(w1)| = |ext({v2}) ∩ ext({w1})| = |{ext[v2] & ext[w1]}| = {len(ext[v2] & ext[w1])}")
print(f"  Equal: {len(ext[v1] & ext[w1]) == len(ext[v2] & ext[w1])}")
print()
print(f"  |ext(v1) ∩ ext(w2)| = |ext({v1}) ∩ ext({w2})| = |{ext[v1] & ext[w2]}| = {len(ext[v1] & ext[w2])}")
print(f"  |ext(v2) ∩ ext(w2)| = |ext({v2}) ∩ ext({w2})| = |{ext[v2] & ext[w2]}| = {len(ext[v2] & ext[w2])}")
print(f"  Equal: {len(ext[v1] & ext[w2]) == len(ext[v2] & ext[w2])}")
print()

# Shared and unique
shared = ext[w1] & ext[w2]
unique1 = ext[w1] - ext[w2]
unique2 = ext[w2] - ext[w1]
print("Hub external partition:")
print(f"  shared = ext(w1) ∩ ext(w2) = {shared}")
print(f"  unique1 = ext(w1) \\ ext(w2) = {unique1}")
print(f"  unique2 = ext(w2) \\ ext(w1) = {unique2}")
print()

# Create G'
Gp = G.copy()
Gp.remove_edge(v1, w1)
Gp.remove_edge(v2, w2)
Gp.add_edge(v1, w2)
Gp.add_edge(v2, w1)

print("=== Graph G' (after switch) ===")
print(f"Edges: {list(Gp.edges())}")
print(f"Degrees: {dict(Gp.degree())}")
print()

# Compute NBL matrices
T_G, edges_G, idx_G = nbl_matrix(G)
T_Gp, edges_Gp, idx_Gp = nbl_matrix(Gp)

print("=== NBL Spectra ===")
eigs_G = np.linalg.eigvals(T_G)
eigs_Gp = np.linalg.eigvals(T_Gp)

eigs_G_sorted = sorted(eigs_G, key=lambda x: (round(x.real, 6), round(x.imag, 6)))
eigs_Gp_sorted = sorted(eigs_Gp, key=lambda x: (round(x.real, 6), round(x.imag, 6)))

print("G eigenvalues:")
for e in eigs_G_sorted:
    print(f"  {e:.6f}")
print()
print("G' eigenvalues:")
for e in eigs_Gp_sorted:
    print(f"  {e:.6f}")
print()

# Check traces
print("=== Trace comparison ===")
for k in range(1, 7):
    tr_G = np.trace(np.linalg.matrix_power(T_G, k))
    tr_Gp = np.trace(np.linalg.matrix_power(T_Gp, k))
    match = "✓" if np.isclose(tr_G, tr_Gp) else "✗"
    print(f"  tr(T^{k}): G={tr_G:.6f}, G'={tr_Gp:.6f} {match}")

# More careful spectrum comparison
print("\n=== Detailed eigenvalue comparison ===")
for i, (e1, e2) in enumerate(zip(eigs_G_sorted, eigs_Gp_sorted)):
    diff = abs(e1 - e2)
    print(f"  {i}: G={e1:.10f}, G'={e2:.10f}, diff={diff:.2e}")

print(f"\nMax eigenvalue difference: {max(abs(e1-e2) for e1, e2 in zip(eigs_G_sorted, eigs_Gp_sorted)):.2e}")

# Check if spectra are actually equal
are_equal = np.allclose(sorted(eigs_G, key=lambda x: (x.real, x.imag)),
                        sorted(eigs_Gp, key=lambda x: (x.real, x.imag)),
                        atol=1e-8)
print(f"Spectra equal (atol=1e-8): {are_equal}")
