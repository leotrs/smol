#!/usr/bin/env python3
"""Expanded GM switching detector with larger switching sets and multi-class partitions.

Enhancements over gm_switching_proper.py:
1. Switching sets up to size n//2 (was limited to 4)
2. Multi-class partitions (k=2,3,4) instead of just k=2
3. More thorough partition enumeration
"""

import networkx as nx
from itertools import combinations


def is_equitable_partition(G, partition):
    """Check if partition is equitable."""
    for i, class_i in enumerate(partition):
        if not class_i:
            continue
        v0 = class_i[0]
        neighbor_counts = []
        for j, class_j in enumerate(partition):
            count = sum(1 for u in class_j if G.has_edge(v0, u))
            neighbor_counts.append(count)

        for v in class_i[1:]:
            v_counts = []
            for j, class_j in enumerate(partition):
                count = sum(1 for u in class_j if G.has_edge(v, u))
                v_counts.append(count)
            if v_counts != neighbor_counts:
                return False

    return True


def can_gm_switch(G, switching_set, partition):
    """Check if GM switching can be applied."""
    for x in switching_set:
        for cell in partition:
            if x in cell:
                continue

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
    """Apply GM switching to graph G."""
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


def generate_k_partitions(vertices, k, min_class_size=1):
    """Generate all k-partitions of vertices.

    This is expensive, so we limit it.
    """
    n = len(vertices)

    if k == 1:
        yield [vertices]
        return

    if k > n:
        return

    # For k=2, enumerate all splits
    if k == 2:
        for size1 in range(min_class_size, n - min_class_size + 1):
            for class1 in combinations(vertices, size1):
                class1 = list(class1)
                class2 = [v for v in vertices if v not in class1]
                if len(class2) >= min_class_size:
                    yield [class1, class2]

    # For k=3, try different splits
    elif k == 3:
        for size1 in range(min_class_size, n - 2*min_class_size + 1):
            for class1 in combinations(vertices, size1):
                class1 = list(class1)
                remaining = [v for v in vertices if v not in class1]

                for size2 in range(min_class_size, len(remaining) - min_class_size + 1):
                    for class2 in combinations(remaining, size2):
                        class2 = list(class2)
                        class3 = [v for v in remaining if v not in class2]
                        if len(class3) >= min_class_size:
                            yield [class1, class2, class3]

    # For k=4, limit to smaller graphs
    elif k == 4 and n <= 9:
        for size1 in range(min_class_size, n - 3*min_class_size + 1):
            for class1 in combinations(vertices, size1):
                class1 = list(class1)
                remaining1 = [v for v in vertices if v not in class1]

                for size2 in range(min_class_size, len(remaining1) - 2*min_class_size + 1):
                    for class2 in combinations(remaining1, size2):
                        class2 = list(class2)
                        remaining2 = [v for v in remaining1 if v not in class2]

                        for size3 in range(min_class_size, len(remaining2) - min_class_size + 1):
                            for class3 in combinations(remaining2, size3):
                                class3 = list(class3)
                                class4 = [v for v in remaining2 if v not in class3]
                                if len(class4) >= min_class_size:
                                    yield [class1, class2, class3, class4]


def is_gm_switching_pair(G, H, max_switching_size=None, max_partition_classes=4):
    """Check if G and H are related by GM switching.

    Args:
        G, H: Graphs to compare
        max_switching_size: Maximum switching set size (default: n//2)
        max_partition_classes: Maximum number of partition classes (default: 4)
    """
    n = G.number_of_nodes()
    nodes = list(G.nodes())

    if max_switching_size is None:
        max_switching_size = max(1, n // 2)

    # Try different switching set sizes
    for switching_size in range(1, min(n, max_switching_size + 1)):
        for switching_set in combinations(nodes, switching_size):
            switching_set = set(switching_set)
            remaining = [v for v in nodes if v not in switching_set]

            if len(remaining) < 1:
                continue

            # Try k-partitions for k=2,3,4
            for k in range(2, min(max_partition_classes + 1, len(remaining) + 1)):
                partition_count = 0
                max_partitions = 1000 if k == 2 else (100 if k == 3 else 10)

                for partition in generate_k_partitions(remaining, k):
                    partition_count += 1
                    if partition_count > max_partitions:
                        break

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


if __name__ == "__main__":
    # Quick test
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from db.database import connect

    conn = connect()
    cur = conn.cursor()

    # Test on a few n=8 pairs
    cur.execute("""
        SELECT g1.graph6, g2.graph6
        FROM cospectral_mates cm
        JOIN graphs g1 ON cm.graph1_id = g1.id
        JOIN graphs g2 ON cm.graph2_id = g2.id
        WHERE cm.matrix_type = 'adj' AND g1.n = 8
        LIMIT 10
    """)

    pairs = cur.fetchall()
    found = 0

    for g6_1, g6_2 in pairs:
        G = nx.from_graph6_bytes(g6_1.encode())
        H = nx.from_graph6_bytes(g6_2.encode())

        result, _, _ = is_gm_switching_pair(G, H)
        if result:
            found += 1

    print(f"Found {found}/10 GM pairs in test")
    conn.close()
