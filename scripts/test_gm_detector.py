#!/usr/bin/env python3
"""Test the GM switching detector with a known example."""

import networkx as nx
from detect_gm_switching import is_gm_switching


def create_gm_pair():
    """Create a known GM switching pair.

    Example with n=6, V1={0,1}, V2={2,3}, V3={4,5}

    G: Complete bipartite K_{2,2} between V1 and V2, plus some edges in V3
    G': Cliques on V1 and V2, same V3 structure
    """
    # Create G with complete bipartite between {0,1} and {2,3}
    G = nx.Graph()
    G.add_nodes_from(range(6))

    # Complete bipartite between V1={0,1} and V2={2,3}
    for u in [0, 1]:
        for v in [2, 3]:
            G.add_edge(u, v)

    # Add some edges in V3={4,5} and to V3
    G.add_edge(4, 5)  # Edge in V3
    G.add_edge(0, 4)  # V1 to V3
    G.add_edge(2, 5)  # V2 to V3

    # Create G' by applying GM switch
    H = G.copy()

    # Remove V1-V2 edges
    for u in [0, 1]:
        for v in [2, 3]:
            H.remove_edge(u, v)

    # Add cliques on V1 and V2
    H.add_edge(0, 1)  # Clique on V1
    H.add_edge(2, 3)  # Clique on V2

    return G, H


def main():
    G, H = create_gm_pair()

    print("Testing GM detector with known example:")
    print(f"G has {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"H has {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")
    print(f"G edges: {sorted(G.edges())}")
    print(f"H edges: {sorted(H.edges())}")

    # Check if detector finds the GM switching
    result = is_gm_switching(G, H)
    print(f"\nGM switching detected: {result}")

    if result:
        print("✓ GM detector works correctly!")
    else:
        print("✗ GM detector failed on known example")

    # Also check reverse direction
    result_reverse = is_gm_switching(H, G)
    print(f"GM switching detected (reverse): {result_reverse}")

    # Check if they're actually cospectral
    import numpy as np
    A_G = nx.adjacency_matrix(G).todense()
    A_H = nx.adjacency_matrix(H).todense()
    evals_G = sorted(np.linalg.eigvalsh(A_G))
    evals_H = sorted(np.linalg.eigvalsh(A_H))

    print(f"\nEigenvalues G: {[f'{x:.4f}' for x in evals_G]}")
    print(f"Eigenvalues H: {[f'{x:.4f}' for x in evals_H]}")
    print(f"Cospectral: {np.allclose(evals_G, evals_H)}")


if __name__ == "__main__":
    main()
