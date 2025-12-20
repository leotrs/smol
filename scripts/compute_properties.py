"""Compute additional graph properties for SMOL database.

This script computes network science properties for graphs that don't have them yet.
Properties are computed using NetworkX and stored in the PostgreSQL database.

Properties computed:
- clique_number: Size of the maximum clique (via nx.find_cliques)
- chromatic_number: Greedy upper bound (via nx.coloring.greedy_color with 'largest_first')
- algebraic_connectivity: Second-smallest Laplacian eigenvalue (Fiedler value)
- global_clustering: Transitivity (ratio of triangles to connected triples)
- avg_local_clustering: Mean of local clustering coefficients
- avg_path_length: Mean shortest path distance (only for connected graphs)
- assortativity: Degree assortativity coefficient (Pearson correlation)

Usage:
    uv run python scripts/compute_properties.py [--n N] [--batch-size SIZE] [--quiet]

Notes:
- Uses WITH HOLD cursor to survive transaction commits during batch processing
- Chromatic number is a greedy upper bound, not exact (exact is NP-hard)
- Assortativity is undefined for graphs where all nodes have the same degree
"""

import argparse
import psycopg2
import networkx as nx
import numpy as np


def graph6_to_nx(g6: str) -> nx.Graph:
    return nx.from_graph6_bytes(g6.encode())


def compute_properties(G: nx.Graph) -> dict:
    """Compute graph theory and network science properties."""
    n = G.number_of_nodes()
    m = G.number_of_edges()

    # Clique number
    if m == 0:
        clique_number = 1
    else:
        cliques = list(nx.find_cliques(G))
        clique_number = max(len(c) for c in cliques) if cliques else 1

    # Chromatic number (greedy upper bound)
    if n == 0:
        chromatic_number = 0
    elif m == 0:
        chromatic_number = 1
    else:
        coloring = nx.coloring.greedy_color(G, strategy='largest_first')
        chromatic_number = max(coloring.values()) + 1 if coloring else 1

    # Algebraic connectivity
    if n <= 1:
        algebraic_connectivity = 0.0
    else:
        lap_eigs = nx.laplacian_spectrum(G)
        lap_eigs.sort()
        algebraic_connectivity = float(lap_eigs[1]) if len(lap_eigs) > 1 else 0.0

    # Global clustering (transitivity)
    if n < 3 or m == 0:
        global_clustering = 0.0
    else:
        global_clustering = nx.transitivity(G)

    # Average local clustering
    if n < 3 or m == 0:
        avg_local_clustering = 0.0
    else:
        avg_local_clustering = nx.average_clustering(G)

    # Average path length (only for connected graphs)
    if n <= 1:
        avg_path_length = 0.0
    elif nx.is_connected(G):
        avg_path_length = nx.average_shortest_path_length(G)
    else:
        avg_path_length = None  # undefined for disconnected

    # Degree assortativity (undefined for regular graphs where all degrees are equal)
    degrees = [d for _, d in G.degree()]
    if m < 2 or (degrees and min(degrees) == max(degrees)):
        assortativity = None
    else:
        try:
            assortativity = nx.degree_assortativity_coefficient(G)
            if np.isnan(assortativity):
                assortativity = None
        except (ValueError, ZeroDivisionError):
            assortativity = None

    return {
        'clique_number': clique_number,
        'chromatic_number': chromatic_number,
        'algebraic_connectivity': algebraic_connectivity,
        'clustering_coefficient': avg_local_clustering,  # legacy column name
        'assortativity': assortativity,
        'global_clustering': global_clustering,
        'avg_local_clustering': avg_local_clustering,
        'avg_path_length': avg_path_length,
    }


def main():
    parser = argparse.ArgumentParser(description='Compute graph properties')
    parser.add_argument('--n', type=int, help='Only process graphs with this vertex count')
    parser.add_argument('--batch-size', type=int, default=500, help='Batch size for updates')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress output')
    args = parser.parse_args()

    conn = psycopg2.connect("dbname=smol")

    where_clause = """WHERE clique_number IS NULL
        OR global_clustering IS NULL"""
    if args.n:
        where_clause += f" AND n = {args.n}"

    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM graphs {where_clause}")
        total = cur.fetchone()[0]
        if not args.quiet:
            print(f"Found {total} graphs needing property computation")

    if total == 0:
        print("Nothing to do.")
        conn.close()
        return

    processed = 0
    batch = []

    with conn.cursor(name='prop_cursor', withhold=True) as cur:
        cur.itersize = 1000
        cur.execute(f"SELECT id, graph6 FROM graphs {where_clause}")

        for row in cur:
            graph_id, g6 = row
            G = graph6_to_nx(g6)
            props = compute_properties(G)

            batch.append((
                props['clique_number'],
                props['chromatic_number'],
                props['algebraic_connectivity'],
                props['clustering_coefficient'],
                props['assortativity'],
                props['global_clustering'],
                props['avg_local_clustering'],
                props['avg_path_length'],
                graph_id
            ))

            if len(batch) >= args.batch_size:
                with conn.cursor() as update_cur:
                    update_cur.executemany("""
                        UPDATE graphs SET
                            clique_number = %s,
                            chromatic_number = %s,
                            algebraic_connectivity = %s,
                            clustering_coefficient = %s,
                            assortativity = %s,
                            global_clustering = %s,
                            avg_local_clustering = %s,
                            avg_path_length = %s
                        WHERE id = %s
                    """, batch)
                conn.commit()
                processed += len(batch)
                if not args.quiet:
                    print(f"Processed {processed}/{total} ({100*processed/total:.1f}%)")
                batch = []

        if batch:
            with conn.cursor() as update_cur:
                update_cur.executemany("""
                    UPDATE graphs SET
                        clique_number = %s,
                        chromatic_number = %s,
                        algebraic_connectivity = %s,
                        clustering_coefficient = %s,
                        assortativity = %s,
                        global_clustering = %s,
                        avg_local_clustering = %s,
                        avg_path_length = %s
                    WHERE id = %s
                """, batch)
            conn.commit()
            processed += len(batch)

    if not args.quiet:
        print(f"Done. Processed {processed} graphs.")

    conn.close()


if __name__ == '__main__':
    main()
