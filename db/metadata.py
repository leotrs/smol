"""Graph metadata computation."""

import networkx as nx


def compute_metadata(G: nx.Graph) -> dict:
    """
    Compute structural metadata for a graph.

    Args:
        G: A networkx Graph

    Returns:
        Dictionary with metadata fields
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()

    degrees = [d for _, d in G.degree()]
    min_degree = min(degrees) if degrees else 0
    max_degree = max(degrees) if degrees else 0

    is_bipartite = nx.is_bipartite(G)
    is_planar, _ = nx.check_planarity(G)
    is_regular = min_degree == max_degree

    if nx.is_connected(G) and n > 0:
        eccentricities = nx.eccentricity(G)
        diameter = max(eccentricities.values())
        radius = min(eccentricities.values())
    else:
        diameter = None
        radius = None

    girth = nx.girth(G)
    if girth == float("inf"):
        girth = None  # Acyclic graph

    triangle_count = sum(nx.triangles(G).values()) // 3

    return {
        "n": n,
        "m": m,
        "is_bipartite": is_bipartite,
        "is_planar": is_planar,
        "is_regular": is_regular,
        "diameter": diameter,
        "radius": radius,
        "girth": girth,
        "min_degree": min_degree,
        "max_degree": max_degree,
        "triangle_count": triangle_count,
    }
