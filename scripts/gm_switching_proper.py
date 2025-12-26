#!/usr/bin/env python3
"""Proper implementation of Godsil-McKay switching detection.

GM Switching: Given graph G with partition V = D ∪ C₁ ∪ ... ∪ Cₖ
- D is the switching set
- C₁, ..., Cₖ partition the remaining vertices
- Each vertex x ∈ D is adjacent to all, none, or exactly half of each Cᵢ
- Switch: for x adjacent to half of Cᵢ, swap which half x connects to

For spectrum preservation, need equitable partition conditions.

Reference: Godsil & McKay, "Constructing cospectral graphs" (1982)
"""

import networkx as nx
from itertools import combinations


def get_equitable_partitions(G, max_classes=4):
    """Generate candidate equitable partitions of G.

    An equitable partition is where vertices in the same class have the same
    number of neighbors in each other class.
    """
    n = G.number_of_nodes()
    nodes = list(G.nodes())

    # Try partitions based on degree sequence
    degree_partition = {}
    for v in nodes:
        deg = G.degree(v)
        if deg not in degree_partition:
            degree_partition[deg] = []
        degree_partition[deg].append(v)

    # Degree-based partition is equitable for regular graphs
    if len(degree_partition) <= max_classes:
        yield list(degree_partition.values())

    # Try automorphism-based partitions (orbits under automorphism group)
    # This is expensive, so only for small graphs
    if n <= 10:
        pass
        # Get canonical labeling which reveals symmetries
        # Skip for now - nauty not installed

    # For now, also try simple partitions
    # Split vertices into 2 classes of equal size
    if n >= 4 and n % 2 == 0:
        for split in combinations(nodes, n // 2):
            class1 = list(split)
            class2 = [v for v in nodes if v not in class1]
            yield [class1, class2]


def is_equitable_partition(G, partition):
    """Check if partition is equitable.

    A partition is equitable if vertices in the same class have the same
    number of neighbors in each other class.
    """
    for i, class_i in enumerate(partition):
        # Count neighbors in each other class for first vertex
        if not class_i:
            continue
        v0 = class_i[0]
        neighbor_counts = []
        for j, class_j in enumerate(partition):
            count = sum(1 for u in class_j if G.has_edge(v0, u))
            neighbor_counts.append(count)

        # Check all other vertices in class_i have same counts
        for v in class_i[1:]:
            v_counts = []
            for j, class_j in enumerate(partition):
                count = sum(1 for u in class_j if G.has_edge(v, u))
                v_counts.append(count)
            if v_counts != neighbor_counts:
                return False

    return True


def can_gm_switch(G, switching_set, partition):
    """Check if GM switching can be applied.

    Each vertex in switching_set must be adjacent to all, none, or exactly
    half of each partition class.
    """
    for x in switching_set:
        for cell in partition:
            if x in cell:
                continue  # x is in this cell, skip

            neighbors_in_cell = sum(1 for v in cell if G.has_edge(x, v))
            cell_size = len(cell)

            # Must be adjacent to all, none, or exactly half
            if neighbors_in_cell not in [0, cell_size, cell_size // 2]:
                return False

            # If half, cell must have even size
            if neighbors_in_cell == cell_size // 2 and cell_size % 2 != 0:
                return False

    return True


def apply_gm_switch(G, switching_set, partition):
    """Apply GM switching to graph G.

    For each vertex x in switching_set and each cell in partition where x
    is adjacent to exactly half the vertices, swap which half x connects to.
    """
    H = G.copy()

    for x in switching_set:
        for cell in partition:
            if x in cell:
                continue

            neighbors_in_cell = [v for v in cell if G.has_edge(x, v)]
            cell_size = len(cell)

            # Only switch if adjacent to exactly half
            if len(neighbors_in_cell) == cell_size // 2 and cell_size % 2 == 0:
                # Remove current edges
                for v in neighbors_in_cell:
                    H.remove_edge(x, v)

                # Add edges to the other half
                non_neighbors = [v for v in cell if not G.has_edge(x, v)]
                for v in non_neighbors:
                    H.add_edge(x, v)

    return H


def is_gm_switching_pair(G, H):
    """Check if G and H are related by GM switching.

    Try different switching sets and partitions to see if any produces H.
    """
    n = G.number_of_nodes()
    nodes = list(G.nodes())

    # Try different switching set sizes (typically small)
    for switching_size in range(1, min(n, 5)):
        for switching_set in combinations(nodes, switching_size):
            switching_set = set(switching_set)
            remaining = [v for v in nodes if v not in switching_set]

            # Try to partition the remaining vertices
            # For now, try simple 2-partition
            if len(remaining) < 2:
                continue

            # Try all 2-partitions of remaining vertices
            for split_size in range(1, len(remaining)):
                for split in combinations(remaining, split_size):
                    class1 = list(split)
                    class2 = [v for v in remaining if v not in class1]
                    partition = [class1, class2]

                    # Check if this is a valid GM configuration
                    if not is_equitable_partition(G, partition):
                        continue

                    if not can_gm_switch(G, switching_set, partition):
                        continue

                    # Apply GM switch and check if result is isomorphic to H
                    Gp = apply_gm_switch(G, switching_set, partition)
                    if nx.is_isomorphic(Gp, H):
                        return True, switching_set, partition

    return False, None, None


def test_on_known_examples():
    """Test on some known constructions."""
    import numpy as np

    print("Test 1: Simple regular graphs")
    # Two cospectral regular graphs from Godsil-McKay
    # Example: complement of C₆ vs. 2K₃
    G = nx.cycle_graph(6).copy()
    G = nx.complement(G)  # Complement of 6-cycle

    H = nx.Graph()
    H.add_edges_from([(0,1), (0,2), (1,2), (3,4), (3,5), (4,5)])  # 2K₃

    A_G = nx.adjacency_matrix(G).todense()
    A_H = nx.adjacency_matrix(H).todense()
    evals_G = sorted(np.linalg.eigvalsh(A_G))
    evals_H = sorted(np.linalg.eigvalsh(A_H))

    print(f"  G (compl C₆): {G.number_of_nodes()}v, {G.number_of_edges()}e")
    print(f"  H (2K₃): {H.number_of_nodes()}v, {H.number_of_edges()}e")
    print(f"  Cospectral: {np.allclose(evals_G, evals_H)}")

    result, switching_set, partition = is_gm_switching_pair(G, H)
    print(f"  GM switching: {result}")
    if result:
        print(f"    Switching set: {switching_set}")
        print(f"    Partition: {partition}")
    print()


if __name__ == "__main__":
    test_on_known_examples()
