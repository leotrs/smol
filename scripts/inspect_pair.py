#!/usr/bin/env python3
"""Inspect a specific cospectral pair."""

import sys
import networkx as nx
import numpy as np


def inspect_pair(g6_1, g6_2):
    G = nx.from_graph6_bytes(g6_1.encode())
    H = nx.from_graph6_bytes(g6_2.encode())

    print(f"Graph 1: {g6_1}")
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    print(f"  Degree sequence: {sorted([d for n, d in G.degree()], reverse=True)}")
    print(f"  Edges: {sorted(G.edges())}")

    print(f"\nGraph 2: {g6_2}")
    print(f"  Nodes: {H.number_of_nodes()}, Edges: {H.number_of_edges()}")
    print(f"  Degree sequence: {sorted([d for n, d in H.degree()], reverse=True)}")
    print(f"  Edges: {sorted(H.edges())}")

    # Check spectrum
    A_G = nx.adjacency_matrix(G).todense()
    A_H = nx.adjacency_matrix(H).todense()
    evals_G = sorted(np.linalg.eigvalsh(A_G))
    evals_H = sorted(np.linalg.eigvalsh(A_H))

    print(f"\nEigenvalues G: {[f'{x:.6f}' for x in evals_G]}")
    print(f"Eigenvalues H: {[f'{x:.6f}' for x in evals_H]}")
    print(f"Cospectral: {np.allclose(evals_G, evals_H, atol=1e-6)}")

    # Find edge differences
    edges_G = set(G.edges())
    edges_H = set(H.edges())
    removed = edges_G - edges_H
    added = edges_H - edges_G

    print("\nEdge differences:")
    print(f"  Removed from G: {sorted(removed)}")
    print(f"  Added to H: {sorted(added)}")
    print(f"  Total changed: {len(removed)} removed, {len(added)} added")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python inspect_pair.py <graph6_1> <graph6_2>")
        sys.exit(1)

    inspect_pair(sys.argv[1], sys.argv[2])
