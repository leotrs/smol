"""Basic SMOL API usage examples.

This script demonstrates simple queries to the SMOL API:
- Looking up a specific graph by its graph6 encoding
- Querying graphs by structural properties
- Getting database statistics

Requirements:
    pip install requests

Usage:
    python basic_api.py
"""

import requests

BASE_URL = "http://localhost:8000"  # Change to production URL when deployed


def lookup_graph(graph6: str) -> dict:
    """Look up a graph by its graph6 encoding."""
    response = requests.get(f"{BASE_URL}/graph/{graph6}")
    response.raise_for_status()
    return response.json()


def query_graphs(params: dict) -> list:
    """Query graphs by properties."""
    response = requests.get(f"{BASE_URL}/graphs", params=params)
    response.raise_for_status()
    return response.json()


def get_stats() -> dict:
    """Get database statistics."""
    response = requests.get(f"{BASE_URL}/stats")
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Example 1: Look up K_5 (complete graph on 5 vertices)
    print("=" * 60)
    print("Example 1: Look up K_5 (graph6: D~{)")
    print("=" * 60)

    k5 = lookup_graph("D~{")
    print(f"Graph: {k5['graph6']}")
    print(f"Vertices: {k5['n']}, Edges: {k5['m']}")
    print("Properties:")
    print(f"  - Regular: {k5['properties']['is_regular']}")
    print(f"  - Diameter: {k5['properties']['diameter']}")
    print(f"  - Clique number: {k5['properties']['clique_number']}")
    print(f"  - Chromatic number: {k5['properties']['chromatic_number']}")
    print(f"Adjacency eigenvalues: {k5['spectra']['adj_eigenvalues']}")
    print()

    # Example 2: Find all 3-regular graphs on 6 vertices
    print("=" * 60)
    print("Example 2: Find 3-regular graphs on 6 vertices")
    print("=" * 60)

    regular_graphs = query_graphs({"n": 6, "regular": True, "min_degree": 3, "max_degree": 3})
    print(f"Found {len(regular_graphs)} graphs:")
    for g in regular_graphs:
        print(f"  {g['graph6']}: {g['m']} edges, diameter={g['properties']['diameter']}")
    print()

    # Example 3: Find bipartite graphs on 7 vertices
    print("=" * 60)
    print("Example 3: Find bipartite graphs on 7 vertices (first 5)")
    print("=" * 60)

    bipartite = query_graphs({"n": 7, "bipartite": True, "limit": 5})
    print(f"Found {len(bipartite)} graphs (showing first 5):")
    for g in bipartite:
        props = g['properties']
        print(f"  {g['graph6']}: {g['m']} edges, girth={props.get('girth', 'N/A')}")
    print()

    # Example 4: Get database statistics
    print("=" * 60)
    print("Example 4: Database statistics")
    print("=" * 60)

    stats = get_stats()
    print(f"Total graphs: {stats['total_graphs']:,}")
    print(f"Connected graphs: {stats['connected_graphs']:,}")
    print("Graphs by vertex count:")
    for n, count in sorted(stats['counts_by_n'].items(), key=lambda x: int(x[0])):
        print(f"  n={n}: {count:,}")
