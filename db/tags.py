"""Graph tag detection.

Detects special graph types and returns a list of tags.
"""

import networkx as nx


def compute_tags(G: nx.Graph) -> list[str]:
    """Compute tags for a graph.

    Args:
        G: A networkx Graph

    Returns:
        List of tag strings (e.g., ['complete', 'regular', 'eulerian'])
    """
    tags = []
    n = G.number_of_nodes()
    m = G.number_of_edges()

    if n == 0:
        return tags

    degrees = [d for _, d in G.degree()]
    min_deg = min(degrees)
    max_deg = max(degrees)
    is_connected = nx.is_connected(G) if n > 0 else False

    # Regular: all vertices have same degree
    if min_deg == max_deg:
        tags.append("regular")

    # Eulerian: all vertices have even degree (and connected)
    if is_connected and all(d % 2 == 0 for d in degrees):
        tags.append("eulerian")

    # Tree: connected and m = n - 1
    is_tree = is_connected and m == n - 1
    if is_tree:
        tags.append("tree")

    # Complete: m = n(n-1)/2
    if m == n * (n - 1) // 2:
        tags.append("complete")

    # Cycle: 2-regular, connected, n = m
    if min_deg == max_deg == 2 and is_connected and n == m:
        tags.append("cycle")

    # Path: tree with max_degree <= 2
    if is_tree and max_deg <= 2:
        tags.append("path")

    # Star: tree with one vertex of degree n-1, others degree 1
    if is_tree and n >= 3:
        if sorted(degrees) == [1] * (n - 1) + [n - 1]:
            tags.append("star")

    # Wheel: one vertex of degree n-1, all others degree 3, and n >= 4
    if n >= 4 and is_connected:
        sorted_degrees = sorted(degrees)
        if sorted_degrees == [3] * (n - 1) + [n - 1]:
            tags.append("wheel")

    # Complete bipartite: bipartite and m = |A| * |B|
    if nx.is_bipartite(G) and is_connected:
        try:
            A, B = nx.bipartite.sets(G)
            if m == len(A) * len(B):
                tags.append("complete-bipartite")
        except nx.AmbiguousSolution:
            pass

    # Petersen graph: n=10, 3-regular, girth=5, diameter=2
    if n == 10 and min_deg == max_deg == 3:
        try:
            girth = nx.girth(G)
            diameter = nx.diameter(G)
            if girth == 5 and diameter == 2:
                tags.append("petersen")
        except nx.NetworkXError:
            pass

    return sorted(tags)
