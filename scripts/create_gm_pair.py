#!/usr/bin/env python3
"""Create a GM switching pair manually to test the detector.

Following Example 2.1 from Godsil & McKay (1982):
Start with two cospectral trees T₁ and T₂, then construct regular graphs.

Or simpler: Use the classical construction with equitable partition.
"""

import networkx as nx
import numpy as np
from gm_switching_proper import is_gm_switching_pair, apply_gm_switch


def create_simple_gm_pair():
    """Create a simple GM pair.

    Construction: Start with complete bipartite K_{2,2} between sets {0,1} and {2,3}.
    Add vertices {4,5} that are each adjacent to one vertex from each side.

    Partition: D={4,5}, C₁={0,1}, C₂={2,3}
    Each vertex in D is adjacent to exactly 1 vertex in C₁ and 1 vertex in C₂.

    For GM switching:
    - Vertex 4 is adjacent to half of C₁ (just vertex 0) and half of C₂ (just vertex 2)
    - Vertex 5 is adjacent to half of C₁ (just vertex 1) and half of C₂ (just vertex 3)

    After switching:
    - Vertex 4 connects to vertex 1 (instead of 0) in C₁, and vertex 3 (instead of 2) in C₂
    - Vertex 5 connects to vertex 0 (instead of 1) in C₁, and vertex 2 (instead of 3) in C₂
    """
    G = nx.Graph()
    G.add_nodes_from(range(6))

    # Complete bipartite between {0,1} and {2,3}
    for i in [0, 1]:
        for j in [2, 3]:
            G.add_edge(i, j)

    # Add connections from switching set
    G.add_edge(4, 0)  # vertex 4 -> half of C₁
    G.add_edge(4, 2)  # vertex 4 -> half of C₂
    G.add_edge(5, 1)  # vertex 5 -> other half of C₁
    G.add_edge(5, 3)  # vertex 5 -> other half of C₂

    # Now apply GM switching
    switching_set = {4, 5}
    partition = [[0, 1], [2, 3]]

    H = apply_gm_switch(G, switching_set, partition)

    return G, H, switching_set, partition


def check_cospectral(G, H):
    """Check if two graphs are cospectral."""
    A_G = nx.adjacency_matrix(G).todense()
    A_H = nx.adjacency_matrix(H).todense()
    evals_G = sorted(np.linalg.eigvalsh(A_G))
    evals_H = sorted(np.linalg.eigvalsh(A_H))
    return np.allclose(evals_G, evals_H, atol=1e-6)


def main():
    G, H, switching_set, partition = create_simple_gm_pair()

    print("Created GM switching pair:")
    print(f"G: {G.number_of_nodes()} vertices, {G.number_of_edges()} edges")
    print(f"  Edges: {sorted(G.edges())}")
    print(f"H: {H.number_of_nodes()} vertices, {H.number_of_edges()} edges")
    print(f"  Edges: {sorted(H.edges())}")
    print()

    print("Construction:")
    print(f"  Switching set D = {switching_set}")
    print(f"  Partition = {partition}")
    print()

    # Check if isomorphic
    iso = nx.is_isomorphic(G, H)
    print(f"Isomorphic: {iso}")

    # Check if cospectral
    cospec = check_cospectral(G, H)
    print(f"Cospectral: {cospec}")

    if cospec:
        A_G = nx.adjacency_matrix(G).todense()
        evals_G = sorted(np.linalg.eigvalsh(A_G))
        print(f"  Spectrum: {[f'{x:.4f}' for x in evals_G]}")
    print()

    # Test detector
    result, found_switching, found_partition = is_gm_switching_pair(G, H)
    print(f"GM detector result: {result}")
    if result:
        print(f"  Found switching set: {found_switching}")
        print(f"  Found partition: {found_partition}")
    else:
        print("  Detector did NOT find GM switching!")
        print("  This means the detector is broken or the construction isn't valid.")


if __name__ == "__main__":
    main()
