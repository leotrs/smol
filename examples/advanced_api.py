"""Advanced SMOL API usage examples.

This script demonstrates more complex API queries:
- Comparing multiple graphs and detecting spectral differences
- Finding cospectral mates (graphs with identical spectra)
- Finding spectrally similar graphs
- Batch processing and analysis

Requirements:
    pip install requests

Usage:
    python advanced_api.py
"""

import requests
from urllib.parse import quote

BASE_URL = "https://smol-graphs-db.fly.dev"  # Production API (or http://127.0.0.1:8000 for local)


def compare_graphs(graph6_list: list[str]) -> dict:
    """Compare multiple graphs."""
    graphs_param = ",".join(graph6_list)
    response = requests.get(f"{BASE_URL}/compare", params={"graphs": graphs_param})
    response.raise_for_status()
    return response.json()


def find_similar(graph6: str, matrix: str = "adj", limit: int = 10) -> list:
    """Find spectrally similar graphs."""
    encoded = quote(graph6, safe="")
    response = requests.get(
        f"{BASE_URL}/similar/{encoded}",
        params={"matrix": matrix, "limit": limit}
    )
    response.raise_for_status()
    return response.json()


def get_graph(graph6: str) -> dict:
    """Look up a single graph."""
    encoded = quote(graph6, safe="")
    response = requests.get(f"{BASE_URL}/graph/{encoded}")
    response.raise_for_status()
    return response.json()


def query_graphs(params: dict) -> list:
    """Query graphs by properties."""
    response = requests.get(f"{BASE_URL}/graphs", params=params)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Example 1: Find and compare cospectral graphs
    print("=" * 60)
    print("Example 1: Find adjacency-cospectral graphs")
    print("=" * 60)

    # Search for a graph that has adjacency-cospectral mates
    print("Searching for graphs with cospectral mates...")
    graphs = query_graphs({"n": 8, "limit": 100})
    found = False
    for g in graphs:
        full = get_graph(g["graph6"])
        if full.get("cospectral_mates", {}).get("adj"):
            mate = full["cospectral_mates"]["adj"][0]
            comparison = compare_graphs([full["graph6"], mate])

            print("\nFound cospectral pair!")
            print(f"Graph 1: {full['graph6']} ({full['m']} edges)")
            print(f"Graph 2: {mate}")
            print("\nSpectral comparison:")
            for matrix, status in comparison["spectral_comparison"].items():
                print(f"  {matrix}: {status}")

            print("\nAdjacency eigenvalues (same for both):")
            eigs = comparison['graphs'][0]['spectra']['adj_eigenvalues']
            print(f"  {[round(e, 4) for e in eigs]}")
            found = True
            break

    if not found:
        print("No cospectral pairs found in first 100 graphs of n=8")
    print()

    # Example 2: Find graphs distinguished by non-backtracking but not adjacency
    print("=" * 60)
    print("Example 2: NB matrix distinguishes adj-cospectral graphs")
    print("=" * 60)

    # Search for adj-cospectral pairs that are NB-distinguished
    graphs = query_graphs({"n": 7, "limit": 100})
    found_pair = False
    for g in graphs:
        full = get_graph(g["graph6"])
        adj_mates = full.get("cospectral_mates", {}).get("adj", [])
        nb_mates = full.get("cospectral_mates", {}).get("nb", [])

        # Find adj-cospectral but not NB-cospectral
        for mate in adj_mates:
            if mate not in nb_mates:
                print(f"Pair: {full['graph6']} and {mate}")
                print("  - Same adjacency spectrum: YES")
                print("  - Same NB spectrum: NO")
                comparison = compare_graphs([full["graph6"], mate])
                print(f"  - Graph 1 edges: {comparison['graphs'][0]['m']}")
                print(f"  - Graph 2 edges: {comparison['graphs'][1]['m']}")
                found_pair = True
                break
        if found_pair:
            break

    if not found_pair:
        print("No pair found in first 100 graphs of n=7")
    print()

    # Example 3: Find spectrally similar graphs
    print("=" * 60)
    print("Example 3: Find spectrally similar graphs to C_6 (cycle)")
    print("=" * 60)

    c6 = "E?Bw"  # 6-cycle
    similar = find_similar(c6, matrix="adj", limit=5)

    print(f"Graphs similar to {c6} (6-cycle) by adjacency spectrum:")
    for s in similar:
        g = s['graph']
        print(f"  {g['graph6']}: distance={s['distance']:.4f}, edges={g['m']}")
    print()

    # Example 4: Analyze a family of graphs
    print("=" * 60)
    print("Example 4: Spectral properties of Petersen-like graphs")
    print("=" * 60)

    # Find 3-regular graphs on 8 vertices
    regular_8 = query_graphs({"n": 8, "regular": "true", "limit": 10})

    print(f"Found {len(regular_8)} 3-regular graphs on 8 vertices")
    print("\nComparing spectral radii (largest adjacency eigenvalue):")

    for g in regular_8[:5]:
        full = get_graph(g["graph6"])
        eigs = full["spectra"]["adj_eigenvalues"]
        spectral_radius = max(abs(e) for e in eigs)
        alg_conn = full["properties"].get("algebraic_connectivity", "N/A")
        print(f"  {g['graph6']}: ρ={spectral_radius:.4f}, algebraic_conn={alg_conn}")

    # Example 5: Batch analysis - chromatic vs clique number
    print()
    print("=" * 60)
    print("Example 5: Chromatic number vs clique number distribution")
    print("=" * 60)

    graphs_8 = query_graphs({"n": 8, "limit": 200})

    # Count (clique, chromatic) pairs
    pairs = {}
    for g in graphs_8:
        clique = g["properties"].get("clique_number")
        chrom = g["properties"].get("chromatic_number")
        if clique and chrom:
            key = (clique, chrom)
            pairs[key] = pairs.get(key, 0) + 1

    print("Distribution of (clique_number, chromatic_number) for n=8 graphs:")
    for (clique, chrom), count in sorted(pairs.items()):
        gap = chrom - clique
        print(f"  ω={clique}, χ={chrom} (gap={gap}): {count} graphs")

    # Example 6: Exploring all 7 matrix types
    print()
    print("=" * 60)
    print("Example 6: Compare cospectrality across all 7 matrix types")
    print("=" * 60)

    # Get a graph and check cospectral mates for each matrix type
    sample = get_graph("H?`crjU")  # A graph with NB-cospectral mates
    print(f"Graph: {sample['graph6']} ({sample['n']} vertices, {sample['m']} edges)")
    print(f"Tags: {sample.get('tags', [])}")
    print("\nCospectral mates by matrix type:")

    matrix_types = ["adj", "kirchhoff", "signless", "lap", "nb", "nbl", "dist"]
    for matrix in matrix_types:
        mates = sample.get("cospectral_mates", {}).get(matrix, [])
        print(f"  {matrix:10s}: {len(mates)} mate(s)")

    # Example 7: Switching mechanisms
    print()
    print("=" * 60)
    print("Example 7: Switching mechanisms for cospectral pairs")
    print("=" * 60)

    # Get mechanisms for a graph with known GM switching
    graph6 = "H?`crjU"
    encoded = quote(graph6, safe="")
    response = requests.get(f"{BASE_URL}/api/graph/{encoded}/mechanisms")
    data = response.json()

    print(f"Graph: {graph6}")
    mechanisms = data.get('mechanisms', {})
    total_mechs = sum(len(mechs) for mechs in mechanisms.values())
    print(f"Mechanisms found: {total_mechs}")

    for matrix_type, mechs in mechanisms.items():
        for mech in mechs[:2]:  # Show first 2 per matrix type
            print(f"  Mate: {mech['mate']}")
            print(f"    Matrix: {matrix_type}")
            print(f"    Mechanism: {mech['mechanism']}")
            if mech.get('config'):
                partition = mech['config'].get('partition', [])
                print(f"    Partition size: {len(partition)} classes")
        if mechs:
            break  # Just show one matrix type for brevity
