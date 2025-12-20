#!/usr/bin/env python3
"""Fix complex eigenvalue sorting bug."""

import networkx as nx
import numpy as np

g6 = 'ECZO'
G1 = nx.from_graph6_bytes(g6.encode())
G2 = G1.copy()
G2.remove_edge(0, 3)
G2.remove_edge(1, 4)
G2.add_edge(0, 4)
G2.add_edge(1, 3)

def build_NBL(G):
    directed_edges = [(u,v) for u,v in G.edges()] + [(v,u) for u,v in G.edges()]
    edge_to_idx = {e: i for i, e in enumerate(directed_edges)}
    m = len(directed_edges)
    T = np.zeros((m, m))
    for i, (u, v) in enumerate(directed_edges):
        d = G.degree(v) - 1
        if d > 0:
            for w in G.neighbors(v):
                if w != u:
                    T[i, edge_to_idx[(v, w)]] = 1.0 / d
    return np.eye(m) - T

L1 = build_NBL(G1)
L2 = build_NBL(G2)

eig1 = np.linalg.eigvals(L1)
eig2 = np.linalg.eigvals(L2)

# Wrong way: np.sort
print('Wrong (np.sort):')
print(f'  Distance: {np.linalg.norm(np.sort(eig1) - np.sort(eig2)):.2e}')

# Better: sort by (real, |imag|)
def sort_eigs(eigs):
    return sorted(eigs, key=lambda x: (round(x.real, 10), round(abs(x.imag), 10)))

e1 = np.array(sort_eigs(eig1))
e2 = np.array(sort_eigs(eig2))
print(f'Better (real, |imag|): {np.linalg.norm(e1 - e2):.2e}')

# Spectral hash approach - round to 8 decimals
def spectral_hash(eigs, decimals=8):
    rounded = [round(e.real, decimals) + round(e.imag, decimals)*1j for e in eigs]
    return sorted(rounded, key=lambda x: (x.real, x.imag))

h1, h2 = spectral_hash(eig1), spectral_hash(eig2)
print(f'Spectral hash match: {h1 == h2}')
print(f'Hash distance: {np.linalg.norm(np.array(h1) - np.array(h2)):.2e}')
